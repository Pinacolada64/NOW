# -*- coding: UTF-8 -*-
"""
Objects are the base class for items in-world.

The default Character, Room and Exit does not inherit from this Object,
but from their respective default implementations in the evennia library.
If you want a class as a parent to change all tangible types, you can do
so by editing the Tangible class in tangibles.py.
"""
from evennia import DefaultObject
from typeclasses.tangibles import Tangible
from evennia.utils.utils import lazy_property
from traits import TraitHandler
from evennia.utils.evmenu import get_input
from world.helpers import make_bar, mass_unit
from commands.poll import PollCmdSet


class Junk(DefaultObject):
    """A minimal object - not intended to be tangible."""

    STYLE = '|r'  # Nobody except superusers would see junk objects directly.

    def basetype_setup(self):
        """
        Junk objects are meant as object placeholders.
        """
        super(Junk, self).basetype_setup()

        # Set locks: can't do much with this object type
        self.locks.add(';'.join([
            'get:none()', 'view:none()', 'puppet:none()', 'tell:none()', 'examine:perm(Immortal)',
            'edit:perm(Immortal)', 'control:perm(Immortal)', 'call:none()']))


class Object(Tangible):
    """
    This is the root typeclass object, implementing an in-game Evennia
    game object, such as having a location, being able to be
    manipulated or looked at, etc. If you create a new typeclass, it
    must always inherit from this object (or any of the other objects
    in this file, since they all actually inherit from BaseObject, as
    seen in src.object.objects).

    The BaseObject class implements several hooks tying into the game
    engine. By re-implementing these hooks you can control the
    system. You should never need to re-implement special Python
    methods, such as __init__ and especially never __getattribute__ and
    __setattr__ since these are used heavily by the typeclass system
    of Evennia and messing with them might well break things for you.


    * Base properties defined/available on all Objects

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved to
                           database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
                                  back to this class
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     player (Player) - controlling player (if any, only set together with
                       sessid below)
     sessid (int, read-only) - session id (if any, only set together with
                       player above). Use `sessions` handler to get the
                       Sessions directly.
     location (Object) - current location. Is None if this is a room
     home (Object) - safety start-location
     sessions (list of Sessions, read-only) - returns all sessions connected
                       to this object
     has_player (bool, read-only)- will only return *connected* players
     contents (list of Objects, read-only) - returns all objects inside this
                       object (including exits)
     exits (list of Objects, read-only) - returns all exits from this
                       object, if any
     destination (Object) - only set if this object is an exit.
     is_superuser (bool, read-only) - True/False if this user is a superuser

    * Handlers available

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                             self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create
                             a database entry when storing data
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().
     sessions - sessions-handler. Get Sessions connected to this
                object with sessions.get()

    * Helper methods (see src.objects.objects.py for full headers)

     search(ostring, global_search=False, attribute_name=None,
             use_nicks=False, location=None, ignore_errors=False, player=False)
     execute_cmd(raw_string)
     msg(text=None, **kwargs)
     msg_contents(message, exclude=None, from_obj=None, **kwargs)
     move_to(destination, quiet=False, emit_to_obj=None, use_destination=True)
     copy(new_key=None)
     delete()
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hooks (these are class methods, so args should start with self):

     basetype_setup()     - only called once, used for behind-the-scenes
                            setup. Normally not modified.
     basetype_posthook_setup() - customization in basetype, after the object
                            has been created; Normally not modified.

     at_object_creation() - only called once, when object is first created.
                            Object customizations go here.
     at_object_delete() - called just before deleting an object. If returning
                            False, deletion is aborted. Note that all objects
                            inside a deleted object are automatically moved
                            to their <home>, they don't need to be removed here.

     at_init()            - called whenever typeclass is cached from memory,
                            at least once every server restart/reload
     at_cmdset_get(**kwargs) - this is called just before the command handler
                            requests a cmdset from this object. The kwargs are
                            not normally used unless the cmdset is created
                            dynamically (see e.g. Exits).
     at_pre_puppet(player)- (player-controlled objects only) called just
                            before puppeting
     at_post_puppet()     - (player-controlled objects only) called just
                            after completing connection player<->object
     at_pre_unpuppet()    - (player-controlled objects only) called just
                            before un-puppeting
     at_post_unpuppet(player) - (player-controlled objects only) called just
                            after disconnecting player<->object link
     at_server_reload()   - called before server is reloaded
     at_server_shutdown() - called just before server is fully shut down

     at_access(result, accessing_obj, access_type) - called with the result
                            of a lock access check on this object. Return value
                            does not affect check result.

     at_before_move(destination)             - called just before moving object
                        to the destination. If returns False, move is cancelled.
     announce_move_from(destination)         - called in old location, just
                        before move, if obj.move_to() has quiet=False
     announce_move_to(source_location)       - called in new location, just
                        after move, if obj.move_to() has quiet=False
     at_after_move(source_location)          - always called after a move has
                        been successfully performed.
     at_object_leave(obj, target_location)   - called when an object leaves
                        this object in any fashion
     at_object_receive(obj, source_location) - called when this object receives
                        another object

     at_traverse(traversing_object, source_loc) - (exit-objects only)
                              handles all moving across the exit, including
                              calling the other exit hooks. Use super() to retain
                              the default functionality.
     at_after_traverse(traversing_object, source_location) - (exit-objects only)
                              called just after a traversal has happened.
     at_failed_traverse(traversing_object)      - (exit-objects only) called if
                       traversal fails and property err_traverse is not defined.

     at_msg_receive(self, msg, from_obj=None, **kwargs) - called when a message
                             (via self.msg()) is sent to this obj.
                             If returns false, aborts send.
     at_msg_send(self, msg, to_obj=None, **kwargs) - called when this objects
                             sends a message to someone via self.msg().

     return_appearance(viewer) - describes this object. Used by "look"
                                 command by default
     at_desc(viewer=None)      - called by 'look' whenever the
                                 appearance is requested.
     at_get(getter)            - called after object has been picked up.
                                 Does not stop pickup.
     at_drop(dropper)          - called when this object has been dropped.
     at_say(speaker, message)  - by default, called if an object inside this
                                 object speaks

    """
    STYLE = '|334'

    def basetype_setup(self):
        """
        Make sure default objects are also dropable by default.
        """
        super(Object, self).basetype_setup()

        self.locks.add(";".join([
            "drop:all()",  # drop object
            ]))

    def at_before_move(self, destination):
        """
        Called just before moving object - If it is supporting another
        object that is currently in the room before allowing the move.
        If it is, we do prevent the move by returning False.
        """
        if not self.location:
            return True  # Avoids being locked in Nothingness.
        # When self is supporting something, do not move it.
        return False if self.attributes.has('locked') and self.db.locked else True

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
        string = "|r%s|n is leaving %s%s|n, heading for %s%s|n." % (name, self.location.STYLE, loc_name,
                                                                    destination.STYLE, dest_name)
        self.location.msg_contents(string, exclude=self)

    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.
        Args:
            source_location (Object): The place we came from
        """
        this = self.name
        here = self.location
        there = source_location
        print(there)
        if not there and here.has_player:
            # This was created from nowhere and added to a player's
            # inventory; it's probably the result of a create command.
            here.msg("You now have %s%s|n in your possession." % (self.STYLE, this))
            return
        if there and there != here:  # TODO: Possible Evennia FIXME:
            string = "|g%s|n arrives to %s%s|n from %s%s|n." % (this, here.STYLE, here.key, there.STYLE, there.key)
        else:
            string = "|g%s|n suddenly appears in %s%s|n from |222Nothingness|n." % (this, here.STYLE, here.key)
        here.msg_contents(string, exclude=self)

    def at_object_creation(self):
            """Called after object is created."""
            if self.tags.get('poll', category='flags'):
                self.cmdset.add('commands.poll.PollCmdSet', permanent=True)

    @staticmethod
    def at_drop(caller):
        """Implements what the dropped object does when dropped by caller."""
        # TODO: Look for odrop or pose message, have self pose it to the room
        pass

    def at_get(self, getter):
        """Implements what the dropped object does when taken by caller."""
        # TODO: Look for take message on self, pose to getter
        getter.msg("%s is now in your possession." % self.get_display_name(getter, mxp='sense %s' % self.key))

    def surface_put(self, pose, caller, connection):
        """Implements the surface connection of object by caller."""
        if not self.attributes.has('surface'):
            self.db.surface = {}
        surface = self.db.surface
        if caller in surface:         
            return False
        surface[caller] = connection
        self.db.locked = True
        caller.db.locked = True
        caller.location.msg_contents("%s|g%s|n sits %s %s%s|n." % (pose, caller.key, connection, self.STYLE, self.key))
        return True

    def surface_off(self, pose, caller):
        """Implements the surface disconnection of object by caller."""
        surface = self.db.surface
        if caller in surface:
            del(surface[caller])
            self.db.surface = surface
            if len(surface) < 1:
                self.attributes.remove('locked')
            caller.attributes.remove('locked')
            caller.location.msg_contents("%s|r%s|n leaves %s%s|n." % (pose, caller.key, self.STYLE, self.key))
            return True
        return False

    def process_sdesc(self, sdesc, obj, **kwargs):
        """
        Allows to customize how your sdesc is displayed (primarily by
        changing colors).

        Args:
            sdesc (str): The sdesc to display.
            obj (Object): The object to which the adjoining sdesc
                belongs (can be yourself).

        Returns:
            sdesc (str): The processed sdesc ready
                for display.

        """
        return '|g%s|n' % sdesc

    def return_appearance(self, viewer):
        """This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return None
        # get and identify all objects
        visible = (con for con in self.contents if con != viewer and con.access(viewer, "view"))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_player:
                users.append(con)
            else:
                things.append(con)
        # get description, build string
        string = self.get_display_name(viewer, mxp='sense #%s' % self.id)
        string += " (%s)" % mass_unit(self.get_mass())
        if self.traits.health:  # Add health bar if object has health.
            gradient = ["|[300", "|[300", "|[310", "|[320", "|[330", "|[230", "|[130", "|[030", "|[030"]
            health = make_bar(self.traits.health.actual, self.traits.health.max, 20, gradient)
            string += " %s\n" % health
        if self.db.surface:
            string += " -- %s" % self.db.surface
        string += "\n"
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'A shimmering illusion of %s shifts from form to form.' % self.name
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.get_display_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer) for t in things)
            string += "\n|wContains:|n " + user_list + ut_joiner + item_list
        return string


