# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils import search, utils


class CmdZone(MuxCommand):
    """
    Add zone to object.
    Usage:
      zone
    Switches:
    /search  Search for rooms of a particular zone type.

    """
    key = 'zone'
    locks = 'cmd:all()'
    help_category = 'System'
    account_caller = True

    # myscript.tags.add('weather', category='climate')
    # mychair.tags.all(category='flags')  # returns a list of Tags
    # mychair.tags.remove('furniture')
    # mychari.tags.clear()

    def func(self):
        """ """
        char = self.character
        here = char.location
        account = self.account
        cmd = self.cmdstring
        switches = self.switches
        args = self.args.strip()
        zones = ['zone', 'area', 'region', 'realm']
        switches_list = [u'search']

        if not switches:
            zones_here = [here.tags.get(category='realm')]
            if here and zones_here[0]:
                zones_here.append(here.tags.get(category='region'))
                zones_here.append(here.tags.get(category='area'))
                zones_here.append(here.tags.get(category='zone'))
                account.msg('Zone here: |c%s' % "|n, |c".join(a for a in [x for x in zones_here if x is not None]))
            else:
                account.msg("No realm zone found here. You are not in any realm.")
                return
        elif not all(x in switches_list for x in switches):
            account.msg("Not a valid switch for %s. Use only these: |g/%s" % (cmd, "|n, |g/".join(switches_list)))
            return
        if 'search' in switches:
            if not args or args not in zones or self.lhs not in zones:
                account.msg("Searching requires providing a search string.  Try one of: zone, area, region, or realm.")
                return
            else:
                category = self.rhs or args
                zone = self.lhs if not self.rhs else args
                rooms = search.search_tag(zone, category=category)
                room_count = len(rooms)
                if room_count > 0:
                    match_string = ", ".join(r.get_display_name(account) for r in rooms)
                    string = "Found |w%i|n room%s with zone category '|g%s|n':\n %s" % \
                             (room_count, "s" if room_count > 1 else '', args, match_string)
                    account.msg(string)
                else:
                    account.msg("No %s zones found." % args)
