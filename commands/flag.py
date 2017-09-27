# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils import search, utils


class CmdFlag(MuxCommand):
    """
    Set flag on object.
    Usage:
      flag   shows flags on the current room.
      flag <object>  shows flags on that object.
      flag <object> = <flag>  sets flag on object.
    Options:
    /search  Search world for all objects with the given flag.
    /list  Shows a list of flags in use in the world.
    /info  Short information on given flags.
    /long  Show more information about flags on given object.
    """
    key = 'flag'
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'
    help_category = 'Building'
    account_caller = True
    FLAGS = {'street': 'cars can drive into here, can take taxi from here',
             'offroad': 'Same as "road" - but unpaved, slower speed',
             'outside': 'Object can land and ascend to/from sky',
             'weather': 'Custom weather occurs here, and can have effects.',
             'shelter': 'weather is observable here, but does not have effect.',
             'water': 'there is water here, but also air - ie. can breath.',
             'aquatic': 'there is water, no way to surface for air',
             'air': 'flight into here is allowed by fliers',
             'cloud': 'denser air type, might allow alternate travel',
             'public': 'anyone allowed here',
             'disk': 'a stepdisk room, can jump to any other stepdisk from here.',
             'haunt': 'a room that allows dark characters.',
             'diet': 'room has food available. You can not starve here.',
             'poll': 'a room or object that polls characters.',
             'contain': 'an object that acts as a container.',
             'stealth': 'room does not announce when someone enters or leaves.'}

#     myscript.tags.add("weather", category="climate")

    def func(self):
        """ """
        char = self.character
        here = char.location
        account = self.account
        cmd = self.cmdstring
        args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        opt = self.switches
        opt_list = [u'list', u'info', u'long', u'search']

        if not all(x in opt_list for x in opt):
            account.msg("Not a valid switch for |y%s|n. Use only these: |g/%s" % (cmd, "|n, |g/".join(opt_list)))
            return
        if not opt or 'long' in opt:
            obj = here
            if not lhs:
                if not here:
                    account.msg("No flag can be put on this location. Trying flags on %s%s|n/" % (char.STYLE, char.key))
                    obj = char
            else:
                obj = char.search(lhs, location=[char, char.location]) if args else here
                if not obj:
                    return
            flags_obj = obj.tags.all(category='flags')
            flags_obj_count = len(flags_obj)
            if flags_obj:  # returns a list of flags
                if 'long' in opt:
                    account.msg('Flag list on %s: (%s): ' % (obj.get_display_name(account), flags_obj_count))
                    for flag in flags_obj:
                        account.msg('|c%s: |w%s|n|/' % (flag, self.FLAGS[flag]))
                else:
                    account.msg('Flag list on %s: (%s) = |c%s' %
                               (obj.get_display_name(account), flags_obj_count, "|n, |c".join(a for a in flags_obj)))
            else:
                account.msg('Flag list is not found on %s.' % obj.get_display_name(account))
            if rhs:  # If something is on the right hand side!
                good_flag = [x for x in self.FLAGS if x in rhs]
                overlap = [x for x in good_flag if x in flags_obj]
                to_set = [x for x in good_flag if x not in overlap]
                if overlap:
                    is_one = abs(len(overlap)) == 1
                    plural = '' if is_one else 's'
                    account.msg('Flag%s already set: |y%s' % (plural, "|n, |y".join(a for a in overlap)))
                is_one = abs(len(to_set)) == 1
                plural = '' if is_one else 's'
                account.msg('Set flag%s: |g%s' % (plural, "|n, |g".join(a for a in to_set)))
        if 'list' in opt:
            account.msg('Displaying list of ' + ('|ymatching' if args else '|gall') + '|n flags:')
            if args:  # Show list of matching flags
                match_list = [x for x in self.FLAGS if x in args]  # This match is not "starts with" or partial.
                account.msg('|c%s' % "|n, |c".join(match_list))
            else:
                account.msg('|c%s' % "|n, |c".join(a for a in self.FLAGS))
        if 'info' in opt:
            good_flag = [x for x in self.FLAGS if x in args] if args else self.FLAGS
            account.msg('Displaying info for ' + ('|ymatching' if args else '|gall') + '|n flags:')
            account.msg("|/".join('|c%s|n - |w%s' % (a, self.FLAGS[a]) for a in good_flag))
        if 'search' in opt:
            obj = search.search_tag(args, category='flags')
            object_count = len(obj)
            if object_count > 0:
                match_string = ", ".join(o.get_display_name(account) for o in obj)
                if args:
                    string = "Found |w%i|n object%s with the flag '|g%s|n' set:\n %s" %\
                             (object_count, "s" if object_count > 1 else '', args, match_string)
                else:
                    string = "Found |w%i|n object%s with any flag set:\n %s" % \
                             (object_count, "s" if object_count > 1 else '', match_string)
                account.msg(string)
            else:
                account.msg('Found no objects flagged: "|g%s"' % args)
