# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
import datetime
from astral import Astral


class CmdAstral(MuxCommand):
    """
    Display astral info about location.
    Usage:
      astral [target]
    """
    key = 'astral'
    help_category = 'Information'
    locks = 'cmd:all()'
    account_caller = True

    def func(self):
        """Display information about server or target"""
        account = self.account
        city_name = 'Phoenix' if not self.args else self.args
        a = Astral()
        a.solar_depression = 'civil'
        city = a[city_name]
        if not city:
            return
        timezone = city.timezone
        sun = city.sun(date=datetime.date.today(), local=True)

        account.msg('Information for %s/%s\n' % (city_name, city.region))
        account.msg('Timezone: %s' % timezone)
        account.msg('Latitude: %.02f; Longitude: %.02f' % (city.latitude, city.longitude))
        account.msg('Dawn:    %s' % str(sun['dawn']))
        account.msg('Sunrise: %s' % str(sun['sunrise']))
        account.msg('Noon:    %s' % str(sun['noon']))
        account.msg('Sunset:  %s' % str(sun['sunset']))
        account.msg('Dusk:    %s' % str(sun['dusk']))
