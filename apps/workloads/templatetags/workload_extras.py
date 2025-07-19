from django import template

register = template.Library()

@register.filter
def get_day_value(workload, day):
    """指定日の工数値を取得"""
    return workload.get_day_value(day)

@register.filter
def add(value, arg):
    """値を加算"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def mod(value, arg):
    """余り計算"""
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError):
        return 0