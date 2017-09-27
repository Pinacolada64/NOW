"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.
"""

from evennia import default_cmds

# from world.rpsystem import CmdSdesc, CmdEmote, CmdRecog, CmdMask  # RP commands used to be here.
from evennia.contrib.mail import CmdMail
from world.clothing import CmdWear, CmdRemove, CmdCover, CmdUncover, CmdGive

# [Traversal of path-exits]
from typeclasses.exits import CmdStop, CmdContinue, CmdBack, CmdSpeed

# [commands modules]
from commands import prelogin
from commands import exitdirections
from commands.suntime import CmdAstral
from commands.say import CmdSay, CmdOoc, CmdSpoof
from commands.set import CmdSettings
from commands.who import CmdWho
from commands.desc import CmdDesc
from commands.flag import CmdFlag
from commands.home import CmdHome
from commands.menu import CmdMenu
from commands.pose import CmdPose
from commands.quit import CmdQuit
from commands.verb import CmdTry
from commands.zeit import CmdTime
from commands.zone import CmdZone
from commands.about import CmdAbout
from commands.sense import CmdSense
from commands.summon import CmdSummon
from commands.access import CmdAccess
from commands.whisper import CmdWhisper
from commands.channel import CmdChannels
from commands.teleport import CmdTeleport
from commands.inventory import CmdInventory


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands available to
    in-world Character objects. It is merged with the `AccountCmdSet` when
    an Account puppets a Character.
    """
    key = 'DefaultCharacter'

    def at_cmdset_creation(self):
        """Populates the DefaultCharacter cmdset"""

        super(CharacterCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.remove(default_cmds.CmdGet)
        self.remove(default_cmds.CmdSay)
        self.remove(default_cmds.CmdDrop)
        self.remove(default_cmds.CmdGive)  # Now handled by world/clothing
        self.remove(default_cmds.CmdLook)   # Now handled by sense command, along with 4 other senses
        self.remove(default_cmds.CmdPose)
        self.remove(default_cmds.CmdTime)   # Moved to account command
        self.remove(default_cmds.CmdAbout)
        self.remove(default_cmds.CmdAccess)
        self.remove(default_cmds.CmdSetHome)  # Replaced with home/set and home/here
        self.remove(default_cmds.CmdDestroy)  # Reuse instead of destroy database objects.
        self.remove(default_cmds.CmdTeleport)  # Teleport has cost and conditions.
# [...]
        self.add(CmdOoc)
        self.add(CmdSay)
        self.add(CmdTry)
        self.add(CmdDesc)
        self.add(CmdFlag)
        self.add(CmdGive)
        self.add(CmdHome)
        self.add(CmdPose)
        self.add(CmdZone)
        self.add(CmdSpoof)
        self.add(CmdSummon)
        self.add(CmdWhisper)
        self.add(CmdInventory)
# [...]
        # Clothing contrib commands
        self.add(CmdWear)
        self.add(CmdRemove)
        self.add(CmdCover)
        self.add(CmdUncover)
# [...]
        self.add(CmdStop)
        self.add(CmdBack)
        self.add(CmdSpeed)
        self.add(CmdContinue)
# [...]
        self.add(exitdirections.CmdExitNorth())
        self.add(exitdirections.CmdExitSouth())
        self.add(exitdirections.CmdExitEast())
        self.add(exitdirections.CmdExitWest())
        self.add(exitdirections.CmdExitNortheast())
        self.add(exitdirections.CmdExitNorthwest())
        self.add(exitdirections.CmdExitSoutheast())
        self.add(exitdirections.CmdExitSouthwest())
        self.add(exitdirections.CmdExitUp())
        self.add(exitdirections.CmdExitDown())


class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """
    key = 'DefaultAccount'

    def at_cmdset_creation(self):
        """Populates the DefaultAccount cmdset"""
        super(AccountCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.remove(default_cmds.CmdCWho)
        self.remove(default_cmds.CmdCBoot)
        self.remove(default_cmds.CmdPage)
        self.remove(default_cmds.CmdCdesc)
        self.remove(default_cmds.CmdClock)
        self.remove(default_cmds.CmdCemit)
        self.remove(default_cmds.CmdAddCom)
        self.remove(default_cmds.CmdDelCom)
        self.remove(default_cmds.CmdAllCom)
        self.remove(default_cmds.CmdCdestroy)
        self.remove(default_cmds.CmdChannelCreate)
        self.add(CmdSay)
        self.add(CmdTry)
        self.add(CmdWho)
        self.add(CmdMail)
        self.add(CmdPose)
        self.add(CmdQuit)
        self.add(CmdTime)
        self.add(CmdAbout)
        self.add(CmdSense)
        self.add(CmdAccess)
        self.add(CmdChannels)
        self.add(CmdSettings)
        self.add(CmdTeleport)
        # self.add(CmdChannelWizard) # TODO: Still under development.


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """
    key = 'DefaultUnloggedin'

    def at_cmdset_creation(self):
        """Populates the DefaultUnloggedin cmdset"""
        super(UnloggedinCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.add(prelogin.CmdWhoUs())


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in.
    It is empty by default.
    """
    key = 'DefaultSession'

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super(SessionCmdSet, self).at_cmdset_creation()
        self.add(CmdMenu)
        # any commands you add below will overload the default ones.
