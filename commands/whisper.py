# -*- coding: UTF-8 -*-
from commands.command import MuxCommand


class CmdWhisper(MuxCommand):
    """
    Whisper to one or more nearby targets.
    Syntax:
      whisper [target name, or names =[=] ][message]
    Usage:
       whisper A, B, C = text of message
    1) whisper text of message
    2) whisper A, B, C =
    3) whisper ==
    4) whisper =
    5) whisper
    *1 Omitting the target(s) and equal sign will whisper
       to the last whispered if message text is given.
    *2 Supplying target(s), an equal sign, but no message
      will set the target(s) for future whispers.
    *3 Supplying two equal signs without target(s) or
       message will set your next whisper to reply to
       the last whispered group.
    *4 Supplying only an equal sign without target(s) or
       message text will set your next whisper to the one
       who last whispered to you.
    *5 If no parameters are given, whisper will display
       the names of those whom you last whispered.
    * In some environments, message degradation may occur,
      similar to a mumble with only partial readability.
    Planned Options:
    /o or /ooc  - Out-of-character whispering.
    /t or /tel  - Telepathic whispering, if you and your
                  target(s) have enough combined telepathy.
    """
    key = 'whisper'
    aliases = ['wh', '""', "''"]
    options = ('version',)
    locks = 'cmd:all()'

    def func(self):
        """Run the whisper command"""
        char = self.character
        here = char.location
        who = self.lhs.strip()
        opt = self.switches
        message = self.args.strip() if not self.rhs else self.rhs.strip()  # If no equals sign, use args for message
        last = self.character.ndb.last_whispered or []
        all_present = [each for each in self.character.location.contents] +\
                      [each for each in self.character.contents] + [here]
        result, new_last = self.whisper(char, who, message, last, all_present)
        for each in new_last:
            if each:
                each.private(char, 'whisper', message)
        char.msg(result)
        char.ndb.last_whispered = new_last
        if 'version' in opt:
            # char.msg('Whisper version 14, Tuesday 31 Jan 2017')
            char.msg('Whisper version https://repl.it/FDZS/23')

    @staticmethod
    def whisper(me, who, message, last, all_present):
        """
        Whisper to one or more nearby targets.
        Syntax:
               whisper A, B, C = text of whisper
               <command> <who> =[=] <message> (last, all_present)
          where:
          me is the object that is whispering.
          who is a comma-delimited string of text from the left-hand
               side of the = sign, of who should receive this whisper.
               If left empty, the last whisperers list is used.
          message is the text from the right-hand side of the = sign,
               the message to be whispered.
          last is a comma-delimited string (like who) of who last
               received a whisper from me, used when who is empty.
          all_present is a list of which objects are near you, in range.
        """

        # is_present, is_awake, is_unlocked, is_available.

        def is_available(obj):  # Test if object is present in room
            return True

        def is_unlocked(obj):  # Test if object is present in room
            return True

        def is_awake(obj):  # To be altered after testing phase.
            return True  # Tests if character is awake.

        def match_object(each, all_present):
            return me.search(each, candidates=all_present)

        # Begin whisper code for Whisper command here.
        who_present, who_success, failed_whisper = [], [], []
        whisper_list = list(set([each_who.strip() for each_who in who.split(',')])) if who else None
        object_list = [match_object(each, all_present) for each in whisper_list] if who else last
        whisper_success = False
        result_message = ''

        for obj in object_list:
            if not obj:
                continue  # Skip objects not found.
            if is_available(obj):
                if is_unlocked(obj):
                    if is_awake(obj):
                        who_success.append(obj)
                        whisper_success = True
                    else:
                        who_success.append(obj)
                        whisper_success = True
                        failed_whisper.append(obj.name + " (is asleep)")
                else:
                    failed_whisper.append(obj.name + " (is uninterested)")
            else:
                failed_whisper.append(obj.name + " (is not available/unreachable)")

        if whisper_success:
            result_message = 'You whisper "' + message + '" to ' + ', '.join([obj.name for obj in who_success]) + '.'
        if failed_whisper:
            plural, verb = ['', 'was'] if (len(failed_whisper) == 1) else ['s', 'were']
            result_message += '\nThe name%s provided %s unable to be whispered to.' % (plural, verb)
            result_message += '\n  Your whisper was not heard by ' + ', '.join(failed_whisper) + '.'
        return result_message, who_success  # String displayed to self showing whisper results.

        # End whisper code for Whisper command here.
