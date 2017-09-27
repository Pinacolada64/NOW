# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils.evmenu import EvMenu


class CmdMenu(MuxCommand):
    """
    List menus you can use
    Usage:
      menu
    List menus you can use
    """
    key = 'menu'
    locks = 'perm(Players)'
    player_caller = True

    def func(self):
        EvMenu(self.caller, 'commands.menu', startnode='menu_main', cmd_on_exit=None, persistent=False)


def menu_main(caller):
    """
    The menu of menus. These are entry points into other menu areas.
    """
    text = 'Main menu options:'
    options = ({'desc': 'Session menu', 'goto': 'menu_session'},
               {'desc': 'Account menu', 'goto': 'menu_account'},
               {'desc': 'Character menu', 'goto': 'menu_character'},
               {'desc': 'Craft menu', 'goto': 'menu_craft'},
               {'desc': 'Room menu', 'goto': 'menu_room'},
               {'desc': 'Helpstaff menu', 'goto': 'menu_helpstaff'},
               {'desc': 'Mages menu', 'goto': 'menu_mage'},
               {'desc': 'Wizards menu', 'goto': 'menu_wizard'},
               {'desc': 'Immortals menu', 'goto': 'menu_imortal'},
               {'desc': 'Admin menu', 'goto': 'menu_admin'},
               {'desc': 'EXIT', 'key': 'X', 'goto': 'menu_quit'},
               {'key': '_default', 'goto': 'menu_quit'})
    return text, options


def menu_session(caller):
    """
    The menu of sessions. This is the entry point into other session menus.
    """
    text = 'What aspect of your session do you want to change?'
    options = ({'desc': 'View session information', 'goto': 'session_info'},
               {'desc': 'Change session settings', 'goto': 'session_set'},
               {'desc': 'EXIT', 'key': 'X', 'goto': 'menu_quit'},
               {'key': '_default', 'goto': 'menu_quit'})
    return text, options


def menu_account(caller):
    """
    The menu of the user account. This is the entry point into other account menus.
    """
    text = 'What aspect of your account do you want to change?'
    options = ({'desc': 'Account information', 'goto': 'account_info'},
               {'desc': 'Edit or enter account settings', 'goto': 'account_set'},
               {'desc': 'EXIT', 'key': 'X', 'goto': 'menu_quit'},
               {'key': '_default', 'goto': 'menu_quit'})
    return text, options


def menu_character(caller):
    """
    The menu of the characters. This is the entry point into other character menus.
    """
    text = 'What aspect of your character do you want to change?'
    options = ({'desc': 'Change name', 'goto': 'set_name'},
               {'desc': 'Edit or enter description', 'goto': 'set_description'},
               {'desc': 'EXIT', 'key': 'X', 'goto': 'menu_quit'},
               {'key': '_default', 'goto': 'menu_quit'})
    return text, options


def menu_room(caller):
    """
    The menu of room editing. This is the entry point into room menus.
    """
    text = 'What aspect of your room do you want to change?'
    options = ({'desc': 'Change name', 'goto': 'set_name'},
               {'desc': 'Edit or enter description', 'goto': 'set_description'},
               {'desc': 'EXIT', 'key': 'X', 'goto': 'menu_quit'},
               {'key': '_default', 'goto': 'menu_quit'})
    return text, options


def menu_quit(caller):
    """
    Quitting menus and notifying of exiting.
    """
    text = 'Menu exited.'
    caller.msg(text)
    return None, None
