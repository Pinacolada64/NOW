# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import evtable
from evennia.utils import utils
import time


class CmdWhoinfo(MuxCommand):
    """Parent class for pre-login who and info commands."""
    locks = "cmd:all()"
    auto_help = True


class CmdWhoUs(CmdWhoinfo):
    key = 'who'
    aliases = ['w']

    def func(self):
        """returns the list of online characters"""
        count_accounts = (SESSIONS.account_count())
        self.caller.msg("[%s] Through the fog you see:" % self.key)
        session_list = SESSIONS.get_sessions()
        table = evtable.EvTable(border='none')
        table.add_row('Character', 'On for', 'Idle',  'Location')
        for session in session_list:
            if not session.logged_in:
                continue
            delta_cmd = time.time() - session.cmd_last_visible
            delta_conn = time.time() - session.conn_time
            puppet = session.get_puppet()
            location = puppet.location.key if puppet and puppet.location else 'Nothingness'
            table.add_row(puppet.key if puppet else 'None', utils.time_format(delta_conn, 0),
                          utils.time_format(delta_cmd, 1), location)
        table.reformat_column(0, width=25, align='l')
        table.reformat_column(1, width=12, align='l')
        table.reformat_column(2, width=7, align='l')
        table.reformat_column(3, width=25, align='l')
        is_one = count_accounts == 1
        string = '%s' % 'A' if is_one else str(count_accounts)
        string += ' single ' if is_one else ' unique '
        plural = ' is' if is_one else 's are'
        string += 'account%s logged in.' % plural
        self.caller.msg(table)
        self.caller.msg(string)
