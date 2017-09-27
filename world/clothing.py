"""
Clothing typeclass and commands for wearable clothing,
which is appended to the view of a character's
description when worn, based on the Evennia contribution
by Tim Ashley Jenkins 2017

Clothing items, when worn, are added to the character's description
in a list. For example, if wearing the following clothing items:

    a thin and delicate necklace
    a pair of regular ol' shoes
    one nice hat
    a very pretty dress

A character's description may look like this:

    Superuser(#1)
    This is User #1.

    Superuser is wearing one nice hat, a thin and delicate necklace,
    a very pretty dress and a pair of regular ol' shoes.

Characters can also specify the style of wear for their clothing - I.E.
to wear a scarf 'tied into a tight knot around the neck' or 'draped
loosely across the shoulders' - to add an easy avenue of customization.
For example, after entering:

    wear scarf draped loosely across the shoulders

The garment appears like so in the description:

    Superuser(#1)
    This is User #1.

    Superuser is wearing a fanciful-looking scarf draped loosely
    across the shoulders.

Items of clothing can be used to cover other items, and many options
are provided to define your own clothing types and their limits and
behaviors. For example, to have undergarments automatically covered
by outerwear, or to put a limit on the number of each type of item
that can be worn. The system as-is is fairly freeform - you
can cover any garment with almost any other, for example - but it
can easily be made more restrictive, and can even be tied into a
system for armor or other equipment.
Example:
    @create a pretty shirt : world.clothing.Item
    @set shirt/clothing_type = 'top'
"""

from typeclasses.objects import Consumable
from commands.command import MuxCommand
from evennia.utils import list_to_string
from evennia.utils import evtable

# Maximum character length of 'wear style' strings, or None for unlimited.
WEARSTYLE_MAXLENGTH = 65

# The order in which clothing types appear on the description. Untyped clothing goes last.
CLOTHING_TYPE_ORDER = ['hat', 'goggles', 'glasses', 'jewelry', 'top', 'undershirt',
                       'gloves', 'fullbody', 'bottom', 'underpants', 'socks', 'shoes', 'accessory']

# The maximum number of each type of clothes that can be worn. Unlimited if untyped or not specified.
CLOTHING_TYPE_LIMIT = {'hat': 1, 'goggles': 1, 'glasses': 1, 'gloves': 1, 'socks': 1, 'shoes': 1}

# The maximum number of clothing items that can be worn, or None for unlimited.
CLOTHING_OVERALL_LIMIT = 20

# What types of clothes will automatically cover what other types of clothes when worn.
# Note that clothing only gets auto-covered if it's already worn when you put something
# on that auto-covers it - for example, it's perfectly possible to have your underpants
# showing if you put them on after your pants!
CLOTHING_TYPE_AUTOCOVER = {'top': ['undershirt'], 'bottom': ['underpants'], 'goggles': ['glasses'],
                           'fullbody': ['undershirt', 'underpants'], 'shoes': ['socks']}

# Types of clothes that can't be used to cover other clothes.
CLOTHING_TYPE_CANT_COVER_WITH = ['jewelry']


# HELPER FUNCTIONS START HERE

def order_clothes_list(clothes_list):
    """
    Orders a given clothes list by the order specified in CLOTHING_TYPE_ORDER.

    Args:
        clothes_list (list): List of clothing items to put in order

    Returns:
        ordered_clothes_list (list): The same list as passed, but re-ordered
                                     according to the hierarchy of clothing types
                                     specified in CLOTHING_TYPE_ORDER.
    """
    ordered_clothes_list = clothes_list
    # For each type of clothing that exists...
    for current_type in reversed(CLOTHING_TYPE_ORDER):
        # Check each item in the given clothes list.
        for clothes in clothes_list:
            # If the item has a clothing type...
            if clothes.db.clothing_type:
                item_type = clothes.db.clothing_type
                # And the clothing type matches the current type...
                if item_type == current_type:
                    # Move it to the front of the list!
                    ordered_clothes_list.remove(clothes)
                    ordered_clothes_list.insert(0, clothes)
    return ordered_clothes_list


def get_worn_clothes(character, exclude_covered=False):
    """
    Get a list of clothes worn by a given character.

    Args:
        character (obj): The character to get a list of worn clothes from.
        exclude_covered (bool): If True, excludes clothes covered by other
                                clothing from the returned list.

    Returns:
        ordered_clothes_list (list): A list of clothing items worn by the
                                     given character, ordered according to
                                     the CLOTHING_TYPE_ORDER option specified
                                     in this module.
    """
    clothes_list = []
    for thing in character.contents:
        # If uncovered or not excluding covered items
        if not thing.db.covered_by or exclude_covered is False:
            # If 'worn' is True, add to the list
            if thing.db.worn:
                clothes_list.append(thing)
    # Might as well put them in order here too.
    ordered_clothes_list = order_clothes_list(clothes_list)
    return ordered_clothes_list


