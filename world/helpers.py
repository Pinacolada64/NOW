"""
Helpers

Methods that are helpful to have in a module.
"""


def make_bar(value, maximum, length, gradient):
    """Make a bar of length, of color value along the gradient."""
    maximum = float(maximum)
    length = float(length)
    value = min(float(value), maximum)
    if not value:
        return ''
    barcolor = gradient[max(0, (int(round((value / maximum) * len(gradient))) - 1))]
    rounded_percent = int(min(round((value / maximum) * length), length - 1))
    barstring = (("{:<%i}" % int(length)).format("%i / %i" % (int(value), int(maximum))))
    barstring = ("|555" + barcolor + barstring[:rounded_percent] + '|[011' + barstring[rounded_percent:])
    return barstring[:int(length) + 13] + "|n"


def mass_unit(value):
    """Present a suitable mass unit based on value"""
    if not value:
        return 'unknown'
    value = float(value)
    if value <= 0:
        return 'weightless'
    if value <= 999:
        return '%s g' % str(value).rstrip('0').rstrip('.')
    if value <= 999999:
        return '%s kg' % str(value/1000).rstrip('0').rstrip('.')
    if value <= 999999999:
        return '%s t' % str(value / 1000000).rstrip('0').rstrip('.')
    if value <= 999999999999:
        return '%s kt' % str(value / 1000000000).rstrip('0').rstrip('.')
    if value <= 999999999999999:
        return '%s Mt' % str(value / 1000000000000).rstrip('0').rstrip('.')
    else:
        return 'super massive'


def escape_braces(text):
    text = text if text else ''
    text = text.replace('{', '{{')
    text = text.replace('}', '}}')
    return text
