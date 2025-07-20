from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """除算フィルター"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

