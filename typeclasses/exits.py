# -*- coding: UTF-8 -*-
"""
Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination, or if the
Character fails to pass the traverse lock, and the exit has a home set, the
traversing Character it is sent to the Exit's home, instead.
"""
from evennia import utils, Command
from evennia import DefaultExit
from typeclasses.tangibles import Tangible
from evennia.utils.utils import lazy_property
from traits import TraitHandler


MOVE_DELAY = dict(stroll=16, walk=8, run=4, sprint=2, scamper=1)  # TODO Lookup, calculate


class Exit(DefaultExit, Tangible):
    """
    Exits are paths between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_location) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """
    STYLE = '|g'
    STYLE_PATH = '|252'

    def at_desc(self, looker=None):
        """
        This is called whenever looker looks at an exit.
        looker is the object requesting the description.
        Called before return_appearance.
        """
        if not looker.location == self:
            looker.msg("You gaze into the distance.")

    def return_appearance(self, viewer):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return ''
        if not viewer.is_typeclass('typeclasses.accounts.Account'):
            viewer = viewer.account  # make viewer reference the account object
        char = viewer.puppet
        here = char.location
        # get and identify all objects
        visible = (con for con in self.contents if con != char and con.access(viewer, 'view'))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_account:
                users.append(con)
            else:
                things.append(con)
        # get description, build description string seen (desc_seen) for the visible contents
        desc_seen = "%s " % (self.get_display_name(viewer, mxp='sense ' + self.key))
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc and here == self:
            desc_seen += "%s" % desc
        elif desc_brief:
            desc_seen += "%s" % desc_brief
        else:
            leads_to = self.destination.get_display_name(
                viewer, mxp='sense ' + self.destination.key) if self.destination else\
                '|112Nothingness|n. |lcback|ltGo |gback|le.'
            desc_seen += "leads to %s" % leads_to
        if exits:
            desc_seen += "\n|wExits: " + ", ".join(e.get_display_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer) for t in things)
            path_view = 'Y' if here == self else 'Along the way y'
            desc_seen += "\n|w%sou see:|n " % path_view + user_list + ut_joiner + item_list
        return desc_seen

    def at_traverse(self, traveller, destination):
        """
        Implements the actual traversal, using utils.delay to delay the move_to.
        if the exit has an attribute is_path and and traveller has move_speed,
        use that, otherwise default to normal exit behavior and "walk" speed.
        """
        if traveller.ndb.currently_moving:
            traveller.msg("You are already moving toward %s." % destination.get_display_name(traveller))
            return False
        entry = self.cmdset.current.commands[0].cmdstring  # The name/alias of the exit used to initiate traversal
        traveller.ndb.exit_used = entry
        is_path = self.tags.get('path', category='flags') or False
        source_location = traveller.location
        move_speed = traveller.db.move_speed or 'walk'  # TODO use Traits
        move_delay = MOVE_DELAY.get(move_speed, 8)
        if not traveller.at_before_move(destination):
            return False
        if self.db.grid_loc or self.db.grid_locs:
            coord = self.db.grid_loc if not self.db.grid_locs else self.db.grid_locs.get(entry, None)
            if coord:
                grid_loc = traveller.ndb.grid_loc
                if grid_loc:
                    traveller.ndb.grid_loc_last = grid_loc
                traveller.ndb.grid_loc = coord
                name = destination.point(coord, 'name') or ''
                print('%s> %r (%s->%s: %s@%r)' % (traveller, entry, source_location, destination, name, coord))
        if not is_path:
            success = traveller.move_to(self, quiet=False)
            if success:
                self.at_after_traverse(traveller, source_location)
            return success
        if traveller.location == destination:  # If object is at destination...
            return True

        def move_callback():
            """This callback will be called by utils.delay after move_delay seconds."""
            start_location = traveller.location
            if traveller.move_to(destination):
                traveller.nattributes.remove('currently_moving')
                self.at_after_traverse(traveller, start_location)
            else:
                self.at_failed_traverse(traveller)

        traveller.msg("You start moving %s at a %s." % (self.key, move_speed))
        if traveller.location != self:  # If object is not inside exit...
            success = traveller.move_to(self, quiet=False, use_destination=False)
            if not success:
                return False
            self.at_after_traverse(traveller, source_location)
        # Create a delayed movement and Store the deferred on the moving object.
        # ndb is used since deferrals cannot be pickled to store in the database.
        deferred = utils.delay(move_delay, callback=move_callback)
        traveller.ndb.currently_moving = deferred
        return True

    def at_failed_traverse(self, traveller):
        """
        Overloads the default hook to implement an exit fail.
        Args:
            traveller (Object): The object that failed traversing us.
        Notes:
            Uses custom enter-fail in exit's messages dictionary or default.
            Sends traveller to exit's home if defined.
        """
        last = traveller.ndb.grid_loc_last
        if last:
            traveller.ndb.grid_loc = last
        if self.db.messages and 'enter-fail' in self.db.messages:  # if exit has a better error message, use it.
            traveller.msg(self.db.messages['enter-fail'])
        else:  # Otherwise, you stay where you are and get a generic fail message.
            traveller.msg("You cannot go there.")
        if self.home:  # If the exit has a "home" location, it sends you there if you fail the lock.
            if traveller.move_to(self.home):
                traveller.nattributes.remove('currently_moving')
        traveller.nattributes.remove('grid_loc_last')

    def at_after_traverse(self, traveller, source_location):
        """called by at_traverse just after traversing."""
        traveller.nattributes.remove('grid_loc_last')
        # entry = self.cmdset.current.commands[0].cmdstring  # The name/alias of the exit used to initiate traversal
        # if not self.db.grid_loc or not self.db.grid_locs:  # Object exit command display  # DEBUG
        #     print('%s> %r (%s->%s)' % (traveller, entry, source_location, traveller.location))  # DEBUG

    def at_msg_receive(self, text=None, **kwargs):
        """!"""
        # Anything heard by self (this exit) as character speech will be sent to its destination's contents,
        if text and self.tags.get('pool') and 'Portal' not in text:  # TODO: excluding send to exits to avoid loops.
            self.destination.msg_contents('|b%s|n: %s' % (self.key, text))
        return True

