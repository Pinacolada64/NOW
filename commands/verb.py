# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia import syscmdkeys, Command
from evennia.utils.utils import string_suggestions
from world.verbs import VerbHandler


class CmdTry(MuxCommand):
    """
    Actions a character can do to things nearby.
    Usage:
      ppose <parse> = <pose>
      try <parse>
      <parse>
    """
    key = syscmdkeys.CMD_NOMATCH
    aliases = 'try'
    auto_help = False
    locks = 'cmd:all()'
    arg_regex = r'\s|$'
    account_caller = True

    def func(self):
        """
        Run the try command
        """
        account = self.account
        char = self.character
        if not char:
            account.msg('You must be in-character to interact with objects.')
            return
        args = self.args
        if args[3:] == 'try':
            args = args[:4]
        here = char.location if char else None
        verb_list = self.verb_list()
        verb, noun = args.split(' ', 1) if ' ' in args else [args, '']
        obj = None
        if args:
            if verb not in verb_list:  # No valid verb used
                if char.ndb.power_pose:  # Detect invalid power pose.
                    here.msg_contents('%s = %s' % (char.ndb.power_pose, args))  # Display as normal pose.
                    char.nattributes.remove('power_pose')  # Flush power pose
                else:
                    account.msg(self.suggest_command())
                return
            else:
                good_targets = self.verb_list(verb)
                if noun:  # Look for an object that matches noun.
                    surroundings = ([here] + here.contents + char.contents) if here else ([char] + char.contents)
                    obj = char.search(noun, quiet=True, candidates=surroundings)
                    obj = obj[0] if obj else None
                if not obj:
                    obj = good_targets[0] if len(good_targets) == 1 else None
                account.msg('(%s/%s (%s))' % (verb, noun, obj))
                if obj and obj in good_targets:
                    self.trigger_response(char, verb, obj)
                else:
                    if good_targets:
                        if obj:
                            account.msg('You can only %s %s|n.' % (verb, self.style_object_list(good_targets, char)))
                        else:
                            account.msg('You can %s %s|n.' % (verb, self.style_object_list(good_targets, char)))
                    else:
                        account.msg('You can not %s %s|n.' % (verb, obj.get_display_name(account)))
        else:
            account.msg('|wVerbs to try|n: |g%s|n.' % '|w, |g'.join(verb_list))

    @staticmethod
    def trigger_response(char, verb, obj):
        """
        Triggers verb method (check for method on verb handler - check against forbidden list.)
        Triggers verb matched with alias, if initial verb is not a match.
        Triggers message (look for message) on default verbs that have no method on the verb handler.
        """
        VerbHandler(char, verb, obj)

    def verb_list(self, search_verb=None):
        """
        Scan location for objects that have verbs, and collect the verbs in a list or, if verb given,
        scan location for objects that have a specific verb, and collect the objects in a list.
        """
        collection = []
        char = self.character
        here = char.location
        surroundings = ([here] + here.contents + char.contents) if here else ([char] + char.contents)
        for obj in surroundings:
            verbs = obj.locks
            for verb in ("%s" % verbs).split(';'):
                element = verb.split(':')[0]
                name = element[2:] if element[:2] == 'v-' else element
                if not obj.access(char, element):  # search_verb on object is inaccessible.
                    continue
                if name == search_verb:
                    collection.append(obj)  # Collect objects that are accessible.
                elif search_verb is None:
                    collection.append(name)
        return list(set(collection))

    @staticmethod
    def style_object_list(objects, viewer):
        """Turn a list of objects into a stylized string for display."""
        collection = []
        for obj in objects:
            collection.append(obj.get_display_name(viewer))
        return ', '.join(collection)

    def suggest_command(self):
        """Create default "command not available" error message."""
        raw = self.raw_string.strip()  # The raw command line text, minus surrounding whitespace
        char = self.character
        message = "|wCommand |n'|y%s|n' |wis not available." % raw
        suggestions = string_suggestions(raw, self.cmdset.get_all_cmd_keys_and_aliases(char), cutoff=0.72, maxnum=3)
        if suggestions:
            if len(suggestions) == 1:
                message += ' Maybe you meant |n"|g%s|n" |w?' % suggestions[0]
            else:
                message += ' Maybe you meant %s' % '|w, '.join('|n"|g%s|n"' % each for each in suggestions[:-1])
                message += ' |wor |n"|g%s|n" |w?' % suggestions[-1:][0]
        else:
            message += ' Type |n"|ghelp|n"|w for help.'
        return message