def clothing_type_count(clothes_list):
    """
    Returns a dictionary of the number of each clothing type
    in a given list of clothing objects.

    Args:
        clothes_list (list): A list of clothing items from which
                             to count the number of clothing types
                             represented among them.

    Returns:
        types_count (dict): A dictionary of clothing types represented
                            in the given list and the number of each
                            clothing type represented.
    """
    types_count = {}
    for garment in clothes_list:
        if garment.db.clothing_type:
            type = garment.db.clothing_type
            if type not in types_count.keys():
                types_count[type] = 1
            else:
                types_count[type] += 1
    return types_count


def single_type_count(clothes_list, type):
    """
    Returns an integer value of the number of a given type of clothing in a list.

    Args:
        clothes_list (list): List of clothing objects to count from
        type (str): Clothing type to count

    Returns:
        type_count (int): Number of garments of the specified type in the given
                          list of clothing objects
    """
    type_count = 0
    for garment in clothes_list:
        if garment.db.clothing_type:
            if garment.db.clothing_type == type:
                type_count += 1
    return type_count


class Item(Consumable):

    STYLE = '|G'

    def wear(self, wearer, wearstyle, quiet=False):
        """
        Sets clothes to 'worn' and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this clothing object
            wearstyle (True or str): string describing the style of wear or True for none
            quiet (bool): If false, does not message the room

        Notes:
            Optionally sets db.worn with a 'wearstyle' that appends a short passage to
            the end of the name  of the clothing to describe how it's worn that shows
            up in the wearer's desc - I.E. 'around his neck' or 'tied loosely around
            her waist'. If db.worn is set to 'True' then just the name will be shown.
        """
        # Set clothing as worn
        self.db.worn = wearstyle
        # Auto-cover appropriate clothing types, as specified above
        to_cover = []
        if self.db.clothing_type and self.db.clothing_type in CLOTHING_TYPE_AUTOCOVER:
            for garment in get_worn_clothes(wearer):
                if garment.db.clothing_type and garment.db.clothing_type \
                        in CLOTHING_TYPE_AUTOCOVER[self.db.clothing_type]:
                    to_cover.append(garment)
                    garment.db.covered_by = self
        if quiet:
            return
        # Otherwise, display a message to the room
        message = "{wearer} puts on {item}"
        if wearstyle and wearstyle is not True:
            message = "{wearer} wears {item} %s" % wearstyle
        if to_cover:
            message = message + ", covering %s" % list_to_string(to_cover)
        wearer.location.msg_contents(message + ".", mapping=dict(wearer=wearer, item=self))

    def remove(self, wearer, quiet=False):
        """
        Removes worn clothes and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this clothing object
            quiet (bool): If false, does not message the room
        """
        self.db.worn = False
        remove_message = "{wearer} removes {item}."
        uncovered_list = []

        # Check to see if any other clothes are covered by this object.
        for thing in wearer.contents:
            # If anything is covered by
            if thing.db.covered_by == self:
                thing.db.covered_by = False
                uncovered_list.append(thing.name)
        if len(uncovered_list) > 0:
            remove_message = "{wearer} removes {item}, revealing %s." % list_to_string(uncovered_list)
        # Echo a message to the room
        if not quiet:
            wearer.location.msg_contents(remove_message, mapping=dict(wearer=wearer, item=self))

    def at_get(self, getter):
        """
        Makes absolutely sure clothes aren't already set as 'worn'
        when they're picked up, in case they've somehow had their
        location changed without getting removed.
        """
        super(Item, self).at_get(getter)
        self.db.worn = False

# COMMANDS START HERE


