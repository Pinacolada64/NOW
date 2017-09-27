# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
# from django.conf import settings
from evennia import CmdSet
from evennia.comms.models import ChannelDB, Msg
from evennia.utils import create, utils, evtable, delay
# from evennia.utils.utils import make_iter, class_from_module
from past.builtins import cmp


class MailCmdSet(CmdSet):
    key = 'mailbox'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the mailbox object (item or room)."""
        self.add(CmdMail())


class CmdMail(MuxCommand):
    """
    Mail a private letter to another character or
    show your last <number> of letters (default is 5)
    Usage:
      mail[/switches] [<account>,<account>,... = <message>]
      mail <number>
    Options:
      last   shows your last sent correspondence.
      check  check for new messages since last read.
    """
    key = 'mail'
    locks = 'cmd:not pperm(mail_banned) and at_home()'
    help_category = 'Communication'
    account_caller = True

    def mail_check(self):
        char = self.character
        if char.ndb.new_mail:
            self.msg('You have new mail in your %s mailbox.' % char.location.get_display_name(self.character))
            return True
        else:
            return False

    def func(self):
        """Implement function using the Msg methods"""
        char = self.character
        sent_messages = Msg.objects.get_messages_by_sender(char, exclude_channel_messages=True)
        recd_messages = Msg.objects.get_messages_by_receiver(char)
        if 'last' in self.switches:
            self.mail_check()
            if sent_messages:
                recv = ', '.join('%s%s|n' % (obj.STYLE, obj.key) for obj in sent_messages[-1].receivers)
                self.msg("You last mailed |w%s|n: |w%s" % (recv, sent_messages[-1].message))
            else:
                self.msg("You haven't mailed anyone yet.")
            self.mail_check()
            return
        if 'check' in self.switches:
            if not self.mail_check():
                if not ('silent' in self.switches and 'quiet' in self.switches):
                    self.msg('Your %s mailbox has no new mail.' % char.location.get_display_name(self.character))
        if not self.args or not self.rhs:
            mail = sent_messages + recd_messages
            mail.sort(lambda x, y: cmp(x.db_date_created, y.db_date_created))
            number = 5
            if self.args:
                try:
                    number = int(self.args)
                except ValueError:
                    self.msg("Usage: mail [<character> = msg]")
                    return
            if len(mail) > number:
                mail_last = mail[-number:]
            else:
                mail_last = mail
            template = "|w%s|n |w%s|n to |w%s|n: %s"
            mail_last = "\n ".join(template %
                                   (utils.datetime_format(mail.date_created),
                                    ', '.join('%s' % obj.get_display_name(self.character) for obj in mail.senders),
                                    ', '.join(['%s' % obj.get_display_name(self.character) for obj in mail.receivers]),
                                    mail.message) for mail in mail_last)
            if mail_last:
                string = "Your latest letters:\n %s" % mail_last
            else:
                string = "You haven't mailed anyone yet."
            self.msg(string)
            char.nattributes.remove('new_mail')  # Removes the notice.
            return
        # Send mode
        if not self.lhs:
            if sent_messages:  # If no recipients provided,
                receivers = sent_messages[-1].receivers  # default to sending to the last character mailed.
            else:
                self.msg("Who do you want to mail?")
                return
        else:  # Build a list of comma-delimited recipients.
            receivers = self.lhslist
        rec_objs = []
        received = []
        r_strings = []
        for receiver in set(receivers):
            if isinstance(receiver, basestring):
                c_obj = char.search(receiver, global_search=True, exact=True)
            elif hasattr(receiver, 'location'):
                c_obj = receiver
            else:
                self.msg("Who do you want to mail?")
                return
            if c_obj:
                if not c_obj.access(char, 'mail'):
                    r_strings.append("You are not able to mail %s." % c_obj)
                    continue
                rec_objs.append(c_obj)
        if not rec_objs:
            self.msg("No one found to mail.")
            return
        message = self.rhs.strip()
        if message.startswith(':'):  # Format as pose if message begins with a :
            message = "%s%s|n %s" % (char.STYLE, char.key, message.strip(':'))
        create.create_message(char, message, receivers=rec_objs)

        def letter_delivery():
            # c_obj.msg('%s %s' % (header, message))
            c_obj.msg('|/A letter has arrived in %s%s|n mailbox for you.|/' % (c_obj.home.STYLE, c_obj.home.key))

        for c_obj in rec_objs:  # Notify character of mail delivery.
            received.append('%s%s|n' % (c_obj.STYLE, c_obj.key))
            if hasattr(c_obj, 'sessions') and not c_obj.sessions.count():
                r_strings.append("|r%s|n is currently asleep, and won't read the letter until later." % received[-1])
                c_obj.ndb.new_mail = True
            else:  # Tell the receiving characters about receiving a letter if they are online.
                utils.delay(20, callback=letter_delivery)
        if r_strings:
            self.msg("\n".join(r_strings))
        stamp_count = len(rec_objs)
        stamp_plural = 'a stamp' if stamp_count == 1 else '%i stamps' % stamp_count
        self.msg('Mail delivery costs %s.' % stamp_plural)
        char.location.msg_contents('|g%s|n places %s on an envelope and slips it into the %s%s|n mailbox.'
                                   % (char.key, stamp_plural, char.location.STYLE, char.location.key))
        self.msg("Your letter to %s will be delivered soon. You wrote: %s" % (', '.join(received), message))
        self.mail_check()
