# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils import search
from evennia.utils import create
from django.conf import settings
from django.db.models import Q
from evennia.objects.models import ObjectDB
from evennia.utils.utils import inherits_from, class_from_module


class CmdExit(MuxCommand):
    """
    Simple destinations are stored on the room in its 'exits' attribute in a dictionary.
    All simple exits on the room use the same attribute, compared to object-based exits,
    which create a new database object.  Simple exits use much less database space.
    Actual exit objects superceed simple exits in every way.
    Usage:
    |w<|ydirection|w>[|glist of switches|w] [|ydestination|w]|n
    Options:
    |g/add|n [name starts with or alias]  adds simple exit to destination in the given direction.
    |g/del|n  removes simple exit in given direction.
    |g/tun|n <name>   adds simple exit from destination in opposite direction.
    |g/both|n <name>  adds simple exit to destination and back in opposite direction.
    |g/none|n <name>  removes simple exit to destination and back in opposite direction.
    |g/new|n [name;alias;...]  creates a new room of given name as destination.
    |g/go|n  after any above operations, move to destination.
    |g/show|n  shows room exit information and back exit from <direction>.

    Options combine in some combinations e.g. west/none/go would remove the exits
    into and out of the room in the given direction, then take you to the destination room.

    This command never deletes rooms, but can create them in a simple fashion when needed.
    """
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'
    help_category = 'Travel'
    auto_help = True
    account_caller = True

    def func(self):
        """Command for all simple exit directions."""
        you = self.character
        loc = you.location
        account = self.account
        cmd = self.cmdstring
        switches = self.switches
        args = self.args.strip()
        direction = self.aliases[0]
        dest = None  # Hopeful destination for exits and moving to.
        switches = self.switches
        switches_list = [u'add', u'del', u'tun', u'both', u'none', u'new', u'go', u'show']

        if switches and not all(x in switches_list for x in switches):
            account.msg("You used an unknown switch for |530%s|n. Use only these: |g/%s" %
                       (self.key, "|n, |g/".join(switches_list)))
            return

        def new_room(room_name):
            """
            print("-----")
            print("New Room creation details.")
            print("Name: %s" % room['name'])
            print("Alises: %s" % room['aliases'])
            print("Type: %s" % typeclass)
            print("Lock: %s" % lockstring)
            print("=====")
            """
            if not account.check_permstring('Builders'):
                you.msg("You must have |wBuilders|n or higher access to create a new room.")
                return None

            name, aliases = '', []
            if ';' in room_name:  # Parse aliases out of room_name.
                name, aliases = room_name.strip().split(';', 1)
                aliases = aliases.split(';')
            else:  # No aliases provided; aliases remain empty.
                name = room_name.strip()

            typeclass = settings.BASE_ROOM_TYPECLASS
            room = {'name': name, 'aliases': aliases}
            lockstring = "control:pid({0}) or perm(Immortals); delete:pid({0})" \
                         " or perm(Wizards); edit:pid({0}) or perm(Wizards); get:false()"\
                .format(account.id)
            r = create.create_object(typeclass, room['name'], aliases=room['aliases'], report_to=you)
            r.locks.add(lockstring)
            alias_string = room['aliases']
            if r.aliases.all():
                alias_string = " |w(|c%s|w)|n" % "|n, |c".join(r.aliases.all())
            account.msg("|gCreated room %s%s of type |m%s." % (r.get_display_name(account), alias_string, typeclass))
            return r or None

        def find_by_name(search):
            search = search.strip().split(';', 1)[0]
            keyquery = Q(db_key__istartswith=search)
            aliasquery = Q(db_tags__db_key__istartswith=search,
                           db_tags__db_tagtype__iexact='alias')

            results = ObjectDB.objects.filter(keyquery | aliasquery).distinct()
            nresults = results.count()

            if nresults:  # convert multiple results to typeclasses.
                results = [result for result in results]
                room_typeclass = settings.BASE_ROOM_TYPECLASS  # Narrow results to only room types.
                results = [obj for obj in results if inherits_from(obj, room_typeclass)]
            return results

        def add(you_add, loc_add, ways_add):
            """"Command for adding an exit - checks location and permissions."""
            results = find_by_name(self.args)
            if not results:
                account.msg('Destination "|r%s|n" was not valid.' % args)
                result = None
            else:
                result = results[0]  # Arbitrarily select the first result of usually only one.
            ways_add[direction] = result
            you_add.msg("|ySearch found|n (%s)" % result.get_display_name(you) if result else None)
            if not result:
                account.msg('Destination "|r%s|n" was not valid.' % args)
                return None
            if ways_add[direction]:
                if loc_add.access(you_add, 'edit'):
                    if ways_add[direction].access(you_add, 'control'):
                        loc_add.db.exits = ways_add
                        you_add.msg("|gAdded|n exit |lc%s|lt|530%s|n|le from %s to %s." %
                                    (self.key, self.key, loc_add.get_display_name(account),
                                     ways_add[direction].get_display_name(account)))
                    else:
                        you_add.msg("You do not control the destination, so can not connect an exit to it.")
                else:
                    you_add.msg("You have no permission to edit here.")
                return ways_add[direction]
            account.msg("You typed command (|y%s|n), switches (|%s|n), with no valid destination." %
                       (cmd, switches))
            account.msg('Destination "|r%s|n" was not valid.' % args)
            return None

        def back_dir(x):
            return {'n': 's', 's': 'n', 'e': 'w', 'w': 'e',
                    'nw': 'se', 'se': 'nw', 'ne': 'sw',
                    'sw': 'ne', 'u': 'd', 'd': 'u'}[x]

        def long_dir(x):
            return {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'nw': 'northwest', 'se': 'southeast',
                    'ne': 'northeast', 'sw': 'southwest', 'u': 'up', 'd': 'down'}[x]

        def tun(you_tun, loc_tun, dest_tun, dir_tun):
            """Command for tunneling an exit back - checks existing exits, location and permissions."""
            tun_ways = dest.db.exits or {}
            tun_way = tun_ways.get(back_dir(dir_tun))
            if tun_way:  # Is the direction in the room's exit dictionary?
                return None
            else:
                tun_ways[back_dir(dir_tun)] = loc_tun
                if dest_tun.access(you_tun, 'control'):
                    dest_tun.db.exits = tun_ways
                    you_tun.msg("|gAdded|n exit |530%s|n back from %s to %s." %
                                (long_dir(back_dir(dir_tun)), dest_tun.get_display_name(account),
                                 loc_tun.get_display_name(account)))
                else:
                    you_tun.msg("You do not control the destination, so can not connect an exit to it.")

        if switches:  # Provide messages giving feedback for Tria
            switch_list = '/' + '/'.join(switches)
            if args:
                account.msg("Showing direction, switches, destination: |y%s|g%s |y%s" %
                           (cmd, switch_list, args))
            else:
                account.msg("Showing direction and switches: |y%s|g%s|n, but no destination was given." %
                           (cmd, switch_list))
                if 'add' in switches or 'new' in switches or 'both' in switches:
                    account.msg("Without a destination, |g/add|n or |g/new|n can not be done.")
        else:
            if args:
                account.msg("Showing direction and destination: |y%s %s|n (No switches were provided - nothing to do.)"
                           % (cmd, args))
        if 'new' in switches and not args:
            you.msg("|g%s|r/new|n requires a destination room to be given, e.g. |g%s/new |yWilderness" % (cmd, cmd))
            return
        if 'add' in switches or 'both' in switches:
                if not args:
                    you.msg("|g%s|r/add|n requires a destination room to be given, e.g. |g%s/add |yWilderness" %
                            (cmd, cmd))
                    return  # No further action, not even check for /go.
                if 'del' in switches or 'none' in switches:  # Can't do both!
                    you.msg("|rThose switches are mutually exclusive; do not do both!")
                    return  # No further action, not even check for /go.
        if you.location.db.exits:  # Does an 'exits' attribute exist (and not None or False)?
            ways = loc.db.exits
            way = ways.get(direction)
            if way:  # Direction in the room's exit dictionary should know room.
                dest = way
                if 'del' in switches or 'none' in switches:
                    dest = way
                    tunnel_way = back_dir(direction)
                    tunnel_ways = dest.db.exits
                    if loc.access(you, 'edit'):
                        del(ways[direction])
                        loc.db.exits = ways
                        you.msg("|rRemoved|n exit |530%s|n from %s." % (self.key, loc.get_display_name(account)))
                    if ('tun' in switches or 'none' in switches) and tunnel_ways:
                        if dest.access(you, 'edit'):
                            del(tunnel_ways[tunnel_way])
                            dest.db.exits = tunnel_ways
                            you.msg("|rRemoved|n exit |530%s|n from %s." %
                                    (long_dir(tunnel_way), dest.get_display_name(account)))
                        else:
                            you.msg("You have no permission to edit here.")
                elif 'add' in switches or 'both' in switches:
                    if loc.access(you, 'edit'):
                        you.msg("Exit |530%s|n to %s leading to %s already exists here." %
                                (self.key, loc.get_display_name(account), dest.get_display_name(account)))
                    else:
                        you.msg("You have no permission to edit here.")
                if ('tun' in switches or 'both' in switches) and not ('del' in switches or 'none' in switches):
                    tun(you, loc, dest, direction)  # Add is done, now see if tun can be done.
                if 'new' in switches:
                    you.msg("Can't make a new room, already going to %s." % dest)
                if 'go' in switches or not switches:
                    if 'show' in switches:
                        you.msg("Ignoring |g/show|n switch; you must use it separately.")
                    you.ndb.moving_to = long_dir(direction)
                    you.ndb.moving_from = long_dir(back_dir(direction))
                    you.ndb.exit_used = direction
                    you.move_to(dest)
            else:  # No direction in the room's exit dictionary goes that way. Or direction goes to None.
                if 'new' in switches:
                    dest = new_room(self.args)
                if 'add' in switches or 'both' in switches:
                    add(you, loc, ways)
                elif 'del' in switches or 'none' in switches:
                    if direction in ways:
                        del(ways[direction])
                        you.msg("Exit |530%s|n was not valid. (|rremoved|n)" % self.key)
                    else:
                        you.msg("Exit |530%s|n does not exist here." % self.key)
                if 'tun' in switches or 'both' in switches:
                    dest = ways.get(direction)
                    if dest:
                        tun(you, loc, dest, direction)  # Add is done, now see if tun can be done.
                    else:
                        if self.args:
                            you.msg("|ySearching|n for \"%s\" to the %s." % (self.args, self.key))
                            dest = find_by_name(self.args)
                            if dest:
                                dest = dest[0]
                                you.msg("|gFound|n \"%s\" to the %s." % (dest, self.key))
                                tun(you, loc, dest, direction)  # Add not done, but see if tun can be done.
                            else:
                                you.msg(
                                    "|rDestination room not found|n \"{0:s}\" to the {1:s} when searching by: {2:s}."
                                    .format(dest, self.key, self.args))
                        else:
                            you.msg("|yYou must supply a name or alias of the target room.|n")
                if 'go' in switches:
                    if 'show' in switches:
                        you.msg("Ignoring |g/show|n switch; you must use it separately.")
                    if 'add' in switches or 'both' in switches:
                        you.ndb.moving_to = long_dir(direction)
                        you.ndb.moving_from = long_dir(back_dir(direction))
                        you.ndb.exit_used = direction
                        you.move_to(ways[direction])
                    else:
                        if ('tun' in switches or 'both' in switches) and dest:
                            if 'show' in switches:
                                you.msg("Ignoring |g/show|n switch; you must use it separately.")
                            you.ndb.moving_to = long_dir(direction)
                            you.ndb.moving_from = long_dir(back_dir(direction))
                            you.ndb.exit_used = direction
                            you.move_to(dest)
                if not switches:
                    if direction in ways:
                        del(ways[direction])
                        you.msg("Exit |530%s|n was not valid. (|rremoved|n)" % self.key)
                    else:
                        you.msg("You cannot travel %s." % self.key)
        else:  # No simple exits from this location.
            ways = {}
            way = None
            dest = way
            if 'new' in switches:
                dest = new_room(self.args)
            if 'add' in switches or 'both' in switches:
                dest = add(you, loc, ways)
            elif 'del' in switches or 'none' in switches:
                if 'tun' in switches or 'both' in switches:
                    # TODO: If 'tun' option is also used -
                    # there is no easy way to find it to delete it.
                    pass
                else:
                    you.msg("No simple exit |530%s|n to delete." % self.key)
            if ('tun' in switches or 'both' in switches) and ('del' not in switches and 'none' not in switches):
                if 'add' in switches or 'both' in switches:
                    dest = ways[direction]
                    tun(you, loc, dest, direction)  # Add is done, now see if tun can be done.
                else:
                    # TODO: Test - does this only work with 'add' option?
                    # It requires a destination, if not.
                    pass
            if 'go' in switches and way:
                if 'show' in switches:
                    you.msg("No simple exits to |g/show|n in this room.")
                you.ndb.moving_to = long_dir(direction)
                you.ndb.moving_from = long_dir(back_dir(direction))
                you.ndb.exit_used = direction
                you.move_to(dest)
            if not switches:
                you.msg("You cannot travel %s." % self.key)
        if 'show' in switches and 'go' not in switches:
            if not account.check_permstring('Helpstaff'):
                you.msg("You must have |gHelpstaff|n or higher access to use this.")
                return None
            if you.location.attributes.has('exits'):  # Does an 'exits' attribute exist?
                ways = loc.db.exits
                if direction in ways:
                    dest = ways[direction] if ways else None
                you.msg("|wSimple exits report: %s exist in %s: %s" %
                        (len(ways), you.location.get_display_name(you), ways))
                tunnel_ways = None
                if dest:
                    tunnel_ways = dest.db.exits
                if tunnel_ways:
                    you.msg("|wSimple exit report|n: exists in %s going |530%s|n back to %s." %
                            (dest.get_display_name(you), long_dir(back_dir(direction)),
                             you.location.get_display_name(you)))
            else:
                you.msg("No simple exits exist in %s." % you.location.get_display_name(you))


class CmdExitNorth(CmdExit):
    __doc__ = CmdExit.__doc__
    key = "north"
    aliases = ['n']


class CmdExitNortheast(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'northeast'
    aliases = ['ne']


class CmdExitNorthwest(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'northwest'
    aliases = ['nw']


class CmdExitEast(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'east'
    aliases = ['e']


class CmdExitSouth(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'south'
    aliases = ['s']


class CmdExitSoutheast(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'southeast'
    aliases = ['se']


class CmdExitSouthwest(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'southwest'
    aliases = ['sw']


class CmdExitWest(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'west'
    aliases = ['w']


class CmdExitUp(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'up'
    aliases = ['u']


class CmdExitDown(CmdExit):
    __doc__ = CmdExit.__doc__
    key = 'down'
    aliases = ['d']
