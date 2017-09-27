# -*- coding: UTF-8 -*-
from commands.command import MuxAccountCommand
from django.conf import settings
from evennia.comms.models import ChannelDB, Msg
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia.utils import create, utils, evtable
from evennia.utils.utils import make_iter

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH


def find_channel(caller, channel_name, silent=False, noaliases=False):
    """
    Helper function for searching for a single channel with
    some error handling.
    """
    channels = ChannelDB.objects.channel_search(channel_name)
    if not channels:
        if not noaliases:
            channels = [chan for chan in ChannelDB.objects.get_all_channels()
                        if channel_name in chan.aliases.all()]
        if channels:
            return channels[0]
        if not silent:
            caller.msg("Channel '%s' not found." % channel_name)
        return None
    elif len(channels) > 1:
        matches = ", ".join(["%s(%s)" % (chan.key, chan.id) for chan in channels])
        if not silent:
            caller.msg("Multiple channels match (be more specific): \n%s" % matches)
        return None
    return channels[0]


class CmdChannels(MuxAccountCommand):
    """
    Channels provide communication with a group of other accounts based on a
    particular interest or subject.  Channels are free of being at a particular
    location. Channels use their alias as the command to post to then.
    Usage:
      chan
    Options:
    /list to display all available channels.
    /join (on) or /part (off) to join or depart channels.

    Batch options:
    /all      to affect all channels at once:
    /all on   to join all available channels.
    /all off  to part all channels currently on.

       If you control a channel:
    /all who <channel> to list who listens to all channels.
    /who  <channel>    who listens to a specific channel.
    /lock <channel>    to set a lock on a channel.
    /desc <channel> = <description>  to describe a channel.
    /emit <channel> = <message>   to emit to channel.
    /name <channel> = <message>   sends to channel as if you're joined.
    /remove <channel> = <account> [:reason]  to remove an account from the channel.
    /quiet <channel> = <account>[:reason]    to remove the user quietly.
    """
    key = 'channel'
    aliases = ['chan', 'channels']
    help_category = 'Communication'
    locks = 'cmd: not pperm(channel_banned)'

    def func(self):
        """Implement function"""

        caller = self.caller
        args = self.args

        # Of all channels, list only the ones with access to listen
        channels = [chan for chan in ChannelDB.objects.get_all_channels()
                    if chan.access(caller, 'listen')]
        if not channels:
            self.msg("No channels available.")
            return

        subs = ChannelDB.objects.get_subscriptions(caller)  # All channels already joined

        if 'list' in self.switches:
            # full listing (of channels caller is able to listen to) ✔ or ✘
            com_table = evtable.EvTable("|wchannel|n", "|wdescription|n", "|wown sub send|n",
                                        "|wmy aliases|n", maxwidth=_DEFAULT_WIDTH)
            for chan in channels:
                c_lower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                nicks = nicks or []
                control = '|gYes|n ' if chan.access(caller, 'control') else '|rNo|n  '
                send = '|gYes|n ' if chan.access(caller, 'send') else '|rNo|n  '
                sub = chan in subs and '|gYes|n ' or '|rNo|n  '
                com_table.add_row(*["%s%s" % (chan.key, chan.aliases.all() and
                                    "(%s)" % ",".join(chan.aliases.all()) or ''),
                                    chan.db.desc,
                                    control + sub + send,
                                    "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                                    if nick.strvalue.lower() == c_lower)])
            caller.msg("|/|wAvailable channels|n:|/" +
                       "%s|/(Use |w/list|n, |w/join|n and |w/part|n to manage received channels.)" % com_table)
        elif 'join' in self.switches or 'on' in self.switches:
            if not args:
                self.msg("Usage: %s/join [alias =] channel name." % self.cmdstring)
                return

            if self.rhs:  # rhs holds the channel name
                channel_name = self.rhs
                alias = self.lhs
            else:
                channel_name = args
                alias = None

            channel = find_channel(caller, channel_name)
            if not channel:
                # custom search method handles errors.
                return

            # check permissions
            if not channel.access(caller, 'listen'):
                self.msg("%s: You are not able to receive this channel." % channel.key)
                return

            string = ''
            if not channel.has_connection(caller):
                # we want to connect as well.
                if not channel.connect(caller):
                    # if this would have returned True, the account is connected
                    self.msg("%s: You are not able to join this channel." % channel.key)
                    return
                else:
                    string += "You now listen to channel %s. " % channel.key
            else:
                string += "You already receive channel %s." % channel.key

            if alias:
                # create a nick and add it to the caller.
                caller.nicks.add(alias, channel.key, category="channel")
                string += " You can now refer to the channel %s with the alias '%s'."
                self.msg(string % (channel.key, alias))
            else:
                string += " No alias added."
            self.msg(string)
        elif 'part' in self.switches or 'off' in self.switches:
            if not args:
                self.msg("Usage: %s/part <alias or channel>" % self.cmdstring)
                return
            o_string = self.args.lower()

            channel = find_channel(caller, o_string, silent=True, noaliases=True)
            if channel:  # Given a channel name to part.
                if not channel.has_connection(caller):
                    self.msg("You are not listening to that channel.")
                    return
                ch_key = channel.key.lower()
                # find all nicks linked to this channel and delete them
                for nick in [nick for nick in make_iter(caller.nicks.get(category="channel", return_obj=True))
                             if nick and nick.strvalue.lower() == ch_key]:
                    nick.delete()
                disconnect = channel.disconnect(caller)
                if disconnect:
                    self.msg("You stop receiving channel '%s'. Any aliases were removed." % channel.key)
                return
            else:
                # we are removing a channel nick
                chan_name = caller.nicks.get(key=o_string, category="channel")
                channel = find_channel(caller, chan_name, silent=True)
                if not channel:
                    self.msg("No channel with alias '%s' was found." % o_string)
                else:
                    if caller.nicks.get(o_string, category="channel"):
                        caller.nicks.remove(o_string, category="channel")
                        self.msg("Your alias '%s' for channel %s was cleared." % (o_string, channel.key))
                    else:
                        self.msg("You had no such alias defined for this channel.")
        elif 'who' in self.switches:
            if not self.args:
                self.msg("Usage: %s/who <channel name or alias>" % self.cmdstring)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            if not channel.access(self.caller, "control"):
                string = "You do not control this channel."
                self.msg(string)
                return
            string = "\n|CChannel receivers|n"
            string += " of |w%s:|n " % channel.key
            subs = channel.db_subscriptions.all()
            if subs:
                string += ", ".join([account.key for account in subs])
            else:
                string += "<None>"
            self.msg(string.strip())
        elif 'lock' in self.switches:
            if not self.args:
                self.msg("Usage: %s/lock <alias or channel>" % self.cmdstring)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            if not self.rhs:  # no =, so just view the current locks
                string = "Current locks on %s:" % channel.key
                string = "%s %s" % (string, channel.locks)
                self.msg(string)
                return
            # we want to add/change a lock.
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            channel.locks.add(self.rhs)  # Try to add the lock
            string = "Lock(s) applied on %s:" % channel.key
            string = "%s %s" % (string, channel.locks)
            self.msg(string)
        elif 'emit' in self.switches or 'name' in self.switches:
            if not self.args or not self.rhs:
                switch = 'emit' if 'emit' in self.switches else 'name'
                string = "Usage: %s/%s <channel> = <message>" % (self.cmdstring, switch)
                self.msg(string)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            message = self.rhs
            if 'name' in self.switches:
                message = "%s: %s" % (self.caller.key, message)
            channel.msg(message)
            if 'quiet' not in self.switches:
                string = "Sent to channel %s: %s" % (channel.key, message)
                self.msg(string)
        elif 'desc' in self.switches:
            if not self.rhs:
                self.msg("Usage: %s/desc <channel> = <description>" % self.cmdstring)
                return
            channel = find_channel(caller, self.lhs)
            if not channel:
                self.msg("Channel '%s' not found." % self.lhs)
                return
            if not channel.access(caller, 'control'):  # check permissions
                self.msg("You cannot describe this channel.")
                return
            channel.db.desc = self.rhs  # set the description
            channel.save()
            self.msg("Description of channel '%s' set to '%s'." % (channel.key, self.rhs))
        elif 'all' in self.switches:
            if not args:
                caller.execute_cmd("@channels")
                self.msg("Usage: %s/all on || off || who || clear" % self.cmdstring)
                return
            if args == "on":  # get names of all channels available to listen to and activate them all
                channels = [chan for chan in ChannelDB.objects.get_all_channels()
                            if chan.access(caller, 'listen')]
                for channel in channels:
                    caller.execute_cmd("@command/join %s" % channel.key)
            elif args == 'off':
                # get names all subscribed channels and disconnect from them all
                channels = ChannelDB.objects.get_subscriptions(caller)
                for channel in channels:
                    caller.execute_cmd("@command/part %s" % channel.key)
            elif args == 'who':
                # run a who, listing the subscribers on visible channels.
                string = "\n|CChannel subscriptions|n"
                channels = [chan for chan in ChannelDB.objects.get_all_channels()
                            if chan.access(caller, 'listen')]
                if not channels:
                    string += "No channels."
                for channel in channels:
                    if not channel.access(self.caller, "control"):
                        continue
                    string += "\n|w%s:|n\n" % channel.key
                    subs = channel.db_subscriptions.all()
                    if subs:
                        string += "  " + ", ".join([account.key for account in subs])
                    else:
                        string += "  <None>"
                self.msg(string.strip())
            else:
                # wrong input
                self.msg("Usage: %s/all on | off | who | clear" % self.cmdstring)
        elif 'remove' in self.switches or 'quiet' in self.switches:
            if not self.args or not self.rhs:
                switch = 'remove' if 'remove' in self.switches else 'quiet'
                string = "Usage: %s/%s <channel> = <account> [:reason]" % (self.cmdstring, switch)
                self.msg(string)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            reason = ''
            if ":" in self.rhs:
                account_name, reason = self.rhs.rsplit(":", 1)
                search_string = account_name.lstrip('*')
            else:
                search_string = self.rhs.lstrip('*')
            account = self.caller.search(search_string, account=True)
            if not account:
                return
            if reason:
                reason = " (reason: %s)" % reason
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            if account not in channel.db_subscriptions.all():
                string = "Account %s is not connected to channel %s." % (account.key, channel.key)
                self.msg(string)
                return
            if 'quiet' not in self.switches:
                string = "%s boots %s from channel.%s" % (self.caller, account.key, reason)
                channel.msg(string)
            # find all account's nicks linked to this channel and delete them
            for nick in [nick for nick in
                         account.character.nicks.get(category="channel") or []
                         if nick.db_real.lower() == channel.key]:
                nick.delete()
            channel.disconnect(account)  # disconnect account
            CHANNELHANDLER.update()
        else:  # just display the subscribed channels with no extra info
            com_table = evtable.EvTable("|wchannel|n", "|wmy aliases|n",
                                        "|wdescription|n", align="l", maxwidth=_DEFAULT_WIDTH)
            for chan in subs:
                c_lower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                com_table.add_row(*["%s%s" % (chan.key, chan.aliases.all() and
                                    "(%s)" % ",".join(chan.aliases.all()) or ""),
                                    "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                                    if nick and nick.strvalue.lower() == c_lower),
                                    chan.db.desc])
            caller.msg("\n|wChannel subscriptions|n (use |w@chan/list|n to list all, " +
                       "|w/join|n |w/part|n to join or part):|n\n%s" % com_table)
