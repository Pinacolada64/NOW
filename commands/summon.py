# -*- coding: UTF-8 -*-
import evennia
from evennia.utils.utils import delay
from commands.command import MuxCommand
from evennia.server.sessionhandler import SESSIONS


class CmdSummon(MuxCommand):
    """
    Open portal from object's location to yours, or location you specify.
    The portal forms 30 seconds later and is, under some circumstances,
    one-way only.
    Usage:
      summon/switch <object>[ = <location>]
    Options:
    /quiet     Portal arrives quietly to others in room.
    /only      Only the summoned object can use the portal exit.
    /in        Portal is one-way; into summon location.
    /out       Portal is one-way; summon location outward
    /vanish    if set, the portal leads to Nothingness.
               When this option is used, <location> is ignored.
    Examples:
      summon Tria
      summon/quiet Rulan=poof
      summon/only LazyLion
      summon/vanish me
    """
    key = 'summon'
    aliases = ['msummon', 'meet', 'join', 'mjoin']
    options = ('quiet', 'only', 'in', 'out', 'vanish')
    locks = 'cmd:perm(summon) or perm(Accounts)'
    help_category = 'Travel'

    def func(self):
        """Performs the summon, accounting for in-world conditions."""

        char = self.character
        loc = char.location
        account = self.account
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        # opt = self.switches  # TODO - add code to make the switches work.

        if char and char.ndb.currently_moving:
            account.msg("You can not summon while moving. (|rstop|n, then try again.)")
            return
        if not args:
            char.msg("Could not find target to summon. Usage: summon <character or NPC>")
            return
        session_list = SESSIONS.get_sessions()
        target = []
        for session in session_list:
            if not (session.logged_in and session.get_puppet()):
                continue
            puppet = session.get_puppet()
            if lhs.lower() in puppet.get_display_name(char, plain=True).lower():
                target.append(puppet)
        if len(target) < 1:
            char.msg("Error: character not found.")
            return
        if len(target) > 1:  # Too many partial matches, try exact matching.
            char.msg("Error: character not found.")
            return
        else:
            target[0].msg("You are being summoned to %s " % loc.get_display_name(target[0]) +
                          "by %s" % char.get_display_name(target[0]) +
                          ". A portal should appear soon that will take you to " +
                          "%s." % char.get_display_name(target[0]))
            char.msg("You begin to summon a portal between %s" % target[0].get_display_name(char) +
                     " and your location.")
        # Check the pool for objects to use.  Filter a list of objects tagged "pool" by those located in None.
        obj_pool = [each for each in evennia.search_tag('pool', category='portal') if not each.location]
        print('Object pool total: %i' % len(obj_pool))
        if len(obj_pool) < 2:
            char.msg('Portals are currently out of stock or in use elsewhere.')
            return
        portal_enter, portal_exit = obj_pool[-2:]

        def open_portal():
            """Move inflatable portals into place."""
            portal_enter.move_to(target[0].location)
            portal_exit.move_to(loc)

        delay(10, callback=open_portal)  # 10 seconds later, the portal (exit pair) appears.

        def close_portal():
            """Remove and store inflatable portals in Nothingness."""
            for each in portal_enter.contents:
                each.move_to(target[0].location)
            for each in portal_exit.contents:
                each.move_to(loc)
            portal_enter.location.msg_contents("|r%s|n vanishes into |222Nothingness|n." % portal_enter)
            portal_exit.location.msg_contents("|r%s|n vanishes into |222Nothingness|n." % portal_exit)
            portal_enter.move_to(None, to_none=True)
            portal_exit.move_to(None, to_none=True)

        delay(180, callback=close_portal)  # Wait, then move portal objects to the portal pool in Nothingness
