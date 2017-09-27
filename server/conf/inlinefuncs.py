"""
Inlinefunc

Inline functions allow for direct conversion of text users mark in a
special way. Inlinefuncs are deactivated by default. To activate, add

    INLINEFUNC_ENABLED = True

to your settings file. The default inlinefuncs are found in
evennia.utils.inlinefunc.

In text, usage is straightforward:

{funcname([arg1,arg2,...]) text {/funcname

Example 1 (using the "pad" inlinefunc):
    "This is {pad(50,c,-) a center-padded text{/pad of width 50."
    ->
    "This is -------------- a center-padded text--------------- of width 50."

Example 2 (using "pad" and "time" inlinefuncs):
    "The time is {pad(30){time(){/time{/padright now."
    ->
    "The time is         Oct 25, 11:09         right now."

To add more inline functions, add them to this module, using
the following call signature:

    def funcname(text, *args, **kwargs)

where `text` is always the part between {funcname(args) and
{/funcname and the *args are taken from the appropriate part of the
call. If no {/funcname is given, `text` will be the empty string.

It is important that the inline function properly clean the
incoming `args`, checking their type and replacing them with sane
defaults if needed. If impossible to resolve, the unmodified text
should be returned. The inlinefunc should never cause a traceback.

While the inline function should accept **kwargs, the keyword is
never accepted as a valid call - this is only intended to be used
internally by Evennia, notably to send the `session` keyword to
the function; this is the session of the object viewing the string
and can be used to customize it to each session.

"""
from random import *  # For the usage, using random


def capitalize(text, *args, **kwargs):
    """Capitalizes the first character of the line."""
    return text.capitalize()


def usage(text, *args, **kwargs):
    """Verbally describes how busy an area is"""
    text += ' quiet' if random() > 0.5 else ' busy'
    return text


def annotate(text, *args, **kwargs):
    """session sees original, unless session is a screen reader.
    ex. $annotate(original, annotation) or
        $annotate(original) for no annotation."""
    session = kwargs.get('session')
    nargs = len(args)
    note = ''
    original = ''

    if nargs > 0:
        note = args[0]
        original = text
    return note if session.protocol_flags['SCREENREADER'] else original


def uni(text, *args, **kwargs):
    """session sees original, unless session uses unicode.
    ex. $uni(original, unicode) or
        $uni(original) for no annotation."""
    session = kwargs.get('session')
    nargs = len(args)
    u = ''
    o = ''

    if nargs > 0:
        u = unicode(args[0])
        o = text
    return u if session.protocol_flags['ENCODING'] == 'utf-8' else o


def affect(text, *args, **kwargs):
    """Affect in response"""
    session = kwargs.get('session')
    target = None
    if len(args) > 0:
        target = unicode(args[0])
    account = session.account
    character = session.get_puppet()
    if target == character:
        pass  # Trait of target(s) are possibly affected.
    trait = text + account.key + character.key

    return trait
