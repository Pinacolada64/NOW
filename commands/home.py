# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils import utils, search


class CmdHome(MuxCommand):
    """
    Takes you to your home, if you have one. home/set will show you
    where your home is set, or provide a what and where to set its home.
    Usage:
      home[/option]
    Options:
    /set <obj> [= home_location]  views or sets <obj>'s home location.
    /sweep <obj>  send obj home.
    /here  sets current character's home to current location.
    /room  returns a character to its home room, regardless of where home is set.
    
    The "home" location is a "safety" location for objects; they will be
    moved there if their current location ceases to exist. All objects
    should always have a home location for this reason.
    It is also a convenient target of the "home" command.
    """
    key = 'home'
    options = ('set', 'sweep', 'here', 'room')
    locks = 'cmd:all()'
    arg_regex = r"^/|\s|$"
    help_category = 'Travel'
    account_caller = True

    def func(self):
        """Implement the command"""
        you = self.character
        account = self.account
        opt = self.switches
        # you potentially has two homes.
        room = you.db.objects['home'] if you.db.objects and you.db.objects.get('home', False) else you.home
        home = room if 'room' in opt else you.home  # Or home room, to handle /room option
        if not opt or 'room' in opt:
            if not home:
                you.msg('You have no home yet.')
            elif home == you.location:
                you.msg('You are already home!')
            else:
                you.msg("There's no place like home ...")
                you.move_to(home, use_destination=False)
        else:
            if not self.args:
                obj = you
            else:
                obj = you.search(self.lhs, global_search=True)
            if not obj:
                return
            if 'sweep' in opt:
                home = obj.home
                if not home:
                    you.msg('%s has no home yet.' % obj.get_display_name(account))
                elif home == obj.location:
                    you.msg('%s is already home!' % obj.get_display_name(account))
                elif obj != you and not account.check_permstring('Helpstaff') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wHelpstaff|n or higher access to send %s home."
                            % obj.get_display_name(account))
                else:
                    obj.msg("There's no place like home ... (%s is sending you home.)" % you.get_display_name(obj))
                    if you.location:
                        you.location.msg_contents('%s%s|n sends %s%s|n home.'
                                                  % (you.STYLE, you.key, obj.STYLE, obj.key))
                    was = obj.location
                    obj.move_to(home, use_destination=False)
                    if you.location != was:
                        source_location_name = was.get_display_name(you) if was else '|222Nothingness|n'
                        you.msg("%s left %s and went home to %s."
                                % (obj.get_display_name(you), source_location_name, home.get_display_name(you)))
                return
            if not self.rhs and 'here' not in opt:  # just view the destination set as home
                if obj != you and not account.check_permstring('Helpstaff') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wHelpstaff|n or higher access to view the home of %s."
                            % obj.get_display_name(account))
                    return
                home = obj.home
                if not home:
                    string = "%s has no home location set!" % obj.get_display_name(you)
                else:
                    string = "%s's current home is %s." % (obj.get_display_name(you), home.get_display_name(you))
            else:  # set/change a home location
                if obj != you and not account.check_permstring('Mages') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wMages|n or higher access to change the home of %s." % obj)
                    return
                if self.rhs and 'here' not in opt:
                    new_home = you.search(self.rhs, global_search=True)
                else:
                    new_home = you.location
                if not new_home:
                    return
                old_home = obj.home
                obj.home = new_home
                if old_home:
                    string = "%s's home location was changed from %s to %s." % (obj, old_home.get_display_name(you),
                                                                                new_home.get_display_name(you))
                else:
                    string = "%s' home location was set to %s." % (obj, new_home.get_display_name(you))
            you.msg(string)
