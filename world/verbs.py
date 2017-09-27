# -*- coding: utf-8 -*-
"""
class Verb

"""
from world.helpers import escape_braces


class VerbHandler:
    """
    class Verb

    A Verb contains methods that allow objects
    to act upon other objects in the world.

    doer, verb, object, preposition, indirect
        TODO: Parse these action forms:
        <verb> (assume subject is also object to make this work after checking for a singular verbable noun)
        <verb> <noun> (This works now)
        <verb> <article> <noun> (check noun for article list after removing possible articles)
        <verb> <preposition> <noun> (check verb for preposition list)
        <verb> <preposition> <article> <noun> (Do both of above)
        <verb> <preposition> <article> <noun> <preposition> <other noun> (look for second preposition options on verb)
        <verb> <preposition> <article> <noun> <preposition> <article> <other noun>

    """
    def __init__(self, subject, verb=None, object=None, preposition=None, indirect=None):
        self.s = subject
        self.v = verb
        self.o = object  # if object else subject
        self.p = preposition
        self.i = indirect
        if hasattr(self, self.v):
            getattr(self, verb)()
        else:
            self._default()

    def _default(self):
        self.s.msg('You {} {}.'.format(self.v, self.o))
        self.o.msg('{} tries to {} you.'.format(self.s, self.v))
        self.s.location.msg_contents('{subject} tries to %s {object}.' % self.v,
                                     mapping=dict(subject=self.s, object=self.o),
                                     exclude=[self.s, self.o])
        if self.o.db.messages and self.v in self.o.db.messages:
            self.s.location.msg_contents('{object} %s' % self.o.db.messages[self.v],
                                         mapping=dict(object=self.o))

    def destroy(self):
        """Implements destroying this object."""
        if not self.o.tags.get('pool'):
            pass
        if self.o.location is not None:
            self.o.location = None

    def drop(self):
        """Implements the attempt to drop this object."""
        self.s.account.execute_cmd('give/drop %s' % self.o.get_display_name(self.s, plain=True))

    def enter(self):
        if self.s.location == self.o:
            self.s.msg("You are already aboard %s." % self.o.get_display_name(self.s))
            return
        if self.o.location == self.s:
            self.s.msg("You cannot board %s while holding it." % self.o.get_display_name(self.s))
            return
        entry_message = None
        if self.o.db.messages and 'entry' in self.o.db.messages:
            entry_message = self.o.db.messages['entry']
        if entry_message:
            self.s.msg('%s%s|n %s' % (self.s.STYLE, self.s.key, entry_message))
        self.s.msg("You board %s." % self.o.get_display_name(self.s))
        if entry_message:
            self.o.msg_contents('%s%s|n %s' % (self.s.STYLE, self.s.key, entry_message), exclude=self.s)
        destination = self.o.destination.location if self.o.tags.get('portal', category='flags') else self.o
        self.s.move_to(destination)
        if entry_message:
            self.o.location.msg_contents('%s%s|n %s' % (self.s.STYLE, self.s.key, entry_message))

    def examine(self):
        self.s.account.execute_cmd('examine %s' % self.o.get_display_name(self.s, plain=True))

    def exit(self):
        if self.s.location != self.o:
            self.s.msg("You are not aboard %s." % self.o.get_display_name(self.s))
            return
        exit_message = None
        if self.o.db.messages and 'exit' in self.o.db.messages:
            exit_message = self.o.db.messages['exit']
        self.s.msg("You disembark %s." % self.o.get_display_name(self.s))
        if exit_message:
            self.s.location.msg_contents('%s%s|n %s' % (self.s.STYLE, self.s.key, exit_message), exclude=self.s)
            self.o.location.msg_contents('%s%s|n %s' % (self.s.STYLE, self.s.key, exit_message))
        self.s.move_to(self.o.location)
        if exit_message:
            self.s.msg('%s%s|n %s' % (self.s.STYLE, self.s.key, exit_message))

    def follow(self):
        """Set following agreement - caller follows character"""
        if self.o == self.s:
            self.s.msg('You decide to follow your heart.')
            return
        action = 'follow'
        if self.o.attributes.has('followers') and self.o.db.followers:
            if self.s in self.o.db.followers:
                self.o.db.followers.remove(self.s)
                action = 'stop following'
            else:
                self.o.db.followers.append(caller)
        else:
            self.o.db.followers = [self.s]
        color = 'g' if action == 'follow' else 'r'
        self.s.location.msg_contents('|%s%s|n decides to %s {follower}.'
                                     % (color, self.s.key, action), from_obj=self.s, mapping=dict(follower=self.o))

    def get(self):
        """Implements the attempt to get this object."""
        too_heavy, too_large = self.s.get_limit() < self.o.get_mass(), False
        pose = self.s.ndb.pose
        if self.s == self.o:
            self.s.msg("%sYou|n can't get yourself." % self.s.STYLE)
        elif self.o.location == self.s:
            self.s.msg("%sYou|n already have %s." % (self.s.STYLE, self.o.get_display_name(self.s)))
        elif too_heavy:
            self.s.msg("%sYou|n can't lift %s; it is too heavy." % (self.s.STYLE, self.o.get_display_name(self.s)))
        elif too_large:
            self.s.msg("%sYou|n can lift %s, but it is too large to carry." %
                       (self.s.STYLE, self.o.get_display_name(self.s)))
        elif self.o.move_to(self.s, quiet=True):
            self.s.location.msg_contents('%s|g%s|n gets {it}.' % (escape_braces(pose), self.s.key),
                                         from_obj=self.s, mapping=dict(it=self.o))
            self.o.at_get(self.s)  # calling hook method

    def puppet(self):
        self.s.account.execute_cmd('@ic %s' % self.o.get_display_name(self.s, plain=True))

    def read(self):
        """
        Implements the read command. This simply looks for an
        Attribute "readable_text" on the object and displays that.
        """
        pose = self.o.ndb.power_pose
        read_text = self.o.db.readable_text or self.o.db.desc_brief or self.o.db.desc
        if read_text:  # Attribute read_text is defined.
            self.s.location.msg_contents("%s |g{s}|n reads {o}." % pose,
                                         mapping=dict(s=self.s, o=self.o))
            string = read_text
        else:
            string = "There is nothing to read on %s." % self.o.get_display_name(self.s)
        self.s.msg(string)

    def ride(self):
        """Set riding agreement - caller rides character"""
        if self.o == self.s:
            return
        action = 'ride'
        if self.o.attributes.has('riders') and self.o.db.riders:
            if self.s in self.o.db.riders:
                self.o.db.riders.remove(self.s)
                action = 'stop riding'
            else:
                self.o.db.riders.append(self.s)
        else:
            self.o.db.riders = [self.s]
        # subject is/was riding self invalidate self.s riding anyone else in the room.
        for each in self.s.location.contents:
            if each == self.s or each == self.o or not each.db.riders or self.s not in each.db.riders:
                continue
            each.db.riders.remove(self.s)
        color = 'g' if action == 'ride' else 'r'
        self.s.location.msg_contents('|%s%s|n decides to %s {mount}.'
                                     % (color, self.s.key, action), from_obj=self.s, mapping=dict(mount=self.o))

    def view(self):
        return self.s.account.execute_cmd('look %s' % self.o.get_display_name(self.s, plain=True))
