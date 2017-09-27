# -*- coding: UTF-8 -*-
import time
from commands.command import MuxAccountCommand
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import ansi, utils, create, search, evtable


class CmdWho(MuxAccountCommand):
    """
    Shows who is currently online.
    Usage:
      who    - basic view
      where  - includes location
      what   - includes doing
      ws     - includes species
      wa     - same as 'where'
    """
    key = 'who'
    aliases = ['ws', 'where', 'wa', 'what', 'wot']
    locks = 'cmd:all()'

    def func(self):
        """Get all connected accounts by polling session."""
        you = self.account
        session_list = SESSIONS.get_sessions()
        cmd = self.cmdstring
        show_session_data = you.check_permstring('Immortals') and not you.attributes.has('_quell')
        account_count = (SESSIONS.account_count())
        table = evtable.EvTable(border='none', pad_width=0, border_width=0, maxwidth=79)
        if cmd == 'wa' or cmd == 'where':
            # Example output expected:
            # Occ, Location,  Avg Time, Top 3 Active, Directions
            # #3 	Park 		5m 		Rulan, Amber, Tria		Taxi, Park
            # Other possible sort methods: Alphabetical by name, by occupant count, by activity, by distance
            # Nick = Global Nick (no greater than five A/N or randomly created if not a Global Nick
            #
            # WA with name parameters to pull up more extensive information about the direction
            # Highest Occupants (since last reboot), Last Visited, Last Busy (3+) etc. (more ideas here)
            table.add_header('|wOcc', '|wLocation', '|wAvg Time', '|cTop 3 Active', '|gDirections')
            table.reformat_column(0, width=4, align='l')
            table.reformat_column(1, width=25, align='l')
            table.reformat_column(2, width=6, align='l')
            table.reformat_column(3, width=16, pad_right=1, align='l')
            table.reformat_column(4, width=20, align='l')
            locations = {}  # Create an empty dictionary to gather locations information.
            for session in session_list:  # Go through connected list and see who's where.
                if not session.logged_in:
                    continue
                character = session.get_puppet()
                if not character:
                    continue
                if character.location not in locations:
                    locations[character.location] = []
                locations[character.location].append(character)  # Build the list of who's in a location
            for place in locations:
                location = place.get_display_name(you) if place else '|222Nothingness|n'
                table.add_row(len(locations[place]), location, '?',
                              ', '.join(each.get_display_name(you) for each in locations[place]),
                              'Summon or walk')
        elif cmd == 'ws':
            my_character = self.caller.get_puppet(self.session)
            if not (my_character and my_character.location):
                self.msg("You can't see anyone here.")
                return
            table.add_header('|wCharacter', '|wOn for', '|wIdle')
            table.reformat_column(0, width=45, align='l')
            table.reformat_column(1, width=8, align='l')
            table.reformat_column(2, width=7, pad_right=1, align='r')
            for element in my_character.location.contents:
                if not element.has_account:
                    continue
                delta_cmd = time.time() - max([each.cmd_last_visible for each in element.sessions.all()])
                delta_con = time.time() - min([each.conn_time for each in element.sessions.all()])
                name = element.get_display_name(you)
                type = element.attributes.get('species', default='')
                table.add_row(name + ', ' + type if type else name,
                              utils.time_format(delta_con, 0), utils.time_format(delta_cmd, 1))
        elif cmd == 'what' or cmd == 'wot':
            table.add_header('|wCharacter  - Doing', '|wIdle')
            table.reformat_column(0, width=72, align='l')
            table.reformat_column(1, width=7, align='r')
            for session in session_list:
                if not session.logged_in or not session.get_puppet():
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                character = session.get_puppet()
                doing = character.get_display_name(you, pose=True)
                table.add_row(doing, utils.time_format(delta_cmd, 1))
        else:  # Default to displaying who
            if show_session_data:  # privileged info shown to Immortals and higher only when not quelled
                table.add_header('|wCharacter', '|wAccount', '|wQuell', '|wCmds', '|wProtocol', '|wAddress')
                table.reformat_column(0, align='l')
                table.reformat_column(1, align='r')
                table.reformat_column(2, width=7, align='r')
                table.reformat_column(3, width=6, pad_right=1, align='r')
                table.reformat_column(4, width=11, align='l')
                table.reformat_column(5, width=16, align='r')
                session_list = sorted(session_list, key=lambda o: o.account.key)
                for session in session_list:
                    if not session.logged_in:
                        continue
                    account = session.get_account()
                    puppet = session.get_puppet()
                    table.add_row(puppet.get_display_name(you) if puppet else 'None',
                                  account.get_display_name(you),
                                  '|gYes|n' if account.attributes.get('_quell') else '|rNo|n',
                                  session.cmd_total, session.protocol_key,
                                  isinstance(session.address, tuple) and session.address[0] or session.address)
            else:  # unprivileged info shown to everyone, including Immortals and higher when quelled
                table.add_header('|wCharacter', '|wOn for', '|wIdle')
                table.reformat_column(0, width=40, align='l')
                table.reformat_column(1, width=8, align='l')
                table.reformat_column(2, width=7, align='r')
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    if not character:
                        continue
                    table.add_row(character.get_display_name(you), utils.time_format(delta_conn, 0),
                                  utils.time_format(delta_cmd, 1))
        is_one = account_count == 1
        string = '%s' % 'A' if is_one else str(account_count)
        string += ' single ' if is_one else ' unique '
        plural = ' is' if is_one else 's are'
        string += 'account%s logged in.' % plural
        self.msg(table)
        self.msg(string)
