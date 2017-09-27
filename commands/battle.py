"""
Commands

Commands describe the input the account can do to the game.

"""
import math
from evennia import CmdSet, utils
from evennia.utils import evmenu
from commands import MuxCommand
from random import randint
from world import rules


class BattleCmdSet(CmdSet):
    key = 'battle'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the vehicle object (item or room)."""
        self.add(CmdStat())


class CmdStat(MuxCommand):
    """
    Set the stat of a character

    Usage:
      setstat [stat] = <1-10>

    This sets the stat of the current character.
    This can only be used during character generation.
    """
    key = 'stat'
    help_category = 'battle'

    def func(self):
        """
        'reset' option sets a character's stats all back to 6.
        """
        cmd = self.cmdstring
        switches = self.switches
        if 'reset' in switches:
            self.caller.msg("All stats reset to 6.")
            self.traits.add('stat_atm', 'Melee Attack', type='gauge', base=6, min=0, max=10)
            self.traits.add('atr', 'Ranged Attack', type='gauge', base=6, min=0, max=10)
            self.traits.add('stat_def', 'Defense', type='gauge', base=6, min=0, max=10)
            self.traits.add('stat_vit', 'Vitality', type='gauge', base=6, min=0, max=10)
            self.traits.add('stat_mob', 'Mobility', type='gauge', base=6, min=0, max=10)
            self.traits.add('stat_spe', 'Special', type='gauge', base=6, min=0, max=10)
            self.traits.add('health', 'Health', type='gauge', base=18, min=0, max=20)
            self.traits.add('special', 'Super', type='gauge', base=12, min=0, max=20)
            return
        errmsg = "You must supply a valid stat name and a number" \
                 " between 0 and 10.|/Syntax: |555%s [stat] = [1-10]|n" % cmd
        if not self.args:
            self.caller.msg(errmsg)
            return
        if not self.rhs:
            self.caller.msg(errmsg)
            return
        if not self.lhs:
            self.caller.msg(errmsg)
            return
        try:
            value = int(self.rhs)
        except ValueError:
            self.caller.msg(errmsg)
            return
        try:
            statname = str(self.lhs)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= value <= 10):
            self.caller.msg(errmsg)
            return
        # At this point the argument is tested as valid. Let's set it.
        # First, make the stat name lowercase.
        statname = statname.lower()
        # Now, we'll test to see what stat is named, using either the
        # abbreviation or the stat's full name.
        if statname == "atm" or statname == "melee" or statname == "melee attack":
            self.caller.trait.stat_atm = value
            self.caller.msg("Your Melee Attack was set to |555%i|n." % value)
        elif statname == "def" or statname == "defense":
            self.caller.trait.stat_def = value
            self.caller.msg("Your Defense was set to |555%i|n." % value)
        elif statname == "vit" or statname == "vitality":
            self.caller.trait.stat_vit = value
            # Also sets your HP to its new maximum.
            self.caller.traits.health = max(value * 3, 1)
            self.caller.msg(
                "Your Vitality was set to %i|n and your new HP maximum is |555%i|n." % (value, max(value * 3, 1)))
        elif statname == "atr" or statname == "ranged attack" or statname == "ranged":
            self.caller.trait.stat_atr = value
            self.caller.msg("Your Ranged Attack was set to |555%i|n." % value)
        elif statname == "mob" or statname == "mobility":
            self.caller.trait.stat_mob = value
            self.caller.msg("Your Mobility was set to |555%i|n." % value)
        elif statname == "spe" or statname == "special":
            self.caller.db.SP = value * 2
            self.caller.trait.stat_spe = value
            self.caller.msg(
                "Your Special was set to |555%i|n and your new SP maximum is |555%i|n." % (value, value * 2))
        # If the stat didn't have a valid name, return an error.
        else:
            self.caller.msg("\"" + self.lhs + "\" is not a valid stat name. Stats are Melee Attack (|522ATM|n),"
                                              " Ranged Attack (|525ATR|n), Defense (|225DEF|n), Vitality (|252VIT|n),"
                                              " Mobility (|552MOB|n), and Special (|255SPE|n).")
            return
        remain = 36 - (self.caller.trait.stat_atm.actual + self.caller.trait.stat_def + self.caller.trait.stat_vit +
                       self.caller.trait.stat_atr + self.caller.trait.stat_mob + self.caller.trait.stat_spe)
        point = "points"
        if remain == 1 or remain == -1:
            point = "point"
        if remain >= 0:
            self.caller.msg("You have |555%i %s|n remaining." % (remain, point))
        else:
            remain *= -1
            self.caller.msg("You have too many points in your stats - you must remove |522%i %s|n to enter the game." %
                            (remain, point))


class CmdRangeMessage(MuxCommand):
    """
    Lets you set pre-defined messages for your attacks.

    Usage:
      rangemessage[/switches] [<new message if adding or number to delete if
    removing>]

    Switches:
    add - Lets you add a new attack message.
    remove - Lets you remove an existing attack message.
    (no switch) - Lists your current attack messages.

    Examples:
    > rangekmessage/add sends an energy blast at <target>!
    Ranged attack message added: sends an energy blast at <target>!

    > rangemessage
    1. unleashes the secret "tiger beam" on <target>!
    2. With a crackle of energy, <self> sends a blast of power to <target>!
    3. throws a small rock at <target>.
    4. sends an energy blast at <target>!

    > rangemessage/remove 3
    Attack message removed: throws a small rock at <target>.


    This command lets you create a pool of pre-defined messages that are randomly
    displayed whenever you use the 'attack' command, in place of the default attack
    message. The message may include "<target>" in brackets, which is replaced with
    the name of your target of your attack. The messages normally have the name of
    your character appended to the beginning of the message (I.E. "Protagonist sends
    an energy blast at Antagonist!"), but if the message includes the word "<self>"
    in brackets, your character's name will appear in place of that instead (I.E.
    "With a crackle of energy, Protagonist sends a blast of power to Antagonist!")

    Since your attack could be blocked or dodged, it should not include the result
    of the attack (like "sends <target> flying with a powerful shot!") and
    generally shouldn't assume anything about the character you're targeting (like
    "strikes at <target>'s legs with a low shot!"). Your target will likely be
    humanoid, but may also be a four-legged beast or a floating, featureless psychic
    orb - keep this in mind when writing your attack messages.

    This command is for adding messages to ranged attacks - the equivalent command
    for melee attacks is 'meleemessage'.
    """
    key = 'rangemessage'
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if not self.caller.db.Range_Messages:
            self.caller.db.Range_Messages = []
        if not self.switches:
            switches = []
        else:
            switches = self.switches
        if 'add' in switches:
            if self.args:
                self.caller.db.Range_Messages.append(self.args)
                self.caller.msg("Added new ranged attack message: " + self.args)
                return
            self.caller.msg("Please specify a message to add!")
        elif 'remove' in switches or 'delete' in switches:
            try:
                itemindex = int(self.args) - 1
            except ValueError:
                self.caller.msg("Please specify a valid number!")
                return
            if itemindex > len(self.caller.db.Range_Messages):
                self.caller.msg("Please specify a valid number!")
                return
            self.caller.msg("Removed ranged attack message: " + self.caller.db.Range_Messages[itemindex])
            del self.caller.db.Range_Messages[itemindex]
            return
        else:
            # List the current combat messages!
            itemnumber = 0
            if len(self.caller.db.Range_Messages) == 0:
                self.caller.msg("You have no ranged attack messages!")
                return
            for message in self.caller.db.Range_Messages:
                itemnumber += 1
                self.caller.msg(("%i. " + message) % itemnumber)


class CmdMeleeMessage(MuxCommand):
    """
    Lets you set pre-defined messages for your close range attacks.

    Usage:
      meleemessage[/switches] [<new message if adding or number to delete if
    removing>]

    Switches:
    /add - Lets you add a new attack message.
    /remove - Lets you remove an existing attack message.
    (no switch) - Lists your current attack messages.

    Examples:
    > meleemessage/add attacks <target> with a quick punch!
    Melee attack message added: attacks <target> with a quick punch!

    > meleemessage
    1. sends a snap kick heading toward <target>!
    2. Twirling, <self> rushes in toward <target> with a spinning attack!
    3. weakly moves to tap <target> with a gentle punch.
    4. attacks <target> with a quick punch!

    > meleemessage/remove 3
    Melee attack message removed: weakly moves to tap <target> with a gentle punch.


    This command is functionally identical to the 'rangemessage' command (see 'help
    rangemessage') except that the messages are only used for attacks made in melee
    (against targets at 0 range).
    """
    key = 'meleemessage'
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if not self.caller.db.Melee_Messages:
            self.caller.db.Melee_Messages = []
        if not self.switches:
            switches = []
        else:
            switches = self.switches
        if 'add' in switches:
            if self.args:
                self.caller.db.Melee_Messages.append(self.args)
                self.caller.msg("Added new melee attack message: " + self.args)
                return
            self.caller.msg("Please specify a message to add!")
        elif 'remove' in switches or 'delete' in switches:
            try:
                itemindex = int(self.args) - 1
            except ValueError:
                self.caller.msg("Please specify a valid number!")
                return
            if itemindex > len(self.caller.db.Melee_Messages):
                self.caller.msg("Please specify a valid number!")
                return
            self.caller.msg("Removed melee attack message: " + self.caller.db.Melee_Messages[itemindex])
            del self.caller.db.Melee_Messages[itemindex]
            return
        else:
            # List the current combat messages!
            itemnumber = 0
            if len(self.caller.db.Melee_Messages) == 0:
                self.caller.msg("You have no melee attack messages!")
                return
            for message in self.caller.db.Melee_Messages:
                itemnumber += 1
                self.caller.msg(("%i. " + message) % itemnumber)


class CmdSpecialMessage(MuxCommand):
    """Lets you set pre-defined messages for your special moves."""
    key = 'specialmessage'
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if not self.caller.db.Special_Messages:
            self.caller.db.Special_Messages = {}
        if not self.switches:
            switches = []
        else:
            switches = self.switches
        if not self.lhs:
            self.caller.msg(
                "Please use the format:|/specialmessage/(list/add/remove) (special name) = (special message)")
            return
        specialname = ''
        if self.lhs:
            for special in self.caller.db.Special_Moves:
                if self.lhs.lower() in special.lower():
                    specialname = special
            if specialname == "":
                self.caller.msg("Special move \"%s\" not found!" % self.lhs)
                return
        if 'add' in switches:
            if self.rhs:
                try:
                    self.caller.db.Special_Messages[specialname].append(self.rhs)
                except KeyError:
                    self.caller.db.Special_Messages.update({specialname: [self.rhs]})
                self.caller.msg("Added new special message to %s: %s" % (specialname, self.rhs))
                return
            self.caller.msg("Please specify a message to add!")
        elif 'remove' in switches or 'delete' in switches:
            try:
                itemindex = int(self.rhs) - 1
            except ValueError:
                self.caller.msg("Please specify a valid number!")
                return
            if itemindex > len(self.caller.db.Special_Messages[specialname]):
                self.caller.msg("Please specify a valid number!")
                return
            if len(self.caller.db.Special_Messages[specialname][itemindex]) == 0:
                self.caller.msg("No messages to remove!")
                return
            self.caller.msg("Removed attack message: " + self.caller.db.Special_Messages[specialname][itemindex])
            del self.caller.db.Special_Messages[specialname][itemindex]
            return
        elif 'list' in switches or not switches or not self.rhs:
            # List the current special messages!
            itemnumber = 0
            if len(self.caller.db.Special_Messages[specialname]) == 0:
                self.caller.msg("%s has no messages!")
                return
            for message in self.caller.db.Special_Messages[specialname]:
                itemnumber += 1
                self.caller.msg(("%i. " + message) % itemnumber)


class CmdAttack(MuxCommand):
    """
    Attack another character in combat.
    Usage:
      hit <target> [optional custom attack message]

    Examples:
    > attack Antagonist
    Protagonist attacks Antagonist! |522[Melee attack roll vs. Antagonist: |5445|522]|n

    > attack Antagonist fires an energy ball at <target>!
    Protagonist fires an energy ball at Antagonist! |525[Ranged attack roll vs. Antagonist: |5453|525]|n

    > attack Antagonist A kick from <self> heads for <target>!
    A kick from Protagonist heads for Antagonist! |522[Melee attack roll vs. Antagonist: |5442|522]|n

    The 'attack' command can only be used once a fight has started (see 'help
    fight'). When used, it makes a random attack roll against your given target. The
    attack roll's result can be anywhere from 1 to your ATM or ATR stat. Your target
    then responds to the attack, usually by defending - if your attack roll is
    greater than your target's defense roll, your target takes damage equal to the
    difference.

    If your target is at range 0, you use your ATM (Melee Attack) stat to attack -
    otherwise, you use your ATR (Ranged Attack) stat. You can't use ranged attacks
    at all, however, if there are enemy fighters engaged (at range 0) with you. You
    can specify which fighters you consider friendly with the 'ally' command - see
    'help ally' for details.

    You can only use the attack command when it is your turn, and doing so uses your
    action for your turn.

    You can implement a custom message on the fly describing your attack if you
    would like - you can also create a pool of randomly selected pre-made combat
    messages to keep your attacks varied and flavorful. See 'help rangemessage' and
    'help meleemessage' details.
    """
    key = 'hit'
    aliases = ['strike']
    help_category = 'battle'

    def func(self):
        """This performs the actual command."""
        cmd_check = rules.cmd_check(self.caller, self.args, "attack",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasAction', 'AttacksResolved',
                                     'NeedsTarget', 'TargetNotSelf', 'TargetInFight', 'TargetHasHP'])
        attack_message = ''
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # Since the input was tested as valid, set the target here.
        target = self.caller.search(self.arglist[0])
        # Attack type is ranged if target is farther than range 0, or melee if target is at range 0
        attack_type = 'ranged'
        if self.caller.db.Combat_Range[target] == 0:
            attack_type = 'melee'
        # Check the attack type versus the target and give an error message if needed.
        type_check = rules.attack_type_check(self.caller, target, attack_type, [])
        if type_check:
            self.caller.msg(type_check)
            return
        if len(self.arglist) > 0:
            target = self.arglist[0]
            attack_message = 'default'
        if len(self.arglist) > 1:
            target = self.arglist[0]
            attack_message = self.args.split(None, 1)[1]
        # If everything checks out, queue the attack and spend the action.
        rules.queue_attack(self.caller, target, attack_message, [], attack_type)
        self.caller.db.Combat_LastAction = 'attack'
        self.caller.db.Combat_Actions -= 1


class CmdSecond(MuxCommand):
    """
    Use your second attack as part of a special move with the
    'Double Attack' effect. It must be of the same type as the
    first attack, and carries the same effect.
    """
    key = 'second'
    aliases = []
    help_category = 'battle'

    def func(self):
        """This performs the actual command."""
        if not self.caller.db.Combat_Second:
            self.caller.msg("|413You can't make a second attack!|n")
            return

        cmd_check = rules.cmd_check(self.caller, self.args, "attack",
                                    ['InCombat', 'IsTurn', 'HasHP', 'AttacksResolved',
                                     'NeedsTarget', 'TargetNotSelf', 'TargetInFight', 'TargetHasHP'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # Since the input was tested as valid, set the target here.
        target = self.caller.search(self.arglist[0])
        # The attack type is set to the previous attack type.
        attack_type = self.caller.db.Combat_Second[0]
        attack_message = ''
        type_check = rules.attack_type_check(self.caller, target, attack_type, [])
        # Also get the effects, if any.
        effects = self.caller.db.Combat_Second[1]
        if type_check:
            self.caller.msg(type_check)
            return
        if len(self.arglist) > 0:
            target = self.arglist[0]
            attack_message = "default"
        if len(self.arglist) > 1:
            target = self.arglist[0]
            attack_message = self.args.split(None, 1)[1]
        # If everything checks out, queue the attack and delete the second attack value.
        rules.queue_attack(self.caller, target, attack_message, effects, attack_type)
        self.caller.db.Combat_LastAction = "attack"
        del self.caller.db.Combat_Second


class CmdDefend(MuxCommand):
    """
    Defend from an attack in combat.

    Usage:
      defend

    Example:
    > defend
    Protagonist defends against Antagonist's attack! |225[Defense roll: |4458|225]|n

    > defend
    Protagonist takes |5552 damage|n from Antagonist's attack! |225[Defense roll: |4453|225]|n

    The 'defend' command is used to respond to when an opponent attacks you during
    their turn in combat. When you issue a command, a random defense roll is made -
    the roll's result can be anywhere from 1 to your DEF stat. If your defense roll
    exceeds or matches your opponent's attack roll, you take no damage. Otherwise,
    you take damage equal to the opponent's attack roll minus your defense roll.

    There are other options for responding to an attack, but 'defend' is the one you
    will use most often - if you don't respond to an attack within 30 seconds, you
    will defend automatically. Alternatively, you can, for whatever earthly reason,
    choose to take full damage from an attack instead of defending against it - see
    'help endure'.
    """
    key = 'defend'
    aliases = ["defense", "def", "block", "guard", "dodge", "df"]
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if not self.caller.db.Combat_IncomingAttack:
            # No incoming attacks.
            self.caller.msg('There are no incoming attacks!')
            return
        else:
            rules.defend_queue(self.caller, 'defend', [])


class CmdEndure(MuxCommand):
    """
    Defend from an attack in combat.

    Usage:
      endure

    Example:
    > endure
    Protagonist takes |5555 damage|n from Antagonist's attack! |225[Endure]|n

    The 'endure' command takes all damage from an incoming attack. You normally
    would never want to do this, but it may be useful if you have another ability
    that keys off of taking damage or being at low health, such as a special move
    with the 'Desperation Move' effect.
    """
    key = "endure"
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if not self.caller.db.Combat_IncomingAttack:
            # No incoming attacks.
            self.caller.msg("There are no incoming attacks!")
            return
        else:
            rules.defend_queue(self.caller, "endure", [])


class CmdRest(MuxCommand):
    """
    Restores all HP and SP. You must be in the recovery bay
    in order to use this command - use the 'return' command
    to teleport to the recovery bay if you fall in battle
    outside the grounds.
    """
    key = "rest"
    aliases = ["recover"]
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if self.caller.db.Combat_TurnHandler:
            # In combat.
            self.caller.msg("You can't rest, you're in a fight!")
            return
        if not self.caller.location.db.recoveryroom:
            # Not in a recovery room.
            self.caller.msg("You can't recover here!")
            return
        rules.recover(self.caller)


class CmdReturn(MuxCommand):
    """
    Returns you to the Institute of Battle's recovery bay.
    """
    key = "return"
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        if self.caller.db.Combat_TurnHandler:
            # In combat.
            self.caller.msg("You can't return, you're in a fight!")
            return
        if self.caller.location == self.caller.search("The Institute's Recovery Bay", global_search=True):
            # Already there.
            self.caller.msg("You're already at the recovery bay!")
            return
        if self.caller.location.is_typeclass("rooms.ChargenRoom"):
            # In a character generation room.
            self.caller.msg("You can't do that until you've entered the game!")
            return
        self.caller.location.msg_contents("With a flash of glowing green light, %s vanishes." % self.caller)
        self.caller.location = self.caller.search("The Institute's Recovery Bay", global_search=True)
        self.caller.execute_cmd("look")
        self.caller.location.msg_contents("%s appears in a flash of glowing green light." % self.caller)


class CmdAlly(MuxCommand):
    """
    View, add, or remove allies.

    Usage:
      ally[/switches] <target>

    Switches:
    /remove - Remove a character from your allies.

    Examples:
    > ally Friend
    You now consider Friend an ally.

    > ally
    You consider these fighters your allies:
    Friend
    Traitor
    Comrade

    > ally/remove Traitor
    You no longer consider Traitor an ally.

    List your allies, or add/remove people to your list of
    people considered allies. If you consider a fighter an
    ally, you will not block their movement or prevent
    them from using ranged attacks on other targets. Some
    special move effects might also include or exclude
    targets based on whether they are considered an ally
    by you or not.
    """

    key = "ally"
    aliases = ["allies", "friend", "team", "group"]
    help_category = 'battle'

    def func(self):
        """Performs the command."""
        if not self.switches:
            switches = []
        else:
            switches = self.switches
        # Create the ally list if it doesn't exist.
        if not self.caller.db.Allies:
            self.caller.db.Allies = []
        # Add an ally
        if "remove" not in switches:
            # If no arguments, list allies.
            if not self.args:
                if len(self.caller.db.Allies) == 0:
                    # The fighter has no friends and is a cool bad ass.
                    coollist = ["You walk alone", "A lone wolf", "None match your skill", "Trust only yourself",
                                "It's you against the world", "The sole survivor"]
                    coolmessage = coollist[randint(0, (len(coollist) - 1))]
                    self.caller.msg("You have no allies. %s." % coolmessage)
                    return
                # Otherwise, list allies.
                self.caller.msg("You consider these fighters your allies:")
                for ally in self.caller.db.Allies:
                    self.caller.msg(ally)
                return
            target = self.caller.search(self.args, global_search=True)
            if not target or not rules.is_fighter(target):
                self.caller.msg("Please specify a valid target.")
                return
            if target not in self.caller.db.Allies:
                self.caller.db.Allies.append(target)
                self.caller.msg("You now consider %s an ally." % target)
                return
            self.caller.msg("You already consider %s an ally." % target)
        if "remove" in self.switches:
            target = self.caller.search(self.args, global_search=True)
            if not target or not rules.is_fighter(target):
                self.caller.msg("Please specify a valid target.")
                return
            if target not in self.caller.db.Allies:
                self.caller.msg("You already don't consider %s an ally." % target)
                return
            self.caller.db.Allies.remove(target)
            self.caller.msg("You no longer consider %s an ally." % target)


class CmdStats(MuxCommand):
    """
    Displays your stats as well as your current HP and SP.

    Usage:
      stats

    Examples:
    > stats
    Protagonist's stats:
    -----------------------
       ATM: 7     ATR: 0
       DEF: 9     MOB: 8
       VIT: 7     SPE: 0
    -----------------------
      HP: 27/27  SP: 0/0

    This command will display your character's stats. You have 30 points to
    distribute between them as you like in character creation (see 'help setstat')
    and each one can range anywhere from 0 to 10. The stats and their uses are as
    follows:

    |522ATM - Melee Attack|n: This stat determines the effectiveness of your melee
    attacks. A character with a high ATM score will hit more often and do more
    damage with their close range attacks. You must be engaged (at range 0) with
    your target to use melee attacks - see 'help attack' for details.

    |525ATR - Ranged Attack|n: This stat determines the effectiveness of your ranged
    attacks. You don't have to be engaged with a target to use ranged attacks -
    however, you can't use ranged attacks if you are engaged with any hostile
    fighters. See 'help attack' for details.

    |225DEF - Defense|n: This stat determines the effectiveness of your defense. A
    character with a high DEF score will avoid attacks more often and take less
    damage from attacks. See 'help defend' for details.

    |252VIT - Vitality|n: This stat determines how much damage you can sustain before
    being defeated in battle. Your total HP is equal to three times your VIT stat -
    when you take damage, your HP is reduced by the damage given, and you are
    defeated when you reach 0 HP. A character with 0 VIT has only 1 HP.

    |552MOB - Mobility|n: This stat determines how much you can move during your turn. You
    gain a number of movement steps equal to half your MOB stat, rounded down (see
    'help approach' and 'help withdraw'), and can spend your action in a turn to
    gain extra movement equal to half your MOB rounded up (see 'help dash'). A
    character with 0 MOB can't change position in combat.

    |255SPE - Special|n: This stat determines how many special moves you can use in a
    fight. A character with a high SPE stat can more freely use powerful special
    moves by spending SP - more powerful special moves cost more SP. Your total SP
    is equal to two times your SP stat. A character with 0 SPE can't use special
    moves that cost SP.
    """
    key = 'stats'
    aliases = ["score", "sheet"]
    help_category = "battle"

    def func(self):
        """This performs the actual command."""
        name = self.caller
        attack_melee = self.caller.db.ATM
        defense = self.caller.db.DEF
        vitality = self.caller.db.VIT
        attack_range = self.caller.db.ATR
        mobility = self.caller.db.MOB
        special = self.caller.db.SPE
        hp = self.caller.traits.health.actual
        sp = self.caller.traits.special.actual
        max_hp = max(self.caller.db.VIT * 3, 1)
        max_sp = self.caller.db.SPE * 2
        current_hp = ("%i/%i" % (hp, max_hp))
        current_sp = ("%i/%i" % (sp, max_sp))
        self.caller.msg("%s's Stats:|/-------------------------|/   |522ATM: |544%i|n     |525ATR: |545%i|n|/"
                        "   |225DEF: |445%i|n     |552MOB: |554%i|n|/   |252VIT: |454%i|n     |255SPE:"
                        " |455%i|n|/-------------------------|/  |252HP:|n %s   |255SP|n: %s" %
                        (name, attack_melee, attack_range, defense, mobility, vitality, special,
                         current_hp, current_sp))


class CmdFight(MuxCommand):
    """
    Starts a fight with everyone in the current room.
    """
    key = 'fight'
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        char = self.character
        here = char.location
        fighters = []
        if not here.db.CombatAllowed:
            self.caller.msg("%s%s|n is no place for battles!" % (here.STYLE, here.key))
            return
        for thing in here.contents:
            if thing.traits.health.actual:
                fighters.append(thing)
        if len(fighters) <= 1:
            self.caller.msg("There's nobody here to fight!")
            return
        if here.db.Combat_TurnHandler:
            here.msg_contents("%s joins the fight!" % self.caller)
            here.db.Combat_TurnHandler.join_fight(self.caller)
            return
        here.msg_contents("%s starts a fight!" % self.caller)
        here.scripts.add("scripts.TurnHandler")


class CmdPass(MuxCommand):
    """Passes on your turn."""
    key = 'pass'
    aliases = ["wait", "hold"]
    help_category = "battle"

    def func(self):
        """This performs the actual command."""
        cmd_check = rules.cmd_check(self.caller, self.args, "pass", ['InCombat', 'IsTurn', 'AttacksResolved'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        if not self.args:
            message = ("%s takes no further action, waiting. |222[Pass]|n" % self.caller)
        else:
            if "<self>" not in self.args:
                message = ("%s %s |222[Pass]|n" % (self.caller, self.args))
            else:
                replaced = self.args.replace("<self>", str(self.caller))
                message = ("%s |222[Pass]|n" % replaced)
        self.caller.location.msg_contents(message)
        self.caller.db.Combat_LastAction = "pass"
        self.caller.db.Combat_Actions = 0
        self.caller.db.Combat_Moves = 0
        if self.caller.db.Combat_Second:
            del self.caller.db.Combat_Second


class CmdDisengage(MuxCommand):
    """Like 'pass', but can end combat."""
    key = "disengage"
    aliases = ["spare"]
    help_category = "battle"

    def func(self):
        """This performs the actual command."""
        cmd_check = rules.cmd_check(self.caller, self.args, "disengage", ['InCombat', 'IsTurn', 'AttacksResolved'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        if not self.args:
            message = ("%s seems ready to stop fighting. |222[Disengage]|n" % self.caller)
        else:
            if "<self>" not in self.args:
                message = ("%s %s |222[Disengage]|n" % (self.caller, self.args))
            else:
                replaced = self.args.replace("<self>", str(self.caller))
                message = ("%s |222[Disengage]|n" % replaced)
        self.caller.location.msg_contents(message)
        self.caller.db.Combat_LastAction = "disengage"
        self.caller.db.Combat_Actions = 0
        self.caller.db.Combat_Moves = 0
        if self.caller.db.Combat_Second:
            del self.caller.db.Combat_Second


class CmdWithdraw(MuxCommand):
    """
    Moves away another character.

    Usage:
    withdraw <target> [Optional number of steps]
    alias 'moveaway', 'retread', 'away', 'wd'

    Examples:
    > withdraw Enemy
    Protagonist withdraws to very far range with Enemy! |552[|5541|552 step]|n

    You can use this command to move away from other fighters.
    If you are engaged (at range 0) with any opponents, they have
    a chance to block some or all of your movement - this chance
    is based on a roll, rolling your mobility against their ATM
    or DEF stat (whichever is higher) for each step. Fighters who
    consider you an ally will not block your movement - see 'help
    ally' for details.

    You can withdraw a number of steps during your turn equal to
    half your MOB stat, rounded down - you can give up your action
    in combat to 'dash' and gain extra movement. See 'help dash'
    for details.

    Using this command with no arguments will use up your movement
    until you reach the edge of the room. You can instead move a
    limited number of steps by putting a number after the command.
    """
    key = "withdraw"
    aliases = ["moveaway", "retreat", "away", "wd"]
    help_category = "battle"

    def func(self):
        """This performs the actual command."""
        cmd_check = rules.cmd_check(self.caller, self.args, "withdraw",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasMove', 'AttacksResolved',
                                     'NeedsTarget', 'TargetNotSelf', 'TargetInFight'])
        who = ''
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # If everything checks out, check to see if an argument is given.
        distance = self.caller.db.Combat_Moves
        if len(self.arglist) > 0:
            who = self.arglist[0]
        if len(self.arglist) > 1:
            distance = self.arglist[1]
            try:  # Set distance to integer given or max movement if arg isn't integer
                distance = max(1, int(distance))
            except (TypeError, ValueError):
                distance = self.caller.db.Combat_Moves
        target = self.caller.search(who)
        # Let's also make sure they aren't too far away.
        if self.caller.db.Combat_Range[target] >= self.caller.location.db.RoomSize:
            self.caller.msg("You can't move away any farther!")
            return
        # Let's make sure they don't try to move farther than they can.
        if distance > self.caller.db.Combat_Moves:
            self.caller.msg("You don't have enough movement to move that many steps!")
            return
        # If everything checks out, queue the withdraw and spend the movement.
        rules.ms_withdraw(self.caller, target, distance, "normal")


class CmdApproach(MuxCommand):
    """
    Moves toward another character.

    Usage:
    approach <target> [Optional number of steps]
    alias 'move', 'step', 'moveto', 'ap'

    Examples:
    > approach Enemy
    Protagonist approaches to very close range with Enemy! |552[|5541|552 step]|n

    You can use this command to get closer to your opponents or
    allies. You will also move closer to any other fighters who
    are closer to your target than you are, and move further
    away from any fighters who are farther from your target
    than you are - if this involves leaving engaged range with
    a fighter, they may block your movement. See 'help withdraw'
    for more details.

    You can approach a number of steps during your turn equal to
    half your MOB stat, rounded down - you can give up your action
    in combat to 'dash' and gain extra movement. See 'help dash'
    for details.

    Using this command with no arguments uses up your movement
    until you reach your target. You can instead specify a number
    of steps to move by putting a number at the end of the
    command.
    """
    key = "approach"
    aliases = ["move", "step", "moveto", "ap"]
    help_category = 'battle'

    def func(self):
        """This performs the actual command."""
        cmd_check = rules.cmd_check(self.caller, self.args, "approach",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasMove', 'AttacksResolved',
                                     'NeedsTarget', 'TargetInFight', 'TargetNotSelf', 'TargetNotEngaged'])
        who = ''
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # If everything checks out, check to see if an argument is given.
        distance = self.caller.db.Combat_Moves
        if len(self.arglist) > 0:
            who = self.arglist[0]
        if len(self.arglist) > 1:
            distance = self.arglist[1]
            try:
                distance = max(1, int(distance))
            except (TypeError, ValueError):
                distance = self.caller.db.Combat_Moves
        target = self.caller.search(who)
        # Let's make sure they don't try to move farther than they can.
        if distance > self.caller.db.Combat_Moves:
            self.caller.msg("You don't have enough movement to move that many steps!")
            return
        # Calls the multi-step function, which also takes care of spending the movement.
        rules.ms_approach(self.caller, target, distance, "normal")


class CmdDash(MuxCommand):
    """
    Spend your action to get more movement.

    Usage:
    dash [optional custom message]

    alias 'run', 'hustle'

    Examples:
    > dash
    Protagonist dashes for extra movement! |552[|554+3|552 Movement]|n

    > dash sprints across the room!
    Protagonist sprints across the room! |552[|554+3|552 Movement]|n

    You can spend your action in combat in order to get more movement
    if you need to close the distance between you and an opponent, or
    put some distance between you and a foe who's dangerous up close.
    Dashing will give you a number of extra movement steps equal to
    half your MOB stat rounded up.
    """
    key = "dash"
    aliases = ["run", "hustle"]
    help_category = 'battle'

    def func(self):
        """This performs the actual command."""
        cmd_check = rules.cmd_check(self.caller, self.args, "dash",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasAction', 'AttacksResolved'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # Check for immobilization.
        if 'Immobilization' in self.caller.db.Combat_Conditions:
            self.caller.msg("You're immobilized! You can't move!")
            return
        if not self.args:
            message = ("%s dashes for extra movement!" % self.caller)
        else:
            message = ("%s %s" % (self.caller, self.args))
        self.caller.db.Combat_Actions -= 1
        self.caller.db.Combat_LastAction = "dash"
        self.caller.db.Combat_Moves += int(math.ceil(float(self.caller.db.MOB) / 2))
        self.caller.location.msg_contents(
            "%s |552[|554+%i|552 Movement]|n" % (message, int(math.ceil(float(self.caller.db.MOB) / 2))))


class CmdCharge(MuxCommand):
    """Prepare a special move."""
    key = "charge"
    aliases = ["ready", "prepare"]
    help_category = 'battle'

    def func(self):
        """
        This performs the actual command.
        """
        cmd_check = rules.cmd_check(self.caller, self.args, "dash", ['InCombat', 'IsTurn', 'HasHP',
                                                                     'HasAction', 'AttacksResolved'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        if not self.caller.db.Combat_Charged:
            self.caller.db.Combat_Charged = []
        if len(self.arglist) == 0:
            self.caller.msg("|413You need to specify a special move name!")
            return
        matchedspecial = ""
        message = ("%s prepares a special move!" % self.caller)
        if len(self.arglist) > 0:
            for special in self.caller.db.Special_Moves:
                if self.arglist[0].lower() in special.lower():
                    matchedspecial = special
            if matchedspecial == "":
                self.caller.msg("|413You don't have that special move!")
                return
            if "Charge Move" not in self.caller.db.Special_Moves[matchedspecial][1]:
                self.caller.msg("|413You don't need to charge that move!")
                return
            if matchedspecial in self.caller.db.Combat_Charged:
                self.caller.msg("|413That move is already charged!")
                return
        if len(self.arglist) > 1:
            # Process a custom message.
            message = self.args.split(None, 1)[1]
            if "<self>" not in message:
                message = "<self> " + message
            message = message.replace("<self>", str(self.caller))
        # If everything checks out, add the special to the charged list.
        self.caller.db.Combat_Charged.append(matchedspecial)
        self.caller.db.Combat_Actions -= 1
        self.caller.db.Combat_LastAction = "charge"
        self.caller.location.msg_contents("%s |255[Charge: |455%s|255]|n" % (message, matchedspecial))


class CmdRange(MuxCommand):
    """
    Displays your distance to other fighters in combat.

    Usage:
    range [optional target]

    Examples:
    > range
    Antagonist: Engaged (0 steps away)
    Bob and Alice: Close (2 steps away)
    Claire: Close (2 steps away)

    > range Antagonist
    Antagonist: Engaged (0 steps away)


    This command shows how far away you are from each other fighter in combat, or
    optionally just your range to one target. Fighters that are engaged (at range 0)
    with each other are grouped together, and considered to be sharing the same
    space.

    The ranges are as follows, by steps away:

    0: Engaged
    1: Very Close
    2: Close
    3: Medium-Close
    4: Medium
    5: Medium-Far
    6: Far
    7: Very Far
    8: Distant
    9: Very Distant
    10: Remote

    The maximum distance you can get from an opponent is determined by the size of
    the room the fight is taking place in. You can use your movement during your
    turn to approach or withdraw from targets to change your range to them (see
    'help approach' and 'help withdraw').
    """
    key = "range"
    aliases = ["distance", "ranges", "position"]
    help_category = 'battle'

    def func(self):
        """This performs the actual command."""
        if not self.caller.db.Combat_TurnHandler:
            self.caller.msg("You can only use this command in combat!")
            return
        target = self.caller.search(self.args, quiet=True)
        if target:
            target = target[0]
            targetrange = self.caller.db.Combat_Range[target]
            self.caller.msg("|525%s: |545%i|525 steps away (%s)" % (target, targetrange, rules.range_name(targetrange)))
            return
        else:
            rangelist = self.caller.db.Combat_Range
            accountedfor = []
            for key in rangelist:
                targetrange = self.caller.db.Combat_Range[key]
                if key != self.caller and key not in accountedfor:
                    engage_group = rules.get_engage_group(key)
                    if self.caller in engage_group:
                        engage_group.remove(self.caller)
                    if len(engage_group) == 1:
                        self.caller.msg(
                            "|525%s: |545%i|525 steps away (%s)" % (key, targetrange, rules.range_name(targetrange)))
                        accountedfor.append(key)
                    if len(engage_group) > 1:
                        engage_list = utils.list_to_string(engage_group, endsep="and", addquote=False)
                        self.caller.msg("|525%s: |545%i|525 steps away (%s)" %
                                        (engage_list, targetrange, rules.range_name(targetrange)))
                        accountedfor.extend(engage_group)
            return


class CmdSetSpecial(MuxCommand):
    """
    Launches the special move creation menu.
    """
    key = 'setspecial'
    aliases = ["newspecial", "addspecial"]
    help_category = 'battle'

    def func(self):
        """Starts the special creation EvMenu instance"""
        evmenu.EvMenu(self.caller, 'typeclasses.special_menu', startnode='menunode_specialtype')


class CmdSpecial(MuxCommand):
    """
    Use one of your special moves.

    Usage:
    special <one word from special move name> <target, if needed> [optional message]
    alias 'spe', 'sp'

    Examples:
    > special megaton Antagonist
    |255[Special: |455Megaton Punch|255 (|4554|255 SP)]|n Protagonist uses a special attack on Antagonist!
    |522[Attack roll vs. Antagonist: |5445|522]|n |255[|455Knockback |255and|455 Double Damage|255]|n

    > special force
    |255[Special: |455Force Field|255 (|4554|255 SP)]|n Protagonist uses a special defense! |255[|455Perfect|n
    |455Defense|255]|n

    > special beam Antagonist fires a beam of energy at <target>!
    |255[Special: |455Hyper Beam|255 (|4554|255 SP)]|n Protagonist fires a beam of energy at Antagonist!
    |522[Attack roll vs. Antagonist: |5447|522]|n |255[|455Boosted Range |255and|455 Defense Bypass|255]|n

    The 'special' command is used to use one of your character's special moves. A
    special move can take the place of your normal attack roll or defense roll, and
    have varying effects depending on those chosen when the special move is created
    (see 'help setspecial'). Your character's special moves will set them apart from
    other characters with similar stats and can be employed strategically to turn
    the tide of battle.

    Most special moves cost SP to use - your total SP is equal to double your SPE
    stat. Having a higher SPE stat means you can use more potent special moves and
    use them more frequently. Special moves that are balanced to an SP cost of 0 by
    a cost-reducing limit or drawback effect can be used at will. A character with a
    SPE stat of 0 will only be able to use special moves that cost 0 SP.

    Special moves can only be used on your turn, and will use your action for the
    turn - with the exception of special defense moves, which are used in place of a
    defense roll.

    Like with regular attacks, you can provide a custom message with your special
    move at the end of the command. You can also set them ahead of time with the
    'specialmessage' command. See 'help specialmessage' for details.
    """
    key = "special"
    aliases = ["spe", "sp"]
    help_category = 'battle'

    def func(self):
        # If no arguments, list the special moves.
        if not self.args:
            for special in self.caller.db.Special_Moves:
                self.caller.msg(rules.pretty_special(self.caller, special) + "\n\n")
            return
        # If already used a special this turn (after gaining a bonus action), return.
        if self.caller.db.Combat_UsedSpecial:
            self.caller.msg("You already used a special move this turn!")
            return
        # First, let's try to match the first argument to a special move name.
        # matched = False
        for special_name in self.caller.db.Special_Moves:
            if self.arglist[0].lower() in special_name.lower():
                matched = special_name
                if rules.special_cost(self.caller.db.Special_Moves[special_name][1]) > self.caller.db.SP:
                    self.caller.msg("|413You don't have enough SP to use %s!" % matched)
                    return
                special_message = "default"
                # If there's a 'Desperation Move' or 'Vital Move' effect, check the user's HP first.
                if "Desperation Move" in self.caller.db.Special_Moves[special_name][1]:
                    if self.caller.traits.health.actual > self.caller.traits.stat_vit.actual:
                        self.caller.msg("|413You have too much HP to use %s!" % special_name)
                        return
                if "Vital Move" in self.caller.db.Special_Moves[special_name][1]:
                    if self.caller.traits.health.actual < self.caller.traits.stat_vit.actual * 2:
                        self.caller.msg("|413You don't have enough HP to use %s!" % special_name)
                        return
                # If there's a 'Charge Move' effect, check to see if it's charged.
                if "Charge Move" in self.caller.db.Special_Moves[special_name][1]:
                    if not self.caller.db.Combat_Charged or special_name not in self.caller.db.Combat_Charged:
                        self.caller.msg(
                            "|413You need to spend an action to charge this move first! Use the 'charge' command!|n")
                        return
                    # Remove the special from the charged list.
                    if special_name in self.caller.db.Combat_Charged:
                        self.caller.db.Combat_Charged.remove(special_name)
                # If there's an 'Opening Gambit' effect, check to see if the last action was null.
                if "Opening Gambit" in self.caller.db.Special_Moves[special_name][1]\
                        and self.caller.db.Combat_LastAction != "null":
                    self.caller.msg("|413You can only use %s on your first turn in combat!|n" % special_name)
                    return
                # If the special type is a Special Melee Attack:
                if self.caller.db.Special_Moves[special_name][0] == "Special Melee Attack":
                    if len(self.arglist) < 2:
                        self.caller.msg("|413You need to specify a target!")
                        return
                    if len(self.arglist) > 2:
                        special_message = self.args.split(None, 2)[2]
                    # If everything checks out, move to the special_attack function as melee!
                    self.special_attack(self.caller, matched, self.caller.db.Special_Moves[special_name][1],
                                        self.arglist[1], special_message, "melee")
                # If the special type is a Special Ranged Attack:
                if self.caller.db.Special_Moves[special_name][0] == "Special Ranged Attack":
                    if len(self.arglist) < 2:
                        self.caller.msg("|413You need to specify a target!")
                        return
                    if len(self.arglist) > 2:
                        special_message = self.args.split(None, 2)[2]
                    # If everything checks out, move to the special_attack function as ranged!
                    self.special_attack(self.caller, matched, self.caller.db.Special_Moves[special_name][1],
                                        self.arglist[1], special_message, "ranged")
                # If the special type is Support Self:
                if self.caller.db.Special_Moves[special_name][0] == "Support Self":
                    if len(self.arglist) > 1:
                        special_message = self.args.split(None, 1)[1]
                    # If everything checks out move to the support_self function!
                    self.support_self(self.caller, matched, self.caller.db.Special_Moves[special_name][1],
                                      special_message)
                # If the special type is Support Other:
                if self.caller.db.Special_Moves[special_name][0] == "Support Other":
                    if len(self.arglist) < 2:
                        self.caller.msg("|413You need to specify a target!")
                        return
                    if len(self.arglist) > 2:
                        special_message = self.args.split(None, 2)[2]
                    # If everything checks out, move to the support other function!
                    self.support_other(self.caller, matched, self.caller.db.Special_Moves[special_name][1],
                                       self.arglist[1], special_message)
                # If the special type is Hinder Other:
                if self.caller.db.Special_Moves[special_name][0] == "Hinder Other":
                    if len(self.arglist) < 2:
                        self.caller.msg("|413You need to specify a target!")
                        return
                    if len(self.arglist) > 2:
                        special_message = self.args.split(None, 2)[2]
                    # If everything checks out, move to the hinder other function!
                    self.hinder_other(self.caller, matched, self.caller.db.Special_Moves[special_name][1],
                                      self.arglist[1], special_message)
                # If the special type is Special Defense:
                if self.caller.db.Special_Moves[special_name][0] == "Special Defense":
                    if len(self.arglist) > 1:
                        special_message = self.args.split(None, 1)[1]
                    # If everything checks out move to the special_defense function!
                    self.special_defense(self.caller, matched, self.caller.db.Special_Moves[special_name][1],
                                         special_message)
                return
        self.caller.msg("|413You don't have that special move!")

    def special_attack(self, user, name, effects, target, special_message, attack_type):
        # Check for pre-set special messages if none was given via the command:
        if special_message == "default":
            try:
                special_message = "<self> uses a special attack on <target>!"
                if len(user.db.Special_Messages[name]) > 0:
                    special_message = user.db.Special_Messages[name][
                        randint(0, len(user.db.Special_Messages[name]) - 1)]
            except (KeyError, TypeError):
                special_message = "<self> uses a special attack on <target>!"
        if "<self>" not in special_message:
            special_message = "<self> " + special_message
        # If the special move type is "Special Attack", run this code!

        cmd_check = rules.cmd_check(user, target, "special attack",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasAction', 'AttacksResolved',
                                     'NeedsTarget', 'TargetNotSelf', 'TargetInFight', 'TargetHasHP'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return

        # Check the attack type versus the target and give an error message if needed.
        type_check = rules.attack_type_check(self.caller, target, attack_type, effects)
        if type_check:
            self.caller.msg(type_check)
            return

        # If everything checks out, spend the SP, queue the special attack and spend the action.
        user.db.SP -= rules.special_cost(effects)
        target = user.search(target, quiet=True)[0]
        message = "|255[Special: |455%s|255 (|455%i|255 SP)]|n %s" %\
                  (name, rules.special_cost(effects), special_message)
        # If there's a lunge attack effect, move the user forward two spaces.
        if 'Lunge Attack' in effects:
            rules.ms_approach(user, target, 2, "free")

        # Queue the attack here.
        rules.queue_attack(user, target, message, effects, attack_type)

        # If there's a parting attack effect, move the user back two spaces.
        if 'Parting Attack' in effects:
            rules.ms_withdraw(user, target, 2, "free")

        # Handle drawback conditions here.
        rules.special_drawback(user, user, effects)

        user.db.Combat_LastAction = "special"
        user.db.Combat_Actions -= 1

    def support_self(self, user, name, effects, special_message):
        # Check for pre-set special messages if none was given via the command:
        if special_message == "default":
            try:
                special_message = "<self> uses a special move!"
                if len(user.db.Special_Messages[name]) > 0:
                    special_message = user.db.Special_Messages[name][
                        randint(0, len(user.db.Special_Messages[name]) - 1)]
            except (KeyError, TypeError):
                special_message = "<self> uses a special move!"
        if "<self>" not in special_message:
            special_message = "<self> " + special_message
        # If the special move type is "Support Self", run this code!
        cmd_check = rules.cmd_check(user, "", "use a special move",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasAction', 'AttacksResolved'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # If everything checks out, spend the SP, queue the special move and spend the action.
        user.db.SP -= rules.special_cost(effects)
        special_message = special_message.replace("<self>", str(user))
        message = "|255[Special: |455%s|255 (|455%i|255 SP)]|n %s" %\
                  (name, rules.special_cost(effects), special_message)
        if effects:
            effect_string = utils.list_to_string(effects, endsep="|255and|455", addquote=False)
            message += " |255[|455%s|255]|n" % effect_string
        self.caller.location.msg_contents(message)
        rules.special_support(user, user, effects)
        self.caller.db.Combat_LastAction = "special"
        self.caller.db.Combat_Actions -= 1
        # Handle drawback conditions here.
        rules.special_drawback(user, user, effects)
        # If there's a bonus action, give the user's action back.
        if 'Bonus Action' in effects:
            self.caller.db.Combat_Actions += 1
            self.caller.db.Combat_UsedSpecial = True

    def support_other(self, user, name, effects, target, special_message):
        # Check for pre-set special messages if none was given via the command:
        if special_message == "default":
            try:
                special_message = "<self> uses a special move on <target>!"
                if len(user.db.Special_Messages[name]) > 0:
                    special_message = user.db.Special_Messages[name][
                        randint(0, len(user.db.Special_Messages[name]) - 1)]
            except (KeyError, TypeError):
                special_message = "<self> uses a special move on <target>!"
        if "<self>" not in special_message:
            special_message = "<self> " + special_message
        # If the special move type is "Support Other", run this code!

        cmd_check = rules.cmd_check(user, target, "special support",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasAction', 'AttacksResolved',
                                     'NeedsTarget', 'TargetNotSelf', 'TargetInFight', 'TargetHasHP'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # Set the target, since it was checked above.
        target = user.search(target, quiet=True)[0]
        # If there's 'Touch Effect', it can only be used on engaged targets.
        if "Touch Effect" in effects:
            if user.db.Combat_Range[target] != 0:
                user.msg("|413You can only use this special move on engaged targets (at range 0)!|n")
                return
        # If everything checks out, spend the SP, queue the special move and spend the action.
        user.db.SP -= rules.special_cost(effects)

        special_message = special_message.replace("<self>", str(user))
        special_message = special_message.replace("<target>", str(target))
        message = "|255[Special: |455%s|255 (|455%i|255 SP)]|n %s" %\
                  (name, rules.special_cost(effects), special_message)
        if effects:
            effect_string = utils.list_to_string(effects, endsep="|255and|455", addquote=False)
            message += " |255[|455%s|255]|n" % effect_string
        self.caller.location.msg_contents(message)
        rules.special_support(target, self.caller, effects)
        self.caller.db.Combat_LastAction = "special"
        self.caller.db.Combat_Actions -= 1
        # Handle drawback conditions here.
        rules.special_drawback(user, user, effects)
        # If there's a bonus action, give the user's action back.
        if 'Bonus Action' in effects:
            self.caller.db.Combat_Actions += 1
            self.caller.db.Combat_UsedSpecial = True

    def hinder_other(self, user, name, effects, target, special_message):
        # Check for pre-set special messages if none was given via the command:
        if special_message == "default":
            try:
                special_message = "<self> uses a special move on <target>!"
                if len(user.db.Special_Messages[name]) > 0:
                    special_message = user.db.Special_Messages[name][
                        randint(0, len(user.db.Special_Messages[name]) - 1)]
            except (KeyError, TypeError):
                special_message = "<self> uses a special move on <target>!"
        if "<self>" not in special_message:
            special_message = "<self> " + special_message
        # If the special move type is "Hinder Other", run this code!

        cmd_check = rules.cmd_check(user, target, "special support",
                                    ['InCombat', 'IsTurn', 'HasHP', 'HasAction', 'AttacksResolved',
                                     'NeedsTarget', 'TargetNotSelf', 'TargetInFight', 'TargetHasHP'])
        if cmd_check:
            self.caller.msg(cmd_check)
            return
        # Set the target, since it was checked above.
        target = user.search(target, quiet=True)[0]
        # If there's 'Touch Effect', it can only be used on engaged targets.
        if "Touch Effect" in effects:
            if user.db.Combat_Range[target] != 0:
                user.msg("|413You can only use this special move on engaged targets (at range 0)!|n")
                return
        # If everything checks out, spend the SP, queue the special move and spend the action.
        user.db.SP -= rules.special_cost(effects)
        special_message = special_message.replace("<self>", str(user))
        special_message = special_message.replace("<target>", str(target))
        message = "|255[Special: |455%s|255 (|455%i|255 SP)]|n %s" %\
                  (name, rules.special_cost(effects), special_message)
        if effects:
            effectstring = utils.list_to_string(effects, endsep="|255and|455", addquote=False)
            message += " |255[|455%s|255]|n" % effectstring
        self.caller.location.msg_contents(message)
        rules.special_hinder(target, self.caller, effects)
        self.caller.db.Combat_LastAction = "special"
        self.caller.db.Combat_Actions -= 1
        # Handle drawback conditions here.
        rules.special_drawback(user, user, effects)
        # If there's a bonus action, give the user's action back.
        if 'Bonus Action' in effects:
            self.caller.db.Combat_Actions += 1
            self.caller.db.Combat_UsedSpecial = True

    def special_defense(self, user, name, effects, special_message):
        if not user.db.Combat_IncomingAttack:
            # No incoming attacks.
            user.msg("|413There are no incoming attacks!")
            return
        attack_type = user.db.Combat_IncomingAttack[3]
        if special_message == "default":
            try:
                special_message = "<self> uses a special move!"
                if len(user.db.Special_Messages[name]) > 0:
                    special_message = user.db.Special_Messages[name][
                        randint(0, len(user.db.Special_Messages[name]) - 1)]
            except (KeyError, TypeError):
                special_message = "<self> uses a special move!"
        if "<self>" not in special_message:
            special_message = "<self> " + special_message

            # If the special move type is "Special Defense", run this code!
        # Test for melee-only and ranged-only defense
        if attack_type == "melee" and "Ranged-Only Defense" in effects:
            user.msg("|413You can only use this defense against ranged attacks!")
            return
        if attack_type == "ranged" and "Melee-Only Defense" in effects:
            user.msg("|413You can only use this defense against melee attacks!")
            return

        # If there's a counterattack, make sure the defender can actually attack the offender in return
        if "Counterattack" in effects:
            # Attack type is ranged if target is farther than range 0, or melee if target is at range 0
            counterattack_type = "ranged"
            if user.db.Combat_Range[user.db.Combat_IncomingAttack[1]] == 0:
                counterattack_type = "melee"
            # Check the attack type versus the target and give an error message if needed.
            type_check = rules.attack_type_check(user, user.db.Combat_IncomingAttack[1], counterattack_type, [])
            if type_check:
                user.msg(type_check)
                return

        # If everything checks out, spend the SP and execute the special defense.
        user.db.SP -= rules.special_cost(effects)
        special_message = special_message.replace("<self>", str(user))
        message = "|255[Special: |455%s|255 (|455%i|255 SP)]|n %s" %\
                  (name, rules.special_cost(effects), special_message)
        effect_string = utils.list_to_string(effects, endsep="|255and|455", addquote=False)
        message += " |255[|455%s|255]|n" % effect_string
        self.caller.location.msg_contents(message)
        rules.defend_queue(user, "defend", effects)
        # Handle drawback conditions here. Target is given as the character whose turn it is in combat.
        rules.special_drawback(user.db.Combat_TurnHandler.db.fighters[user.db.Combat_TurnHandler.db.turn], user,
                               effects)


class CmdRemoveSpecial(MuxCommand):
    """
    Removes a special move.

    Usage:
    removespecial (special move name)

    Use this to get rid of a special move you
    don't want anymore. You can set new special
    moves with 'setspecial' in character generation.
    """

    key = "removespecial"

    def func(self):
        """This performs the actual command."""
        if not self.args or self.args == "" or self.args == " ":
            self.caller.msg("Please specify a special move name.")
            return
        for special in self.caller.db.Special_Moves:
            if self.args.lower() in special.lower():
                self.caller.msg("Special move %s deleted." % special)
                del self.caller.db.Special_Moves[special]
                return
        self.caller.msg("You don't have a special move named %s." % self.args)


class CmdEnterGame(MuxCommand):
    """
    enters the game

    Usage:
      enter game

    This command checks your character
    and lets you enter the game if there
    are no issues - if there is an issue
    with your character, you will be
    informed of it.
    """
    key = "enter game"

    def func(self):
        """Checks everything first!"""
        char = self.caller
        stats_total = char.db.ATM + char.db.DEF + char.db.VIT + char.db.ATR + char.db.MOB + char.db.SPE
        # Check for stats are too high.
        if stats_total > 36:
            char.msg("Your stats are %i points too high. You need to set some of your stats lower to enter the game." %
                     (stats_total - 36))
            return
        # Verify each special move and check for if too many special moves are set.
        special_count = 0
        for special in char.db.Special_Moves:
            special_count += 1
            # Check the special move for stat requirements, etc. - if it returns a message, print it and return.
            if rules.verify_special_move(self.caller, special):
                char.msg(rules.verify_special_move(self.caller, special))
                return
            if special_count > 5:
                char.msg("You have more than 5 special moves. You can only have 5! Remove some before continuing.")
                return
        # From here, the checks won't stop the account from entering the game, but will warn them first.
        if not self.args or self.args != "anyway":
            anyway = False
            special_count = 0
            # Stats are lower than the cap.
            if stats_total < 36:
                char.msg("Your stats total is less than 36! You can add %i more points of stats - try sticking them in "
                         "Vitality to get more HP if you don't know what else to do with them." % (36 - stats_total))
                anyway = True
            # Less than the capped number of special moves are defined.
            for special in char.db.Special_Moves:
                print(special)
                special_count += 1
            if special_count < 5:
                char.msg("You have less than five special moves set - you can set up to five. Even if you have 0 SP,"
                         " you can still use special moves with no SP cost by setting limits or drawbacks on them -"
                         " there's really no reason not to at least have the option!")
                anyway = True
            if anyway:
                char.msg("You can still enter the game by typing 'enter game anyway',"
                         " but your character will be weaker than others. You've been warned!")
                return
        # If it's all good, enter the grid!
        char.msg("Going on-grid. Prepare for battles!")
        char.location = char.search("Great Fog", global_search=True)
        char.execute_cmd("look")
