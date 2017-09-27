# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from django.conf import settings
from evennia import utils

# error return function, needed by Extended Look command
_AT_SEARCH_RESULT = utils.variable_from_module(*settings.SEARCH_AT_RESULT.rsplit('.', 1))


class CmdSense(MuxCommand):
    """
    Handle sensing objects in different ways. WIP: Expanding to handle other senses.
    Sense yourself, your location or objects in your vicinity.
    Usage:
      <|ysense verb|n>[|g/switch|n] <|yobject|n>['s aspect[ = [detail]]

      Add detail following the equal sign after the object's aspect.
      Nothing following the equals sign (=) will remove the detail.

      The command 'sense' is strictly informative, while the more specific alternative
      versions are interactive and may trigger a notification, response, or cause effects.
    """
    key = 'sense'
    aliases = ['l', 'look', 'taste', 'touch', 'smell', 'listen', 'glance']
    locks = 'cmd:all()'
    arg_regex = r'\s|$'

    def func(self):
        """Handle sensing objects in different ways, including look."""
        char = self.character
        here = char.location if char else None
        account = self.account
        if not (char and here):
            account.msg('You sense only |222Nothingness|n.')
            message = '|gback|n or |ghome' if char else '|g@ic'
            account.msg('(Type %s|n to return to the NOW.)' % message)
            return
        args = self.args.strip()
        cmd = self.cmdstring
        lhs = self.lhs.strip()
        rhs = self.rhs
        obj_string, aspect = [lhs, None] if "'s " not in lhs else lhs.rsplit("'s ", 1)

        if obj_string and obj_string.lower() in ('outside', 'out') and here and here.location:
            char.msg('From within {}, you see:'.format(here.get_display_name(char)))
            obj = [here.location]
        else:
            obj = char.search(obj_string, quiet=True,
                              candidates=[here] + here.contents + char.contents) if args else [char]
        if obj:
            obj = obj[0]
            obj_string = obj.key
        else:
            _AT_SEARCH_RESULT(obj, char, args, quiet=False)
            return  # Trying to sense something that isn't there. "Could not find ''."
        style = obj.STYLE if obj and hasattr(obj, 'STYLE') else '|g'
        if cmd == 'glance':
            if here and not args:
                obj = here
            sights = obj.return_glance(char)
            if sights:
                account.msg('|/You glance at %s and see: %s ' % (obj.get_display_name(char), sights))
            else:
                account.msg('|/You glance at %s, but see nothing.' % obj.get_display_name(char))
            return
        # senses = obj.db.senses
        # details = obj.db.details
        if self.rhs is not None:  # Equals sign exists.
            if not self.rhs:  # Nothing on the right side
                # TODO: Delete and verify intent with switches. Mock-up command without switches.
                # Scan senses before deleting details - make sure not to remove detail if another sense uses it.
                account.msg('Functionality to delete aspects and details is not yet implemented.' % self.switches)

                if aspect:
                    account.msg("|w%s|n (object) %s%s|n's |g%s|n (aspect)  =  |r (detail removed)" %
                               (cmd, style, obj_string, aspect))
                else:
                    account.msg("|w%s|n (object) %s%s|n  =  |r (detail removed)" %
                               (cmd, style, obj_string))
            else:
                # TODO: Add and verify intent with switches. Mock-up command without switches.
                account.msg('Functionality to add aspects and details is not yet implemented.' % self.switches)
                if aspect:
                    account.msg("|w%s|n (object) %s%s|n's |g%s|n (aspect)  =  |c%s|n (detail)" %
                               (cmd, style, obj_string, aspect, rhs))
                else:
                    account.msg("|w%s|n (object) %s%s|n  =  |c%s|n (detail)" %
                               (cmd, style, obj_string, rhs))
            return
        if cmd != 'l' and 'look' not in cmd:  # Doing non-LOOK stuff in here.
            if 'sense' in cmd:
                char.msg('|wSensing...')
                if obj:
                    if obj.db.senses:  # Object must be database object to be sensed.
                        string = '* Senses available for %s: ' % obj.get_display_name(account)
                        string += ", ".join('|lc%s %s|lt|g%s|n|le'
                                            % (element, obj.get_display_name(char, plain=True), element)
                                            for element in obj.db.senses.keys())
                        char.msg(string)
                        aspect_list = []  # list aspects.
                        for element in obj.db.senses.keys():
                            for aspect in obj.db.senses[element].keys():
                                aspect_list.append("|lc%s %s's %s|lt|g%s|n|le " % (element, obj.key, aspect, aspect)
                                                   if aspect else '')
                        if len(aspect_list) > 0:
                            char.msg(obj.get_display_name(account) + ' has the following aspects that can be sensed: ' +
                                     ''.join(aspect_list))
                    if obj != char:
                        verb_msg = "%s responds to: " % obj.get_display_name(account)
                    else:
                        verb_msg = "%sYou|n respond to: " % char.STYLE
                    verbs = obj.locks
                    collector_list = []
                    show_red = True if obj.access(char, 'examine') else False
                    for verb in ("%s" % verbs).split(';'):
                        element = verb.split(':')[0]
                        if element == 'call':
                            continue
                        name = element[2:] if element[:2] == 'v-' else element
                        if obj.access(char, element):  # obj lock checked against actor
                            collector_list.append("|lctry %s %s|lt|g%s|n|le " %
                                                  (name, obj.get_display_name(char, plain=True), name))
                        elif show_red:
                            collector_list.append("|r%s|n " % name)
                    char.msg(verb_msg + ''.join(collector_list))
            elif 'taste' in cmd or 'touch' in cmd or 'smell' in cmd or 'listen' in cmd:  # Specific sense (not look)
                if not obj:
                    return
                # Object to sense might have been found. Check the senses dictionary.
                if obj.db.senses and cmd in obj.db.senses:
                    senses_of = obj.db.senses[cmd]  # senses_of is the sense dictionary for current sense.
                    if aspect in senses_of:
                        details_of = obj.db.details
                        if details_of and senses_of[aspect] in details_of:
                            entry = details_of[senses_of[aspect]]
                            char.msg('%sYou|n sense %s from %s.' % (char.STYLE, entry, obj.get_display_name(account)))
                        else:
                            if aspect:
                                char.msg("%sYou|n try to %s %s's %s, but can not."
                                         % (char.STYLE, cmd, obj.get_display_name(account), aspect))
                            else:
                                char.msg("%sYou|n try to %s %s, but can not."
                                         % (char.STYLE, cmd, obj.get_display_name(account)))
                    else:
                        if aspect:
                            char.msg("%sYou|n try to %s %s's %s, but can not."
                                     % (char.STYLE, cmd, obj.get_display_name(account), aspect))
                        else:
                            char.msg("%sYou|n try to %s %s, but can not."
                                     % (char.STYLE, cmd, obj.get_display_name(account)))
                else:
                    char.msg('%sYou|n try to %s %s, but can not.' % (char.STYLE, cmd, obj.get_display_name(account)))
                # First case: look for an object in room, inventory, room contents, their contents,
                # and their contents contents with tagged restrictions, then if no match is found
                # in their name or alias, look at the senses tables in each of these objects: The
                # Senses attribute is a dictionary of senses that point to the details dictionary
                # entries. Senses dictionary allows for aliases in the details and pointing
                # specific senses to specific entries.
                #
                # If not looking for a specific object or entry, list objects and aspects of the particular
                # sense. Start with that first, and start with the char's own self and inventory.
                # when the /self;me and /inv;inventory switch is used?
            return
        if args:  # < LOOK begins here. ------------------------------------------- >
            if not obj:  # If no object was found, then look for a detail on the object.
                # no object found. Check if there is a matching detail around the location.
                # TODO: Restrict search for details by possessive parse:  [object]'s [aspect]
                candidates = [here] + here.contents + char.contents
                for location in candidates:
                    # TODO: Continue if look location is not visible to looker.
                    if location and hasattr(location, "return_detail") and callable(location.return_detail):
                        detail = location.return_detail(args)
                        if detail:
                            char.msg(detail)  # Show found detail.
                            return  # TODO: Add /all switch to override return here to view all details.
                _AT_SEARCH_RESULT(obj, char, args, quiet=False)  # no detail found. Trigger delayed error messages
                return
            else:
                obj = utils.make_iter(obj)[0]  # Use the first match in the list.
        else:
            obj = here
        if not obj.access(char, 'view'):
            char.msg("You are unable to sense '%s'." % args)
            return
        account.msg(obj.return_appearance(char))  # get object's appearance as seen by char
        obj.at_desc(looker=char)  # the object's at_desc() method - includes look-notify.