SPEED_DESCS = dict(stroll='strolling', walk='walking', run='running', sprint='sprinting', scamper='scampering')


class CmdSpeed(Command):
    """
    Set your character's default movement speed
    Usage:
      speed [stroll||walk||run||sprint||scamper]
    This will set your movement speed, determining how long time
    it takes to traverse exits. If no speed is set, 'walk' speed
    is assumed. If no speed is given, the current speed is shown.
    """
    key = 'speed'
    help_category = 'Travel'

    def func(self):
        """Simply sets an Attribute used by the exit paths in default exits."""
        speed = self.args.lower().strip()
        if not self.args:
            speed = self.caller.traits.speed.actual if self.caller.traits and self.caller.traits.speed.actual else 8
            self.caller.msg("You are set to move by %s." % SPEED_DESCS[speed])
            return
        if speed not in SPEED_DESCS:
            self.caller.msg("Usage: speed stroll||walk||run||sprint||scamper")
        elif self.caller.db.move_speed == speed:  # TODO Update to Traits
            self.caller.msg("You are already set to move by %s." % SPEED_DESCS[speed])
        else:
            self.caller.db.move_speed = speed  # TODO Update to Traits
            self.caller.msg("You will now move by %s." % SPEED_DESCS[speed])


class CmdStop(Command):
    """
    Stops the current character movement, if any.
    Usage:
      stop
    """
    key = 'stop'
    locks = 'cmd:on_path()'
    help_category = 'Travel'

    def func(self):
        """
        This is a very simple command, using the
        stored deferred from the exit traversal above.
        """
        currently_moving = self.caller.ndb.currently_moving
        if currently_moving:
            currently_moving.cancel()  # disables the trigger.
            self.caller.nattributes.remove('currently_moving')  # Removes the trigger.
            self.caller.msg("You stop moving.")
        else:
            self.caller.msg("You are not moving.")


class CmdContinue(Command):
    """
    Move again: Exit the path into the room if stopped.
    Usage:
      continue || move || go
    """
    key = 'continue'
    aliases = ['move', 'go']
    locks = 'cmd:on_path()'
    help_category = 'Travel'

    def func(self):
        """This just moves you if you're stopped."""
        caller = self.caller
        start = caller.location
        destination = caller.location.destination
        if not destination:
            caller.msg("You have not yet decided which way to go.")
            return
        if caller.ndb.currently_moving:
            caller.msg("You are already moving toward %s." % destination.get_display_name(caller))
        else:
            caller.location.msg_contents("%s is going to %s." %
                                         (caller.get_display_name(caller.sessions),
                                          destination.get_display_name(caller.sessions)), exclude=caller)
            caller.msg("You begin %s toward %s." % (SPEED_DESCS[caller.db.move_speed],  # TODO use Traits
                                                    destination.get_display_name(caller.sessions)))
            if caller.move_to(destination, quiet=False):
                start.at_after_traverse(caller, start)


class CmdBack(Command):
    """
    About face! Exit the path into the location room.
    Usage:
      back
    """
    key = 'back'
    aliases = ['return', 'u-turn']
    locks = 'cmd:NOT no_back()'
    help_category = 'Travel'

    def func(self):
        """
        This turns you around if you are traveling,
        or tries to take you back to a previous room
        if you are stopped in a room.
        If you are in Nothingness, you can return somewhere.
        """
        char = self.caller  # The character calling "back"
        here = char.location
        if not here:
            safe_place = char.ndb.last_location or char.db.last_room or char.home
            char.move_to(safe_place)
            visible = (con for con in safe_place.contents if con != char and con.access(char, 'view'))
            for each in visible:
                each.msg('|g%s fades into view.' % char.get_display_name(each, plain=True))
            return
        destination = here.destination  # Where char is going.
        start = here.location  # Where char came from.
        if not destination:  # You are inside of something.
            # Find an exit that leads back to the last room you were in.
            # last_location = char.ndb.last_location or False
            last_room = char.db.last_room or False
            if last_room:  # Message if you have arrived in a room already.
                if last_room != here:  # We are not in the place we were.
                    # We came from another room. How do we go back?
                    exits = here.exits  # All the ways we can go.
                    if exits:
                        for e in exits:  # Iterate through all the exits...
                            # Is this exit the one that takes us back?
                            if e.destination == last_room:  # It's the way back!
                                char.execute_cmd(e.name)  # Try! It might fail.
                    else:  # The room has no way out of it.
                        char.msg("You go back the way you came.")
                        char.move_to(last_room)
            else:  # No way back, try out.
                if start:
                    char.msg("You leave %s." % here.get_display_name(char.sessions))
                    char.move_to(start)
                else:
                    char.msg("You can not leave %s." % here.get_display_name(char.sessions))
            return
        elif char.ndb.currently_moving:  # If you are inside an exit,
            char.execute_cmd('stop')  # traveling, then stop, go back.
        char.msg("You turn around and go back the way you came.")
        char.move_to(start)