class CmdWear(MuxCommand):
    """
    Puts on an item of clothing you are holding.

    Usage:
      wear <obj> [wear style]

    Examples:
      wear shirt
      wear scarf wrapped loosely about the shoulders

    All the clothes you are wearing are appended to your description.
    If you provide a 'wear style' after the command, the message you
    provide will be displayed after the clothing's name.
    """
    key = 'wear'
    help_category = 'Clothing'

    def func(self):
        """
        This performs the actual command.
        """
        char = self.character
        if not self.args:
            char.msg("Usage: wear <obj> [wear style]")
            return
        clothing = char.search(self.arglist[0], candidates=char.contents)
        wearstyle = True
        if not clothing:
            return
        if not clothing.is_typeclass("world.clothing.Item"):
            char.msg("That's not clothes!")
            return

        # Enforce overall clothing limit.
        if CLOTHING_OVERALL_LIMIT and len(get_worn_clothes(char)) >= CLOTHING_OVERALL_LIMIT:
            char.msg("You can't wear any more clothes.")
            return

        # Apply individual clothing type limits.
        if clothing.db.clothing_type and not clothing.db.worn:
            type_count = single_type_count(get_worn_clothes(char), clothing.db.clothing_type)
            if clothing.db.clothing_type in CLOTHING_TYPE_LIMIT.keys():
                if type_count >= CLOTHING_TYPE_LIMIT[clothing.db.clothing_type]:
                    char.msg("You can't wear any more clothes of the type '%s'." % clothing.db.clothing_type)
                    return

        if clothing.db.worn and len(self.arglist) == 1:
            char.msg("You're already wearing %s!" % clothing.name)
            return
        if len(self.arglist) > 1:  # If wearstyle arguments given
            wearstyle_list = self.arglist  # Split arguments into a list of words
            del wearstyle_list[0]  # Leave first argument (the clothing item) out of the wearstyle
            wearstring = ' '.join(str(e) for e in wearstyle_list)  # Join list of args back into one string
            if WEARSTYLE_MAXLENGTH and len(wearstring) > WEARSTYLE_MAXLENGTH:  # If length of wearstyle exceeds limit
                char.msg("Please keep your wear style message to less than %i characters." % WEARSTYLE_MAXLENGTH)
            else:
                wearstyle = wearstring
        clothing.wear(char, wearstyle)


class CmdRemove(MuxCommand):
    """
    Removes an item of clothing.

    Usage:
       remove <obj>

    Removes an item of clothing you are wearing. You can't remove
    clothes that are covered up by something else - you must take
    off the covering item first.
    """
    key = 'remove'
    help_category = 'Clothing'

    def func(self):
        """
        This performs the actual command.
        """
        char = self.character
        clothing = char.search(self.args, candidates=char.contents)
        if not clothing:
            return
        if not clothing.db.worn:
            char.msg("You're not wearing that!")
            return
        if clothing.db.covered_by:
            char.msg("You have to take off %s first." % clothing.db.covered_by.name)
            return
        clothing.remove(char)


class CmdCover(MuxCommand):
    """
    Covers a worn item of clothing with another you're holding or wearing.

    Usage:
        cover <obj> <=|with> <obj>

    When you cover a clothing item, it is hidden and no longer appears in
    your description until it's uncovered or the item covering it is removed.
    You can't remove an item of clothing if it's covered.
    """
    key = 'cover'
    help_category = 'Clothing'
    parse_using = ' with '

    def func(self):
        """
        This performs the actual command.
        """
        char = self.character
        lhs, rhs = self.lhs, self.rhs
        if not rhs:
            char.msg("Usage: cover <worn clothing> [=|with] <clothing object>")
            return
        to_cover = char.search(lhs, candidates=char.contents)
        cover_with = char.search(rhs, candidates=char.contents)
        if not to_cover or not cover_with:
            return
        if not to_cover.is_typeclass("world.clothing.Item"):
            char.msg("{item} isn't clothes!".format(item=to_cover.get_display_name(char)))
            return
        if not cover_with.is_typeclass("world.clothing.Item"):
            char.msg("{item} isn't wearable!".format(item=cover_with.get_display_name(char)))
            return
        if cover_with.db.clothing_type:
            if cover_with.db.clothing_type in CLOTHING_TYPE_CANT_COVER_WITH:
                char.msg("You can't cover anything with that!")
                return
        if not to_cover.db.worn:
            char.msg("You're not wearing {item}!".format(item=to_cover.get_display_name(char)))
            return
        if to_cover == cover_with:
            char.msg("You can't cover an item with itself!")
            return
        if cover_with.db.covered_by:
            char.msg("{} is covered by something else!".format(cover_with.get_display_name(char)))
            return
        if to_cover.db.covered_by:
            char.msg("{item} is already covered by {cover}.".format(
                item=cover_with.get_display_name(char),
                cover=to_cover.db.covered_by.get_display_name(char)))
            return
        if not cover_with.db.worn:
            cover_with.wear(char, True)  # Put on the item to cover with if it's not on already
        char.location.msg_contents("{wearer} covers {item} with {cover}.",
                                   mapping=dict(wearer=char,
                                                item=to_cover.get_display_name(char),
                                                cover=cover_with.get_display_name(char)))
        to_cover.db.covered_by = cover_with


