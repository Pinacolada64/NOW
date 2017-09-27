# -*- coding: UTF-8 -*-
"""
Rooms are simple containers that need no location of their own.
"""
import time  # Check time since last activity
import random  # Random weather events
from math import sqrt  # Distance formula for coordinate
from evennia.server.sessionhandler import SESSIONS  # Checking sessions for active accounts in room
from typeclasses.tangibles import Tangible
from evennia.utils.utils import lazy_property
from traits import TraitHandler
from evennia import TICKER_HANDLER  # TICKERS for weather events
from evennia.comms.models import ChannelDB, Msg  # Sending active/inactive status to public channel
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia import CmdSet  # For the class Grid
from evennia import default_cmds  # For the class Grid's commands


class Room(Tangible):
    """
    Rooms' location is usually None (which is default), but represent
    geographic locations with coordinates (x, y, and z) that
    are stored as tags, allowing for an efficient and quick search in the
    database, and simplify the task when retrieving a room at a given
    position, or looking for rooms around a given position.
    """
    STYLE = '|y'

    def return_appearance(self, viewer):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not (viewer and viewer.has_account):
            return ''
        # get and identify all objects visible to the viewer, excluding the viewer.
        visible = (con for con in self.contents if con != viewer and con.access(viewer, 'view'))
        exits, ways = [], []

        way_dir = {'ne': 'northeast', 'n': 'north', 'nw': 'northwest', 'e': 'east',
                   'se': 'southeast', 's': 'south', 'sw': 'southwest', 'w': 'west', 'u': 'up', 'd': 'down'}

        default_exits = [u'north', u'south', u'east', u'west', u'northeast', u'northwest', u'southeast', u'southwest',
                         u'up', u'down', u'in', u'out']

        exits_simple, exits_complex = [], []

        def sort_exits(x, y):
            """sort supplied list of exit strings, based on default_exits, returns sorted list."""
            matches = []  # start empty and build a sorted list
            for j in default_exits:
                for i, easy in enumerate(x):
                    if j == easy:
                        matches.append(y[i])
            s = set(matches)  # Set magic for adding back non-matches.
            return matches + [z for z in y if z not in s]

        for con in visible:
            if con.destination:
                exits.append(con)
        string = "\n%s\n" % self.get_display_name(viewer, mxp='sense here')
        desc = self.db.desc  # get description, build string
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'Nothing more than smoke and mirrors appears around you.'
        if self.attributes.has('exits'):
            ways = self.db.exits
        if exits or ways:
            string += "\n|wVisible exits|n: "
            for e in exits:  # Green or Blue exits
                exits_simple.append(e.name)
                exit_color = '|225' if e.tags.get('path', category='flags') or False else e.STYLE  # Blue if path exit
                exits_complex.append("|lc%s|lt%s%s|n|le" % (e.key, exit_color, e.key))
            if ways and not ways == {}:  # Orange exits
                for w in ways:
                    exits_simple.append(way_dir[w])
                    exits_complex.append("|lc%s|lt|530%s|n|le" % (w, way_dir[w]))
            string += ", ".join(d for d in sort_exits(exits_simple, exits_complex))
        elif viewer.db.last_room:
            string += "\n|wVisible exits|n: |lcback|lt|gBack|n|le to %s." % viewer.db.last_room.get_display_name(viewer)
        if self.ndb.weather_last:
            string += '|/|*%s|n' % self.ndb.weather_last
        if self.return_glance(viewer, bool=True):  # Glance to see what is within the room that can be seen
            string += ("\n|wHere you find:|n " + self.return_glance(viewer))  # Glance again to list items.
        return string

    def announce_move_from(self, destination):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.
        Args:
            destination (Object): The place we are going to.
        """
        if not self.location:
            return
        name = self.name
        loc_name = self.location.name
        dest_name = destination.name
        string = "%s%s|n is leaving %s%s|n, heading for %s%s|n." % (self.STYLE, name, self.location.STYLE, loc_name,
                                                                    destination.STYLE, dest_name)
        self.location.msg_contents(string, exclude=self)

    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.
        Args:
            source_location (Object): The place we came from
        """
        name = self.name
        if not source_location and self.location.has_account:
            # This was created from nowhere and added to a account's
            # inventory; it's probably the result of a create command.
            string = "You now have %s%s|n in your possession." % (self.STYLE, name)
            self.location.msg(string)
            return
        src_name = "nowhere"
        loc_name = self.location.name
        if source_location:
            src_name = source_location.name
        string = "%s%s|n arrives to %s%s|n from %s%s|n." % (self.STYLE, name, self.location.STYLE, loc_name,
                                                            source_location.STYLE, src_name)
        self.location.msg_contents(string, exclude=self)

    def at_object_creation(self):
        """Called when room is first created"""
        self.db.desc_brief = "This is a default room."

    def at_object_receive(self, new_arrival, source_location):
        """
        When an object enters a room we tell other objects in the room
        about it by trying to call a hook on them. The Mob object
        uses this to cheaply get notified of enemies without having
        to constantly scan for them.

        Args:
            new_arrival (Object): the object that just entered this room.
            source_location (Object): the previous location of new_arrival.
        """
        if self.tags.get('rp', category='flags') and not new_arrival.attributes.has('_sdesc'):
            sdesc = self.db.messages and self.db.messages.get('species') or new_arrival.key
            new_arrival.sdesc.add(sdesc)
        if new_arrival.has_account:  # and not new_arrival.is_superuser: # this is a character
            if self.tags.get('weather', category='flags'):
                if not self.nattributes.has('weather_time'):
                    self.attempt_weather_update(1.00)  # 100% chance of update on initial arrival.
                tickers = TICKER_HANDLER.all_display()
                counter = 0
                for tick in tickers:
                    if tick[0] == self and tick[1] == 'update_weather':
                        notice = ''
                        counter += 1
                        show = '20%% chance every %s seconds in ' % tick[3]
                        show += "%s%s" % (tick[0] or "[None]", tick[0] and " (#%s)" %
                                          (tick[0].id if hasattr(tick[0], 'id') else '') or '')
                        if counter > 1:
                            notice = '|rExtra Ticker|n - |yadditional|n '
                            # TODO: Too many weather tickers going, maybe remove extra?
                        channel = ChannelDB.objects.channel_search('MudInfo')
                        if channel[0]:
                            channel[0].msg('* %s\'s %s experience * %s%s' % (new_arrival.key, tick[4], notice, show),
                                           keep_log=False)
                if counter == 0:  # No weather ticker! Add a weather ticker.
                    interval = random.randint(12, 30) * 10
                    TICKER_HANDLER.add(interval=interval, callback=self.update_weather, idstring='Weather')
            for obj in self.contents_get(exclude=new_arrival):
                if hasattr(obj, 'at_new_arrival'):
                    obj.at_new_arrival(new_arrival)

    def attempt_weather_update(self, odds):
        """
        Called by update_weather
        Args:
            odds (float): 0 to 1 - odds of the weather changing.
        """
        weather = self.db.weather or (
            "The rain coming down from the iron-grey sky intensifies.",
            "A gust of wind throws the rain right in your face. Despite your cloak you shiver.",
            "The rainfall eases a bit and the sky momentarily brightens.",
            "For a moment it looks like the rain is slowing, then it begins anew with renewed force.",
            "The rain pummels you with large, heavy drops. You hear the rumble of thunder in the distance.",
            "The wind is picking up, howling around you, throwing water droplets in your face. It's cold.",
            "Bright fingers of lightning flash over the sky, moments later followed by a deafening rumble.",
            "It rains so hard you can hardly see your hand in front of you. You'll soon be drenched to the bone.",
            "Lightning strikes in several thundering bolts, striking the trees in the forest to your west.",
            "You hear the distant howl of what sounds like some sort of dog or wolf.",
            "Large clouds rush across the sky, throwing their load of rain over the world.")
        if random.random() >= odds:
            return
        new_weather = random.choice(weather)
        if self.ndb.weather_last != new_weather:  # ... only update on a new weather condition.
            self.msg_contents("|w%s|n" % new_weather)
            self.ndb.weather_last = new_weather
            self.ndb.weather_time = int(time.time())

    def update_weather(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals. Even so, we
        only update 20% of the time, picking a random weather message
        when we do. The tickerhandler requires that this hook accepts
        any arguments and keyword arguments (hence the *args, **kwargs
        even though we don't actually use them in this example)
        """
        slow_room = True
        empty_room = True
        session_list = SESSIONS.get_sessions()
        for session in session_list:
            character = session.get_puppet()
            if not session.logged_in or not character or character.location != self:
                continue
            empty_room = False
            if session.cmd_last_visible > self.ndb.weather_time:
                slow_room = False
                break
        if empty_room:
            return
        if slow_room:
            self.attempt_weather_update(0.05)  # only attempt update 5% of the time
        else:
            self.attempt_weather_update(0.20)

    @classmethod
    def get_room_at(cls, x, y, z):
        """
        Return the room at the given location or None if not found.
        Args:
            x (int): the X coord.
            y (int): the Y coord.
            z (int): the Z coord.
        Return:
            The room at this location (Room) or None if not found.
        """
        rooms = cls.objects.filter(
                db_tags__db_key=str(x), db_tags__db_category="coordx").filter(
                db_tags__db_key=str(y), db_tags__db_category="coordy").filter(
                db_tags__db_key=str(z), db_tags__db_category="coordz")
        if rooms:
            return rooms[0]

        return None

    def get_rooms_near(self, distance):
        """A shortcut into get_rooms_around that is
         some distance from this room."""
        x = int(self.tags.get(category="coordx"))
        y = int(self.tags.get(category="coordy"))
        z = int(self.tags.get(category="coordz"))
        return self.get_rooms_around(x, y, z, distance)

    @classmethod
    def get_rooms_around(cls, x, y, z, distance):
        """Return the list of rooms around the given coords.
        This method returns a list of tuples (distance, room) that
        can easily be browsed.  This list is sorted by distance (the
        closest room to the specified position is always at the top
        of the list).
        Args:
            x (int): the X coord.
            y (int): the Y coord.
            z (int): the Z coord.
            distance (int): the maximum distance to the specified .
        Returns:
            A list of tuples containing the distance to the specified
            position and the room at this distance.  Several rooms
            can be at equal distance from the position.
        """
        # Performs a quick search to only get rooms in a kind of rectangle
        x_r = list(reversed([str(x - i) for i in range(0, distance + 1)]))
        x_r += [str(x + i) for i in range(1, distance + 1)]
        y_r = list(reversed([str(y - i) for i in range(0, distance + 1)]))
        y_r += [str(y + i) for i in range(1, distance + 1)]
        z_r = list(reversed([str(z - i) for i in range(0, distance + 1)]))
        z_r += [str(z + i) for i in range(1, distance + 1)]
        wide = cls.objects.filter(
                db_tags__db_key__in=x_r, db_tags__db_category="coordx").filter(
                db_tags__db_key__in=y_r, db_tags__db_category="coordy").filter(
                db_tags__db_key__in=z_r, db_tags__db_category="coordz")

        # We now need to filter down this list to find out whether
        # these rooms are really close enough, and at what distance
        rooms = []
        for room in wide:
            x2 = int(room.tags.get(category="coordx"))
            y2 = int(room.tags.get(category="coordy"))
            z2 = int(room.tags.get(category="coordz"))
            distance_to_room = sqrt(
                    (x2 - x) ** 2 + (y2 - y) ** 2 + (z2 - z) ** 2)
            if distance_to_room <= distance:
                rooms.append((distance_to_room, room))

        # Finally sort the rooms by distance
        rooms.sort(key=lambda tup: tup[0])
        return rooms

    def _get_x(self):
        """Return the X coordinate or None."""
        x = self.tags.get(category="coordx")
        return int(x) if isinstance(x, str) else None

    def _set_x(self, x):
        """Change the X coordinate."""
        old = self.tags.get(category="coordx")
        if old is not None:
            self.tags.remove(old, category="coordx")
        self.tags.add(str(x), category="coordx")
    x = property(_get_x, _set_x)

    def _get_y(self):
        """Return the Y coordinate or None."""
        y = self.tags.get(category="coordy")
        return int(y) if isinstance(y, str) else None

    def _set_y(self, y):
        """Change the Y coordinate."""
        old = self.tags.get(category="coordy")
        if old is not None:
            self.tags.remove(old, category="coordy")
        self.tags.add(str(y), category="coordy")
    y = property(_get_y, _set_y)

    def _get_z(self):
        """Return the Z coordinate or None."""
        z = self.tags.get(category="coordz")
        return int(z) if isinstance(z, str) else None

    def _set_z(self, z):
        """Change the Z coordinate."""
        old = self.tags.get(category="coordz")
        if old is not None:
            self.tags.remove(old, category="coordz")
        self.tags.add(str(z), category="coordz")
    z = property(_get_z, _set_z)


class RealmEntry(Room):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    STYLE = '|242'

    def at_object_creation(self):
        """Called when the room is first created."""
        super(RealmEntry, self).at_object_creation()
        self.db.desc_brief = "An entry point for the realm, this room checks " \
                             "the realm-specific requirements before allowing entry."

    def at_object_receive(self, character, source_location):
        """Assign properties on characters"""

        if character.is_superuser:
            string = "-" * 78 +\
                     "|/WARNING: You are playing while superuser. Use the {quell} command|/" \
                     " to play without superuser privileges (many functions and locks are bypassed|/" \
                     " by default by the presence of a superuser, making this mode really only useful|/" \
                     " for exploring things behind the scenes later or entering to make modifications).|/"\
                     + "-" * 78
            character.msg("|r%s|n" % string.format(quell="|w@quell|r"))
        else:  # setup character for the particular realm:
            pass


class CmdSetGridRoom(CmdSet):
        """This method adds commands to the grid room command set."""
        key = 'Grid Nav'
        priority = 101  # Same as Exit objects

        def at_cmdset_creation(self):
            self.add(CmdGrid())
            self.add(CmdGridNorth())
            self.add(CmdGridSouth())
            self.add(CmdGridEast())
            self.add(CmdGridWest())
            self.add(CmdGridNortheast())
            self.add(CmdGridNorthwest())
            self.add(CmdGridSoutheast())
            self.add(CmdGridSouthwest())


class CmdGridMotion(default_cmds.MuxCommand):
    """
    Parent class for all simple exit-directions.
    Actual exit objects superseded these in every way.

    Grid locations are stored on the Grid room that is navigated by these commands.
    Usage:
    """
    arg_regex = r'^/|\s|$'
    auto_help = True
    help_category = 'Travel'
    account_caller = True

    def func(self):
        """Command for all simple exit directions."""
        you = self.character
        loc = you.location
        now = int(time.time())
        coord = you.ndb.grid_loc
        min = loc.grid('min')
        max = loc.grid('max')
        if not coord:  # A default place - this logic should check last crumbs instead.
            coord = loc.grid('current')
        bound = self.motion(coord)
        into = loc.point(bound, 'into')
        empty = loc.point(bound, 'empty')
        carve = loc.tags.get('carve', category='flags')
        name = loc.point(coord, 'name')
        desc = loc.point(coord, 'desc')
        if carve and not empty and not name and not desc:
            empty = True  # Carve through, empty means impassible if name/desc not set
        if into:
            you.move_to(into)
            return
        if bound[0] > max[0] or bound[1] > max[1] or bound[0] < min[0] or bound[1] < min[1] or empty:
            you.msg("You cannot travel %s." % self.key)
            return
        if not name:
            name = '%s @ %r' % (loc.get_display_name(you, mxp='sense here'), coord)
        last, coord = coord, self.motion(coord)  # Update coord with move, save last for later use
        new = loc.point(coord, 'name')
        if not new:
            new = '%s @ %r' % (loc.get_display_name(you, mxp='sense here'), coord)
        # Check for riders/followers to bring them along
        # If rider/follower, add to lists. Riders move with mounts; followers move later
        # r_list = you.db.riders if you.db.riders and len(you.db.riders) > 0 else False  # FIXME temporary hack
        f_list = you.db.followers if you.db.followers and len(you.db.followers) > 0 else False
        r_list = f_list  # <- FIXME temporary hack (Remove this line when updated)
        riders, followers = [], []
        if r_list:
            for each in r_list:
                if each.location != loc:
                    continue
                if each.ndb.grid_loc == last and each not in riders:
                    riders.append(each)  # Add this one to the list, it will ride with you
                    loc.point(coord, each, now)  # Apply timestamp
                    each.ndb.grid_loc = coord  # Mark location on moving object's followers/riders
        if len(riders) > 0:
            bringing = ", ".join(each.get_display_name(you) for each in riders)
            loc.msg_contents('{you} takes %s |g%s|n from %s to %s.'
                             % (bringing, self.key, name, new), from_obj=you, mapping=dict(you=you))
        else:
            loc.msg_contents('{you} moves |g%s|n from %s to %s.'
                             % (self.key, name, new), from_obj=you, mapping=dict(you=you))
        loc.point(coord, you, now)  # Apply timestamp
        you.ndb.grid_loc = coord  # Mark location on moving object and its riders
        you.msg(you.at_look(you.location))
        if r_list:  # All the riders look upon arrival
            for each in riders:
                each.msg(each.at_look(each.location))
        if f_list:
            pass  # Command the followers here

    def motion(self, position=(0, 0)):
        """
        Update character's position in room where position is (x, y)
        TODO: Allow for X and/or Y wrap-around by checking settings,
        min, max, and returning new location after move.

        """
        direction = self.key
        x_motion, y_motion = (0, 0)
        if 'north' in direction:
            y_motion = -1
        if 'east' in direction:
            x_motion = 1
        if 'west' in direction:
            x_motion = -1
        if 'south' in direction:
            y_motion = 1
        x_pos, y_pos = position
        x_out, y_out = map(lambda x, y: x + y, (x_pos, y_pos), (x_motion, y_motion))
        return x_out, y_out  # Defaults to tuple


class CmdGrid(CmdGridMotion):
    """
    grid  -- manage the room's grid.
    Usage:
      grid
    Switches:
    /exits   Show exits of the room affected by grid motion commands.
    /size <[xmin..xmax, ymin..ymax]>   Show or edit the current working grid size of the room.
    /base <[x, y]>                     Show or edit the base (center) of the grid in the room.
    /current <[x, y]>                  Show or edit the current working location in the room.
    /large                             Show a large grid to represent the grid room layout.
    /small                             Show a small grid to represent the grid room layout.
    """
    key = 'grid'
    help_category = 'Building'
    locks = 'cmd:perm(Builders)'
    account_caller = True

    def func(self):
        """Command to manage all grid room properties."""
        you = self.character
        loc = you.location
        min = loc.grid('min')
        max = loc.grid('max')
        base = loc.grid('base')
        current = loc.grid('current')
        x, y = current
        size = [abs(min[0] - max[0]) + 1, abs(min[1] - max[1]) + 1]
        if 'exits' in self.switches:
            exits = []
            for e in loc.exits:
                short_name = str(e.key)
                exits.append([e, short_name])
            you.msg("Exits: %s" % exits)
        if 'size' in self.switches:
            if not self.args:
                you.msg("Room: %sx%s as %s..%s, %s..%s  Current editing position: (%s, %s)" %
                        (size[0], size[1], min[0], max[0], min[1], max[1], x.current, y.current))
                you.msg('|wUse this format to resize: |ggrid/size xmin..xmax, ymin..ymax')
            else:
                x_y = self.args.split(',')
                xr, yr = x_y[0], x_y[1] if len(x_y) > 1 else [x_y[0], x_y[0]]
                xmin, xmax = xr.split('..') if len(xr.split('..')) > 1 else [str(xr), str(xr + 1)]
                ymin, ymax = yr.split('..') if len(yr.split('..')) > 1 else [str(yr), str(yr + 1)]
                xmin, xmax, ymin, ymax = [int(xmin), int(xmax), int(ymin), int(ymax)]
                if xmax-xmin < 99 and ymax-ymin < 99 and xmin <= base[0] <= xmax and ymin <= base[1] <= ymax:
                    you.msg("Room: %sx%s as [%s..%s, %s..%s]" %
                            (xmax-xmin+1, ymax-ymin+1, xmin, xmax, ymin, ymax))
                    min, max, = (xmin, ymin), (xmax, ymax)
                    loc.grid(min=min, max=max)
                else:
                    range_error = "x0..x1, y0..y1 ranges must be at least 1 and at most 100."
                    base_error = "Base values [%s, %s] must be within [x0..x1, y0..y1]." \
                                 "|/Change ranges, or change base values." % (base[0], base[1])
                    you.msg(base_error if xmax-xmin < 99 and ymax-ymin < 99 else range_error)
            return
        if 'base' in self.switches:
            x_y = self.args.split(',')
            xbase, ybase = int(x_y[0]), int(x_y[1]) if len(x_y) > 1 else (0, 0)
            if min[0] <= xbase <= max[0] and min[1] <= ybase <= max[1]:
                base = [xbase, ybase]
                loc.grid(base=base)
                you.msg("|gRoom base set|n to [%s, %s] within %sx%s area [%s..%s, %s..%s]" %
                        (xbase, ybase, size[0], size[1], min[0], max[0], min[1], max[1]))
            else:
                you.msg("|rRoom base must be within %sx%s area|n [%s..%s, %s..%s]" %
                        (size[0], size[1], min[0], max[0], min[1], max[1]))
        if 'current' in self.switches:
            if not self.args:
                xcurr, ycurr = you.ndb.grid_loc or (0, 0)
            else:
                x_y = self.args.split(',')
                xcurr, ycurr = int(x_y[0]), int(x_y[1]) if len(x_y) > 1 else (0, 0)
            if min[0] <= xcurr <= max[0] and min[1] <= ycurr <= max[1]:
                current = (xcurr, ycurr)
                loc.grid(current=current)
                you.msg("|gRoom current edit location set|n to [%s, %s] within %sx%s area [%s..%s, %s..%s]" %
                        (xcurr, ycurr, size[0], size[1], min[0], max[0], min[1], max[1]))
            else:
                you.msg("|rRoom current edit location must be within %sx%s area|n [%s..%s, %s..%s]" %
                        (size[0], size[1], min[0], max[0], min[1], max[1]))
        small = True if 'small' in self.switches else False
        if small or 'large' in self.switches:
            intro = 'Small' if small else 'Large'
            you.msg('%s grid display of room:|/' % intro)
            for i in range(min[1], max[1] + 1):
                line_list = []
                if small:
                    for j in range(min[1], max[1] + 1):
                        line_list.append(' x ' if x == j and y == i else ' . ')
                    you.msg(''.join(line_list) + '|/')
                else:
                    for k in range(0, 2):
                        for j in range(min[0], max[0] + 1):
                            if k == 0:
                                line_list.append('[ _ ] ' if x == j and y == i else '[   ] ')
                            else:
                                line_list.append('[___] ' if x == j and y == i else '[___] ')
                        line_list.append('|/')
                    you.msg(''.join(line_list))
        coord = loc.grid('current')
        if 'name' in self.switches:
            if self.args:
                loc.point(coord, 'name', self.args)
                you.msg('|gAdded |cgrid/name %s|w to |y%r' % (self.args, coord))
            else:
                name = loc.point(coord, 'name')
                if name:
                    you.msg('%s - %s @ %r' % (loc.get_display_name(you), name, coord))
                    you.msg('You can change the name to this location with |ggrid/name <new name>')
                else:
                    you.msg('You can add a name to this location with |ggrid/name <name>')
        if 'desc' in self.switches:
            if self.args:
                loc.point(coord, 'desc', self.args)
                you.msg('|gAdded |cgrid/desc %s|w to |y%r' % (self.args, coord))
            else:
                you.msg('You can add/change the description of this location with |ggrid/desc <new description>')
        if 'empty' in self.switches:  # Toggle True/False on current 'empty' entry.
            setting = loc.point(coord, 'empty')
            if self.args:
                if 'on' in self.args.lower() or 'yes' in self.args.lower() or 'true' in self.args.lower():
                    setting = True
                elif 'off' in self.args.lower() or 'no' in self.args.lower() or 'false' in self.args.lower():
                    setting = False
                loc.point(coord, 'empty', setting)
                you.msg('|gSet |cgrid/empty @ %r %s|w' % (coord, setting))
            else:
                you.msg('|gViewing |cgrid/empty @ %r %s|w' % (coord, setting))
        if 'exit' in self.switches:
            if self.args:
                loc.point(coord, self.args, True)
                you.msg('|gAdded |cgrid/exit %s|w to |y%r' % (self.args, coord))
            else:
                you.msg('You can add the name of the exit leaving this location with |ggrid/exit <exit name>')
        if 'into' in self.switches:
            if self.args:
                into_room = you.search(self.args, global_search=True)
                if into_room:
                    loc.point(coord, 'into', into_room)
                    you.msg('|gAdded |cgrid/into %s|w to |y%r' % (into_room.get_display_name(you), coord))
                else:
                    return
            else:
                you.msg('You can add the name of a room to move into when'
                        ' entering this location with |ggrid/into <room name>')
        if 'here' in self.switches or 'there' in self.switches:
            here = you.ndb.grid_loc
            there = loc.grid('current')
            if here == there:
                name = '%s - %s' % (loc.get_display_name(you), loc.point(here, 'name'))
                you.msg('|yYou are already here at Current edit location %s|w @ %r' % (name, coord))
                return
            if 'here' in self.switches:
                if here:
                    loc.grid('current', here)
                    coord = here
                    name = '%s - %s' % (loc.get_display_name(you), loc.point(here, 'name'))
                    you.msg('|yCurrent edit location moved here at %s|w @ %r' % (name, coord))
                else:
                    here = there
                    name = '%s - %s' % (loc.get_display_name(you), loc.point(here, 'name'))
                    you.msg('|yYou are already here at Current edit location %s|w @ %r' % (name, coord))
                return
            if 'there' in self.switches:
                if here:
                    you.ndb.grid_loc = there
                    name = '%s - %s' % (loc.get_display_name(you), loc.point(here, 'name'))
                    you.msg('|yYou have been moved to Current edit location at %s|w @ %r' % (name, coord))
                else:
                    here = there
                    name = '%s - %s' % (loc.get_display_name(you), loc.point(here, 'name'))
                    you.msg('|yYou are already here at Current edit location %s|w @ %r' % (name, coord))
                return
        if not self.switches:
            loc.msg_contents('{you} examines {loc}.', from_obj=you, mapping=dict(you=you, loc=loc))
            name = loc.point(coord, 'name')
            you.msg("Room: %sx%s as [%s..%s, %s..%s]|/Base editing position: %r|/Current editing position named %s: %r"
                    % (size[0], size[1], min[0], max[0], min[1], max[1], base, name, current))


class CmdGridNorth(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "north  or n        -- move north on the room's grid."
    key = 'north'
    aliases = 'n'
    locks = 'cmd:not on_exit(n)'


class CmdGridNortheast(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "northeast  or ne   -- move northeast on the room's grid."
    key = 'northeast'
    aliases = 'ne'
    locks = 'cmd:not on_exit(ne)'


class CmdGridNorthwest(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "northwest  or nw   -- move northwest on the room's grid."
    key = 'northwest'
    aliases = 'nw'
    locks = 'cmd:not on_exit(nw)'


class CmdGridEast(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "east  or e         -- move east on the room's grid."
    key = 'east'
    aliases = 'e'
    locks = 'cmd:not on_exit(e)'


class CmdGridSouth(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "south  or s        -- move south on the room's grid."
    key = 'south'
    aliases = 's'
    locks = 'cmd:not on_exit(s)'


class CmdGridSoutheast(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "sortheast  or se   -- move southeast on the room's grid."
    key = 'southeast'
    aliases = 'se'
    locks = 'cmd:not on_exit(se)'


class CmdGridSouthwest(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "southwest  or sw   -- move southwest on the room's grid."
    key = 'southwest'
    aliases = 'sw'
    locks = 'cmd:not on_exit(sw)'


class CmdGridWest(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "west  or w         -- move west on the room's grid."
    key = 'west'
    aliases = 'w'
    locks = 'cmd:not on_exit(w)'


class Grid(Room):
    """
    Grid Rooms are like any Room, except they have sub locations within
    by default. Objects dropped here are associated with a specific 
    location preventing them from being picked up unless the character
    is next to them.
    """
    STYLE = '|204'

    def return_appearance(self, viewer):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return ''
        loc = viewer.location
        coord = viewer.ndb.grid_loc
        if not coord:
            coord = loc.grid('current')
        name = loc.point(coord, 'name')
        desc = loc.point(coord, 'desc')
        if not (name or desc):
            return super(Grid, self).return_appearance(viewer)
        else:
            name = '%s - %s' % (self.get_display_name(viewer, mxp='sense here'), name)
        visible = [element for element in self.contents if element != viewer and not element.destination
                   and element.access(viewer, 'view')]
        here = [element for element in visible if element.ndb.grid_loc == coord]
        there = [element for element in visible if element not in here]
        # Contents you can see.  Show here, and then show there (with names).
        string = ' |/|y%s|n|/%s' % (name, desc or '')
        if here:
            here_list = ", ".join(each.get_display_name(viewer, pose=True) for each in here).replace('.,', ';')
            string += '|/Here you find: %s' % here_list  # If something here can be seen, list it
        if there:
            there_list = ", ".join(each.get_display_name(viewer, pose=True) for each in there).replace('.,', ';')
            string += '|/Elsewhere: %s' % there_list  # If something there can be seen, list it
        return string

    def grid(self, key=None, value=None, **kwargs):
        """Read/Write dictionary in the grid attribute for persistence.
        To read keys and values, call with the keys you want by setting
        the values to None.
        To write keys and values, call with the keys you want and set their
        values to anything not None.
        """
        if not self.db.grid:
            self.db.grid = {}
        results = {}
        # for k, v in kwargs.items():  # Use this after update to Python 3
        for k, v in kwargs.iteritems():  # Use this until update to Python 3
            if v is None:  # Skip setting any entry whose value is set to None
                results[k] = self.db.grid.get(k, None)
                continue
            self.db.grid[k] = v
        if key:
            if value:
                self.db.grid[key] = value
            else:
                results = self.db.grid.get(key, None)
        return results

    def point(self, loc, key=None, value=None, **kwargs):
        push, pop = [kwargs.get('push', False), kwargs.get('pop', False)]  # Read kwargs, set defaults.
        entries = self.grid(loc) or {}
        if value:  # Writing an entry.
            if pop:  # Deleting the entry
                entries.pop(key, None)  # popped from entries
            else:  # Add or push the entry given
                if push:  # Pushing an entry into a list
                    if not entries[key]:  # Is this entry empty?
                        entries[key] = []  # initialize new list
                    entries[key].append(value)  # Append entries to list
                else:
                    if entries is None:  # Is this entry empty?
                        entries = {}  # If so, start with a blank dictionary
                    entries[key] = value
            self.grid(loc, entries)  # Write all entries for loc back to grid.
            return entries  # Return all loc entries, which could be useful.
        else:  # Reading an entry.
            return entries.get(key, None) if key else entries  # return requested entry or all entries

    def crumbs(self, traveller):
        """

        Returns:
            list of breadcrumbs, latest to oldest
        """
        pass

    def at_object_receive(self, new_arrival, source_location):
        """
        When an object enters a room we tell other objects in the room
        about it by trying to call a hook on them.

        An arriving object's location needs to be set if it entered
        in a specific way, or restored if it is returning via teleport, etc.

        Args:
            new_arrival (Object): the object that just entered this room.
            source_location (Object): the previous location of new_arrival.
        """
        super(Grid, self).at_object_receive(new_arrival, source_location)

    def at_object_creation(self):
        """called when the object is first created"""
        self.cmdset.add_default(CmdSetGridRoom)
        self.grid(base=(0, 0), current=(0, 0), min=(0, 0), max=(0, 0))  # Make default 1 x 1 room
