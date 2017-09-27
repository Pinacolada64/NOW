# -*- coding: UTF-8 -*-
"""
Commands

Commands describe the input the account can do to the world.

"""
import time  # Check time since last activity
from evennia.utils import inherits_from
from evennia import default_cmds
from evennia import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand, MuxAccountCommand


class Command(BaseCommand):
    """
    Inherit from this if you want to create your own
    command styles. Note that Evennia's default commands
    use MuxCommand instead (next in this module).

    Note that the class's `__doc__` string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.

    Each Command implements the following methods, called
    in this order:
        - at_pre_command(): If this returns True, execution is aborted.
        - parse(): Should perform any extra parsing needed on self.args
            and store the result on self.
        - func(): Performs the actual work.
        - at_post_command(): Extra actions, often things done after
            every command, like prompts.
    """
    key = "MyCommand"
    aliases = []
    locks = "cmd:all()"
    help_category = "General"

    def at_pre_cmd(self):
        """
        This hook is called before `self.parse()` on all commands.
        """
        pass

    def parse(self):
        """
        This method is called by the `cmdhandler` once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from `self.func()` (see below).

        The following variables are available to us:
           # class variables:

           self.key - the name of this command ('mycommand')
           self.aliases - the aliases of this cmd ('mycmd','myc')
           self.locks - lock string for this command ("cmd:all()")
           self.help_category - overall category of command ("General")

           # added at run-time by `cmdhandler`:

           self.caller - the object calling this command
           self.cmdstring - the actual command name used to call this
                            (this allows you to know which alias was used,
                             for example)
           self.args - the raw input; everything following `self.cmdstring`.
           self.cmdset - the `cmdset` from which this command was picked. Not
                         often used (useful for commands like `help` or to
                         list all available commands etc).
           self.obj - the object on which this command was defined. It is often
                         the same as `self.caller`.
        """
        pass

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        self.caller.msg('Command "%s" called!' % self.cmdstring)

    def at_post_cmd(self):
        """
        This hook is called after `self.func()`.
        """
        pass


class MuxCommand(default_cmds.MuxCommand):
    """
    This sets up the basis for Evennia's 'MUX-like' command style.
    The idea is that most other Mux-related commands should
    just inherit from this and don't have to implement parsing of
    their own unless they do something particularly advanced.

    A MUXCommand command understands the following possible syntax:

        name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]

    The `name[ with several words]` part is already dealt with by the
    `cmdhandler` at this point, and stored in `self.cmdname`. The rest is stored
    in `self.args`.

    The MuxCommand parser breaks `self.args` into its constituents and stores them
    in the following variables:
        self.switches = optional list of /switches (without the /).
        self.raw = This is the raw argument input, including switches.
        self.args = This is re-defined to be everything *except* the switches.
        self.lhs = Everything to the left of `=` (lhs:'left-hand side'). If
                     no `=` is found, this is identical to `self.args`.
        self.rhs: Everything to the right of `=` (rhs:'right-hand side').
                    If no `=` is found, this is `None`.
        self.lhslist - `self.lhs` split into a list by comma.
        self.rhslist - list of `self.rhs` split into a list by comma.
        self.arglist = list of space-separated args (including `=` if it exists).

    All args and list members are stripped of excess whitespace around the
    strings, but case is preserved.
    """
    account_caller = True  # By default, assume caller is account.
    parse_using = ''  # If set, use additional left/right delimiter.
    options = ()  # If set, use only these options, ignoring any others.

    def at_pre_cmd(self):
        """
        This hook is called before self.parse() on all commands
        """
        self.command_time = time.time()

    def parse(self):
        """
        This method is called by the cmdhandler once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from self.func()
        """
        super(MuxCommand, self).parse()
        # Parse mux options, comparing them against user-provided options, expanding abbreviations.
        if self.options and self.switches:  # If specific options are known, test them against given options.
            valid_options,  unuse_options, extra_options = [], [], []
            for element in self.switches:
                option_check = [each for each in self.options if each.lower().startswith(element.lower())]
                if len(option_check) > 1:
                    extra_options += option_check    # Either the option provided is ambiguous,
                elif len(option_check) == 1:
                    valid_options += option_check    # or it is a valid option abbreviation,
                elif len(option_check) == 0:
                    unuse_options += [element]       # or an extraneous option to be ignored.
            if extra_options:
                self.caller.msg('|g%s|n: |wAmbiguous option used. Did you mean /|C%s|w?' %
                                (self.cmdstring, '|nor /|C'.join(extra_options)))
            if valid_options:
                self.switches = valid_options
            if unuse_options:
                plural = '' if len(unuse_options) == 1 else 's'
                self.caller.msg('|g%s|n: |wExtra option%s "/|C%s|w" ignored.' %
                                (self.cmdstring, plural, '|n, /|C'.join(unuse_options)))
        # Now parse left/right sides using a custom delimiter, if provided.
        if self.parse_using and self.parse_using in self.args:
            self.lhs, self.rhs = self.args.split(self.parse_using, 1)  # At most, split once, into left and right parts.

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        super(MuxCommand, self).func()

    def at_post_cmd(self):
        """
        This hook is called after the command has finished executing
        (after self.func()).
        """
        char = self.character
        account = self.account
        here = char.location if char else None
        who = account.key if account else (char if char else '-visitor-')
        cmd = self.cmdstring if self.cmdstring != '__nomatch_command' else ''
        if here:
            if char.db.settings and 'broadcast commands' in char.db.settings and \
                            char.db.settings['broadcast commands'] is True:
                for each in here.contents:
                    if each.has_account:
                        if each == self or each.db.settings and 'see commands' in each.db.settings and\
                                        each.db.settings['see commands'] is True:
                            each.msg('|r(|w%s|r)|n %s%s|n' % (char.key, cmd, self.raw.replace('|', '||')))
        command_time = time.time() - self.command_time
        if account:
            account.db._command_time_total = (0 if account.db._command_time_total is None
                                             else account.db._command_time_total) + command_time
        if char:
            if char.traits.ct is None:
                char.traits.add('ct', 'Core Time', 'counter')
            if char.traits.cc is None:
                char.traits.add('cc', 'Core Count', 'counter')
            char.traits.ct.current += command_time
            char.traits.cc.current += 1
        print(u'{}> {}{} ({:.4f})'.format(who, cmd, self.raw, command_time))


class MuxAccountCommand(MuxCommand):
    """
    This is an on-Account version of the MuxCommand. Since these commands sit
    on Accounts rather than on Characters/Objects, we need to check
    this in the parser.
    Account commands are available also when puppeting a Character, it's
    just that they are applied with a lower priority and are always
    available, also when disconnected from a character (i.e. "ooc").
    This class makes sure that caller is always an Account object, while
    creating a new property "character" that is set only if a
    character is actually attached to this Account and Session.
    """
    def parse(self):
        """
        We run the parent parser as usual, then fix the result
        """
        super(MuxAccountCommand, self).parse()

        if inherits_from(self.caller, "evennia.objects.objects.DefaultObject"):
            self.character = self.caller  # caller is an Object/Character
            self.caller = self.caller.account
        elif inherits_from(self.caller, "evennia.accounts.accounts.DefaultAccount"):
            self.character = self.caller.get_puppet(self.session)  # caller was already an Account
        else:
            self.character = None
