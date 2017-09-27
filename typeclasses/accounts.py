"""
Account

The Account represents the game "account" and each login has only one
Account object. An Account is what chats on default channels but has no
other in-game-world existence. Rather the Account puppets Objects (such
as Characters) in order to actually participate in the game world.


Guest

Guest accounts are simple low-level accounts that are created/deleted
on the fly and allows users to test the game without the commitment
of a full registration. Guest accounts are deactivated by default; to
activate them, add the following line to your settings file:

    GUEST_ENABLED = True

You will also need to modify the connection screen to reflect the
possibility to connect with a guest account. The setting file accepts
several more options for customizing the Guest account system.
"""
from evennia import DefaultAccount, DefaultGuest


class Account(DefaultAccount):
    """
    This class describes the actual OOC account (i.e. the user connecting
    to the MUD). It does NOT have visual appearance in the game world (that
    is handled by the character which is connected to this). Comm channels
    are attended/joined using this object.

    It can be useful e.g. for storing configuration options for your game, but
    should generally not hold any character-related info (that's best handled
    on the character level).

    Can be set using BASE_ACCOUNT_TYPECLASS.


    * available properties

     key (string) - name of account
     name (string)- wrapper for user.username
     aliases (list of strings) - aliases to the object.
              Will be saved to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     user (User, read-only) - django User authorization object
     obj (Object) - game object controlled by account. 'character' can also be used.
     sessions (list of Sessions) - sessions connected to this account
     is_superuser (bool, read-only) - if the connected user is a superuser

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create a database entry when storing data
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().

    * Helper methods

     msg(text=None, **kwargs)
     swap_character(new_character, delete_old_character=False)
     execute_cmd(raw_string, session=None)
     search(ostring, global_search=False, attribute_name=None, use_nicks=False,
            location=None, ignore_errors=False, account=False)
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hook methods (when re-implementation, remember methods need to have self as first arg)

     basetype_setup()
     at_account_creation()

     - note that the following hooks are also found on Objects and are
       usually handled on the character level:

     at_init()
     at_cmdset_get(**kwargs)
     at_first_login()
     at_post_login(session=None)
     at_disconnect()
     at_message_receive()
     at_message_send()
     at_server_reload()
     at_server_shutdown()
    """
    STYLE = '|[100'

    def get_display_name(self, looker, **kwargs):
        """Displays the name of the object in a viewer-aware manner."""
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return "%s%s|w(#%s)|n" % (self.STYLE, self.name, self.id)
        else:
            return "%s%s|n" % (self.STYLE, self.name)

    def at_post_login(self, session=None):
        welcome = ('''
        |rN  N |y  OOO |g W   W
        |rNN  N|y OO OO|g W   W
        |rN N N|y O   O|g W W W
        |rN  NN|y OO OO|g W W W
        |r N  N|y  OOO |g  W W
         ''', 'NOW (in large friendly letters)')
        # if the account has saved protocol flags, apply them to this session.
        protocol_flags = self.attributes.get("_saved_protocol_flags", None)
        if session and protocol_flags:
            session.update_flags(**protocol_flags)

        # inform the client of logged in status via OOB message
        if session:
            session.msg(logged_in={})

        self._send_to_connect_channel('|G{} connected|n'.format(self.key))
        if not (self.is_superuser or (self.sessions.count() != 1)):
            if not self.attributes.has('_quell'):
                self.attributes.add('_quell', True)
                self.locks.reset()
        if session:
            webclient = session.protocol_key == 'websocket'
            text = '' if webclient else welcome[0]
            text += ('\n|wSuccessful login. Welcome, %s!' % self.key)
            if webclient:
                session.msg(
                    image=['http://marketingland.com/wp-content/ml-loads/2014/08/google-now-fade-1920-800x450.jpg'])
            session.msg(text)
            session.execute_cmd('@ic')

    def at_disconnect(self):
        super(Account, self).at_disconnect()
        # sessions = self.sessions.all()
        # session = sessions[-1]
        # do_not_exceed = 24  # Keep the last dozen entries
        # if not self.db.lastsite:
        #     self.db.lastsite = []
        # self.db.lastsite = self.db.lastsite.insert(0, (session.address, int(time.time())))
        # if len(self.db.lastsite) > do_not_exceed:
        #     self.db.lastsite.pop()
        # print(session.cmd_total)
        pass  # Write stats to db.


class Guest(DefaultGuest):
    """
    This class is used for guest logins. Unlike Accounts, Guests and their
    characters are deleted after disconnection.
    """
    STYLE = '|[305'

    def get_display_name(self, looker, **kwargs):
        """Displays the name of the object in a viewer-aware manner."""
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return "%s%s|w(#%s)|n" % (self.STYLE, self.name, self.id)
        else:
            return "%s%s|n" % (self.STYLE, self.name)