class Consumable(Object):  # TODO: State and analog decay. (State could be discrete analog?)
    """
    This is the consumable typeclass object, implementing an in-game
    object, to be consumed and decay, break, be eaten, drank, cast,
    burned, or wear out slowly like clothing or furniture.
    """
    STYLE = '|321'

    def consume(self, caller):
        """
        Use health.
        """
        if self.traits.health.actual:
            self.traits.health.current -= 1
        return self.traits.health.actual

    def drink(self, caller):  # TODO: Make this use a more generic def consume
        """Response to drinking the object."""
        if not self.locks.check_lockstring(caller, 'holds()'):
            msg = "You are not holding %s." % self.get_display_name(caller.sessions)
            caller.msg(msg)
            return False
        finish = ''
        if self.traits.health.actual:
            self.traits.health.current -= 1
            if self.traits.health.actual < 1:
                finish = ', finishing it'
                # self.location = None # Leaves empty container.
        else:
            finish = ', finishing it'
            self.location = None
        caller.location.msg_contents('{caller} takes a drink of {drink}%s.'
                                     % finish, from_obj=caller, mapping=dict(char=caller, drink=self))

        def drink_callback(caller, prompt, user_input):
            """"Response to input given after drink potion"""
            msg = "%s begins to have an effect on %s, transforming into species %s." %\
                  (self.get_display_name(caller.sessions), caller.get_display_name(caller.sessions), user_input)
            caller.location.msg_contents(msg)
            caller.db.species = user_input[0:20].strip()

        get_input(caller, "Species? (Type your species setting now, and then [enter]) ", drink_callback)
        return True

    def eat(self, caller):  # TODO: Make this use a more generic def consume
        """Response to eating the object."""
        if not self.locks.check_lockstring(caller, 'holds()'):
            msg = "You are not holding %s." % self.get_display_name(caller.sessions)
            caller.msg(msg)
            return False
        finish = ''
        if self.traits.health.actual:
            self.traits.health.current -= 1
            if self.traits.health.actual < 1:
                finish = ', finishing it'
                self.location = None
        else:
            finish = ', finishing it'
            self.location = None
        msg = "%s%s|n takes a bite of %s%s|n%s." % (caller.STYLE, caller.key, self.STYLE, self.key, finish)
        caller.location.msg_contents(msg)
        return None


