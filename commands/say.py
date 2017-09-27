# -*- coding: UTF-8 -*-
import re
from commands.command import MuxCommand
from evennia.utils import ansi
from evennia.utils.utils import pad, justify
from world.helpers import escape_braces


class CmdSay(MuxCommand):
    """
    Speak as your character.
    Usage:
      say[/option] <message>
    Options:
    /ooc  - Out-of-character to the room.
    /verb - set default say verb.
    """
    key = 'say'
    aliases = ['"', "'"]
    locks = 'cmd:all()'
    options = ('ooc', 'quote', 'verb')

    def func(self):
        """Run the say command"""
        char = self.character
        here = char.location if char else None
        account = self.account
        opt = self.switches
        args = self.args.strip()
        if not (here and char):
            if args:
                account.execute_cmd('pub %s' % args)
            else:
                account.msg('Usage: say <message>   to speak on public channel.')
            return
        if not args:
            account.execute_cmd("help say")
            return
        if 'verb' in opt:
            char.attributes.add('say-verb', args)
            here.msg_contents(text=('{char} warms up vocally with "%s|n"' % escape_braces(args),
                                    {'type': 'pose', 'action': True}),
                              from_obj=char, mapping=dict(char=char))
            return
        if 'quote' in opt:
            if len(args) > 2:
                char.quote = args  # Not yet implemented.
                return
        else:
            speech = args
            verb = char.attributes.get('say-verb') if char.attributes.has('say-verb') else 'says'
            if 'ooc' in opt:
                here.msg_contents(text=('[OOC] {char} says, "|w%s|n"' % escape_braces(speech),
                                        {'type': 'say', 'ooc': True}), from_obj=char, mapping=dict(char=char))
                if here.has_account:
                    here.msg(text=('[OOC] %s says, "|w%s|n"' % (char.get_display_name(here), escape_braces(speech)),
                                   {'type': 'say', 'ooc': True}), from_obj=char)
            else:
                here.msg_contents(text=('{char} %s, "|w%s|n"' % (escape_braces(verb), escape_braces(speech)),
                                        {'type': 'say'}), from_obj=char, mapping=dict(char=char))
                if here.has_account:
                    here.msg(text=('From inside you, %s %s, "|w%s|n"' %
                                   (char.get_display_name(here), escape_braces(verb),
                                    escape_braces(speech)), {'type': 'say'}), from_obj=char)


class CmdOoc(MuxCommand):
    """
    Send an out-of-character message to your current location.
    Usage:
      ooc <message>
      ooc :<message>
      ooc "<message>.
    """
    key = 'ooc'
    aliases = ['_']
    locks = 'cmd:all()'

    def func(self):
        """Run the ooc command"""
        char = self.character
        account = self.account
        here = char.location
        args = self.args.strip()
        if not args:
            account.execute_cmd('help ooc')
            return
        elif args[0] == '"' or args[0] == "'":
            account.execute_cmd('say/o ' + args[1:])
        elif args[0] == ':' or args[0] == ';':
            account.execute_cmd('pose/o %s' % args[1:])
        else:
            here.msg_contents(text=('[OOC {char}] %s' % escape_braces(args), {'type': 'ooc', 'ooc': True}),
                              from_obj=char, mapping=dict(char=char))
            if here.has_account:
                here.msg(text=('[OOC %s] %s' %
                               (char.get_display_name(here), escape_braces(args)),
                               {'type': 'ooc', 'ooc': True}), from_obj=char)


class CmdSpoof(MuxCommand):
    """
    Send a spoofed message to your current location.
    Usage:
      spoof <message>
    Switches:
    /dot . <msg>  Remove leading dot, but preserve leading spaces after it
    /center <msg> [ = position ]  Center msg at position
    /right <msg> [ = position ]   Align right at position
    /indent <msg> [ = position ]  Begin msg starting at position
    /news <message> [ = <width> [indent] ]
    /strip <message sent to room with markup stripped>
    /self <message only to you with full markup>
    """
    key = 'spoof'
    aliases = ['~', '`', 'sp']
    locks = 'cmd:all()'
    options = ('dot', 'center', 'right', 'indent', 'news', 'strip', 'self')

    def func(self):
        """Run the spoof command"""
        char = self.character
        here = char.location
        opt = self.switches
        args = self.args
        to_self = 'self' in opt or not here
        if not args:
            self.account.execute_cmd('help spoof')
            return
        # Optionally strip any markup /or/ just escape it,
        stripped = ansi.strip_ansi(args)
        spoof = stripped if 'strip' in opt else args.replace('|', '||')
        if 'indent' in opt:
            indent = 20
            if self.rhs:
                args = self.lhs.strip()
                indent = re.sub("[^0123456789]", '', self.rhs) or 20
                indent = int(indent)
            if to_self:
                char.msg(' ' * indent + args.rstrip())
            else:
                here.msg_contents(text=(' ' * indent + escape_braces(args.rstrip()), {'type': 'spoof'}))
        elif 'right' in opt or 'center' in opt or 'news' in opt:
            if self.rhs is not None:  # Equals sign exists.
                parameters = '' if not self.rhs else self.rhs.split()
                args = self.lhs.strip()
                if len(parameters) > 1:
                    if len(parameters) == 2:
                        outside, inside = self.rhs.split()
                    else:
                        outside, inside = [parameters[0], parameters[1]]
                    outside = re.sub("[^0123456789]", '', outside) or 0
                    inside = re.sub("[^0123456789]", '', inside) or 0
                    outside, inside = [int(max(outside, inside)), int(min(outside, inside))]
                else:
                    outside, inside = [72, 20]
            else:
                outside, inside = [72, min(int(self.rhs or 72), 20)]
            block = 'r' if 'right' in opt else 'f'
            block = 'c' if 'center' in opt else block
            for text in justify(args, width=outside, align=block, indent=inside).split('\n'):
                if to_self:
                    char.msg(text.rstrip())
                else:
                    here.msg_contents(text=(escape_braces(text.rstrip()), {'type': 'spoof'}))
        else:
            if 'strip' in opt:  # Optionally strip any markup or escape it,
                if to_self:
                    char.msg(spoof.rstrip(), options={'raw': True})
                else:
                    here.msg_contents(text=(escape_braces(spoof.rstrip()), {'type': 'spoof'}), options={'raw': True})
            elif 'dot' in opt:  # Leave leading spacing intact, remove leading dot.
                spoof = args.lstrip('.')
                if to_self:
                    char.msg(spoof.rstrip(), options={'raw': True})
                else:
                    here.msg_contents(text=(escape_braces(spoof.rstrip()), {'type': 'spoof'}), options={'raw': True})
            else:
                if to_self:
                    char.msg(args.rstrip())
                else:
                    here.msg_contents(text=(escape_braces(spoof.rstrip()), {'type': 'spoof'}))
