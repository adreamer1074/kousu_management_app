from django import template

register = template.Library()

@register.filter
def get_day_value(workload, day):
    """workloadから指定された日の工数を取得"""
    if workload and day:
        return workload.get_day_value(day)
    return 0.0

@register.filter
def div(value, arg):
    """除算フィルター"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0