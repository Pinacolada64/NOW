# -*- coding: UTF-8 -*-
from evennia import DefaultObject
from evennia.utils.utils import lazy_property
from traits import TraitHandler
# from effects import EffectHandler


class Tangible(DefaultObject):
    """
    Methods universal to all tangible in-world objects are
    included here.

    Includes all DefaultObject methods and contains methods
    used in Rooms, Characters, Objects, and Exits, which
    are categorized as "Tangible"
    """
    STYLE = '|Y'

    @lazy_property
    def traits(self):
        return TraitHandler(self)

    def get_display_name(self, viewer, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            self (Object, Character, Exit or Room):
            viewer (TypedObject): The object or player that is looking
                at/getting information for this object.
        Kwargs:
            pose Return pose appended to name if True
            color Return includes color style markup prefix if True
            mxp Return includes mxp command markup prefix if provided
            db_id Return includes database id to privliged viewers if True
            plain Return does not include database id or color
        Returns:
            name (str): A string of the sdesc containing the name of the object,
            if this is defined.
                including the DBREF if viewer is privileged to control this.
        """
        color, pose = [kwargs.get('color', True), kwargs.get('pose', False)]  # Read kwargs, set defaults.
        mxp, db_id = [kwargs.get('mxp', False), kwargs.get('db_id', True)]
        if kwargs.get('plain', False):  # "plain" means "without color, without db_id"
            color, db_id = [False, False]
        name = self.key
        if self.location:
            if self.tags.get('rp', category='flags') or self.location.tags.get('rp', category='flags'):
                pass  # NOWTangible is in an RP flagged room.
        elif self.tags.get('rp', category='flags'):
            pass  # NOWTangible is an RP flagged object.
        display_name = ("%s%s|n" % (self.STYLE, name)) if color else name
        if mxp:
            display_name = "|lc%s|lt%s|le" % (mxp, display_name)
        if self.access(viewer, access_type='control') and db_id:
            display_name += '|w(#%s)|n' % self.id
        if pose and self.attributes.get('pose'):
            display_name += ('|n' if color else '') + self.attributes.get('pose')
        return display_name

    def mxp_name(self, viewer, command):  # Depreciated. call obj.get_display_name(viewer, mxp=command)
        """Returns the full styled and clickable-look name for the viewer's perspective as a string."""
        print('*** Depreciated use of mxp_name ***')
        print('%s / %s /%s' % (self.key, viewer.key, command))
        return self.get_display_name(viewer, mxp=command) if viewer and self.access(viewer, 'view') else ''

    def private(self, source, category, text):
        """
        Displays a private message to self from source of a certain category
        Args:
            self (Object, Character, Exit or Room to receive message)
            source (Object, Character, Exit or Room)
            category (string) type of private message.
            text (string) text of private message.
              self will see "You privately " prepended to message.
        """
        print('%s-(%s)-> %s "%s"' % (source.key if source else 'NOW', category, self.key, text))
        message = '%sYou|n privately ' % self.STYLE
        if category == 'whisper':
            message += 'hear %s whisper "|w%s|n".' % (source.get_display_name(self), text)
        elif source is None:
            message = text
        else:
            message += text
        self.msg(message)

    def return_glance(self, viewer):
        """
        Displays the name or sdesc of the object with its room pose in a viewer-aware manner.
        If self is in Nothingness, shows inventory contents instead of room contents.

        Args:
            self (Object, Character, or Room):
            viewer (TypedObject): The object or player that is looking
                at/getting information for this object.

        Returns:
            name (str): A string of the name or sdesc containing the name of the objects
            contained within and their poses in the room. If 'self' is a room, the room
            is omitted from the output. Calls 'get_display_name' - output depends on viewer.
        """
        users, things = [], []
        if self.location:
            visible = (con for con in [self] + self.contents if con != viewer and con.access(viewer, 'view'))
        else:
            visible = (con for con in self.contents if con != viewer and con.access(viewer, 'view'))
        for con in visible:
            if con.has_player:
                users.append(con)
            elif con.destination:
                continue
            else:
                things.append(con)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer, mxp='sense %s' % u.get_display_name(
                viewer, plain=True), pose=True) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer, mxp='sense %s' % t.get_display_name(
                viewer, plain=True), pose=True) for t in things)
            return (user_list + ut_joiner + item_list).replace('\n', '').replace('.,', ';')
        return '%sYou|n see nothing here.' % viewer.STYLE

    def return_detail(self, detail_key):
        """
        This looks for an Attribute "obj_details" and possibly
        returns the value of it.

        Args:
            detail_key (str): The detail being looked at. This is
                case-insensitive.
        """
        return self.db.details.get(detail_key.lower(), None) if self.db.details else None

    def set_detail(self, detail_key, description):
        """
        This sets a new detail, using an Attribute "details".

        Args:
            detail_key (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            description (str): The text to return when looking
                at the given detail_key.
        """
        if self.db.details:
            self.db.details[detail_key.lower()] = description
        else:
            self.db.details = {detail_key.lower(): description}
