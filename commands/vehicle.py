# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia import CmdSet


class VehicleCmdSet(CmdSet):
    key = 'vehicle'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the vehicle object (item or room)."""
        self.add(CmdVehicle())


class CmdVehicleDefault(MuxCommand):
    """Add command to the set - this set will be attached to the vehicle object (item or room)."""
    key = 'vehicle'
    locks = 'cmd:all()'
    help_category = 'Travel'
    account_caller = True

    def send_msg(self, message):
        """Send message internal and external to vehicle and optionally move vehicle."""
        char = self.character
        where = self.obj
        outside = where.location
        where.msg_contents(message, exclude=char)
        outside.msg_contents(message, exclude=char)


class CmdVehicle(CmdVehicleDefault):
    """
    Operate various aspects of the vehicle as configured.
    Usage:
      vehicle  display other commands available.
    """
    aliases = 'operate'

    def func(self):
        """ """
        cmd = self.cmdstring
        opt = self.switches
        args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        char = self.character
        where = self.obj
        here = char.location
        outside = where.location
        account = self.account
        setting = where.db.settings or {}
        if 'vehicle' in cmd:
            account.msg('|wCommand list for %s%s|n:|/|C%s' % (where.STYLE, where.key, '|n, |C'.join(self.aliases)))
        if 'operate' in cmd:
            if 'list' in opt:
                if not where.db.settings:
                    where.db.settings = {}
                account.msg('Listing %s%s|n control panel settings: |g%s'
                           % (where.STYLE, where.key, '|n, |g'.join('%s|n: |c%s' % (each, where.db.settings[each])
                                                                    for each in where.db.settings)))
                return
            if 'on' in opt or 'off' in opt or 'toggle' in opt or 'set' in opt:
                action = opt[0]
                if action == 'on':
                    action = 'engage'
                    setting[args] = True
                elif action == 'off':
                    action = 'disengage'
                    setting[args] = False
                elif action == 'set':
                    action = 'dial'
                    setting[lhs] = rhs
                else:
                    setting[args] = False if where.db.settings and args in where.db.settings\
                                             and where.db.settings[args] else True
                if 'set' in opt and rhs:
                    message = '|g%s|n %ss %s to %s on %s%s|n control panel.' % \
                              (char.key, action, lhs if lhs else 'something', rhs, where.STYLE, where.key)
                else:
                    message = '|g%s|n %ss %s on %s%s|n control panel.' %\
                              (char.key, action, args if args else 'something', where.STYLE, where.key)
                if not here == where:
                    outside.msg_contents(message)
                where.msg_contents(message)
                where.db.settings = setting
                return
            self.send_msg("%s%s|n commands in-operable %s%s|n vehicle to %s." %
                          (char.STYLE, char.key, where.STYLE, where.key, args))
            account.msg("%s%s|n commands in-operable %s%s|n vehicle to %s." %
                       (char.STYLE, char.key, where.STYLE, where.key, args))
            self.send_msg("%s%s|n does nothing." % (where.STYLE, where.key))
            account.msg("%s%s|n does nothing." % (where.STYLE, where.key))