class Tool(Consumable):
    """
    This is the Tool typeclass object, implementing an in-game
    object, to be used to craft, alter, or destroy other objects.
    """
    STYLE = '|511'

    # Currently there is nothing special about a tool compared to a Consumable.


class Vehicle(Tool):
    """
    This is the Vehicle typeclass object, implementing an in-game
    object, to be used to travel at high speeds and, alter, or
    destroy other objects.
    """
    STYLE = '|y|[004'

    def at_object_creation(self):
        """Called after object is created."""
        super(Vehicle, self).at_object_creation()
        self.cmdset.add('commands.vehicle.VehicleCmdSet', permanent=True)

    # Vehicle needs command set that may include speed and direction control,
    # with a way to limit both speed and direction, and only allow movement
    # into specially tagged areas, such as outside, air, cloud, road or offroad.
    # Water or underwater vehicles might be limited to only those tagged rooms.
    # Some public vehicles might even be limited to public places.

    # Also important is the entry/exit of both the contain-type vehicle and
    # the surface-passenger type.  The contain type will require additional
    # mechanisms for viewing the room and also posing, broadcasting, and listening.


class Dispenser(Consumable):
    """
    This is the Tool typeclass object, implementing an in-game
    object, to be used to craft, alter, or destroy other objects.
    """
    STYLE = '|350'

    @staticmethod
    def produce_weapon(caller):
        """
        This will produce a new weapon from the rack,
        assuming the caller hasn't already gotten one. When
        doing so, the caller will get Tagged with the id
        of this rack, to make sure they cannot keep
        pulling weapons from it indefinitely.
        """
        pass
