# -*- coding: UTF-8 -*-
from evennia import CmdSet
from evennia.utils.evmenu import EvMenu
from commands.command import MuxCommand


class ConvoCmdSet(CmdSet):
    key = 'talk'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the vehicle object (item or room)."""
        self.add(NPCConvo())


class NPCConvo(MuxCommand):
    """
    Greet an NPC

    Usage:
        greet
    list [description, response], [label, description, response], [label, description, response]]
      Skyrim is a good model for gaming conversation high-end evolution:  Perhaps, have the NPC wait?
      Meanwhile other things can be done.  If too many poses occur, then quit convo.
      If three says occur, quit convo.  If too much time passes, also quit the conversation.
    """
    key = 'greet'
    locks = 'cmd:all()'

    def func(self):
        EvMenu(self.caller, 'commands.greet', startnode='menu_start_node', cmd_on_exit=None, persistent=False)


CONV = [['Say Hello', 'Well, hello there!  How are you this fine day?'],
        ['Ask about potions', 'You can buy potions of various effects in the potion shop.'],
        ['Ask about picking fruits', 'You can earn up to 3 silver pieces a day.'],
        ['Talk about weather', "Yes, it's quite foggy."]]


def menu_start_node(caller):
    text = "NPC greets you."
    options = ()
    for each in CONV:
        options += ({'desc': each[0]},)
    options += ({"key": "_default", "goto": "conversation"},)
    return text, options


def conversation(caller, raw_string):
    inp = raw_string.strip().lower()
    topics = {}
    for i, each in enumerate(CONV):
        topics[str(i + 1)] = CONV[i][1]
    if inp in topics.keys():
        text = topics[inp]
        options = ({'key': "_default", 'goto': 'conversation'})
    else:
        text = obj.get_display_name(caller) + " nods as you end the conversation."
        options = None
    return text, options