class CmdUncover(MuxCommand):
    """
    Reveals a worn item of clothing that's currently covered up.

    Usage:
        uncover <obj>

    When you uncover an item of clothing, you allow it to appear in your
    description without having to take off the garment that's currently
    covering it. You can't uncover an item of clothing if the item covering
    it is also covered by something else.
    """
    key = 'uncover'
    help_category = 'Clothing'

    def func(self):
        """
        This performs the actual command.
        """
        char = self.character
        if not self.args:
            char.msg("Usage: uncover <worn clothing object>")
            return

        to_uncover = char.search(self.args, candidates=char.contents)
        if not to_uncover:
            return
        if not to_uncover.db.worn:
            char.msg("You're not wearing {item}!".format(item=to_uncover.get_display_name(char)))
            return
        if not to_uncover.db.covered_by:
            char.msg("{item} isn't covered by anything!".format(item=to_uncover.get_display_name(char)))
            return
        covered_by = to_uncover.db.covered_by
        if covered_by.db.covered_by:
            char.msg("{item} is under too many layers to uncover.".format(item=to_uncover.get_display_name(char)))
            return
        char.location.msg_contents("{wearer} uncovers {item}.", mapping=dict(wearer=char, item=to_uncover))
        to_uncover.db.covered_by = None


class CmdGive(MuxCommand):
    """
    Gives an item from your inventory to another.

    Usage:
      give <inventory obj> [=|to <target>]

    Options:
    /quiet or /silent  Others in the room not notified of give.
    /drop   Drops <inventory obj>
    """
    key = 'give'
    aliases = ['qgive']
    locks = 'cmd:all()'
    parse_using = ' to '

    def func(self):
        """Implement give"""
        opt = self.switches
        cmd = self.cmdstring
        char = self.character
        drop = 'drop' in opt
        lhs, rhs = self.lhs, 'here' if drop else self.rhs
        if not self.args or not rhs:
            char.msg("Usage: {} <inventory object> [<=|to> <target>]".format(cmd))
            return
        to_give = char.search(self.lhs, location=char, nofound_string='You aren\'t carrying "%s".' % self.lhs,
                              multimatch_string='You carry more than one "%s":' % self.lhs)
        target = char.search(rhs)
        drop = drop or target is char.location
        quiet = cmd == 'qgive' or 'silent' in opt or 'quiet' in opt
        if not (to_give and target):
            return
        if target == char:
            char.msg("You keep {it} to yourself.".format(it=to_give.get_display_name(char)))
            return
        if not to_give.location == char:
            char.msg("You are not holding {it}.".format(it=to_give.get_display_name(char)))
            return
        # This is new! Can't give away something that's worn.
        if to_give.db.covered_by:
            verb = 'drop {verb}' if drop else 'give {verb} away'
            verb = verb.format(verb=to_give.get_display_name(char))
            char.msg("You can't %s because it's covered by %s." % (verb, to_give.db.covered_by.get_display_name(char)))
            return
        # Remove clothes if they're given or dropped.
        if to_give.db.worn:
            to_give.remove(char)
        result = False if to_give is target else to_give.move_to(target, quiet=True)
        if not result:
            message = "drop %s." % to_give.get_display_name(char) if drop else\
                "give %s to %s." % (to_give.get_display_name(char), target.get_display_name(char))
            char.msg("You can't %s" % message)
            return
        if drop:
            message = "You quietly drop {}." if quiet else "You drop {}."
            char.msg(message.format(to_give.get_display_name(char)))
        else:
            message = "You quietly give {} to {}." if quiet else "You give {} to {}."
            char.msg(message.format(to_give.get_display_name(char), target.get_display_name(char)))
        if not quiet:
            if drop:
                char.location.msg_contents("{giver} drops {item}.",
                                           mapping=dict(giver=char, item=to_give),
                                           exclude=[char, target])
            else:
                char.location.msg_contents("{giver} gives {item} to {receiver}.",
                                           mapping=dict(giver=char, item=to_give, receiver=target),
                                           exclude=[char, target])
        if target.location and target.has_account:
            message = "{} quietly gives you {}." if quiet else "{} gives you {}."
            target.msg(message.format(char.get_display_name(char), to_give.get_display_name(char)))
        # Call the object script's at_give() method.
        to_give.at_give(char, target)
