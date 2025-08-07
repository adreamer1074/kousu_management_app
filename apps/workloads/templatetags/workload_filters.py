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

@register.filter
def get_weekday_class(day, weekday_info):
    """指定日の曜日クラスを取得"""
    if not weekday_info or day not in weekday_info:
        return 'weekday'
    
    info = weekday_info[day]
    if info['is_holiday'] or info['is_sunday']:
        return 'holiday'
    elif info['is_saturday']:
        return 'saturday'
    else:
        return 'weekday'

@register.filter
def is_weekend_or_holiday(day, weekday_info):
    """週末または祝日かどうかを判定"""
    if not weekday_info or day not in weekday_info:
        return False
    
    info = weekday_info[day]
    return info['is_saturday'] or info['is_sunday'] or info['is_holiday']

@register.filter
def get_item(dictionary, key):
    """辞書から指定キーの値を取得"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}

@register.filter
def get_weekday_name(weekday):
    """曜日番号から曜日名を取得"""
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    if isinstance(weekday, int) and 0 <= weekday <= 6:
        return weekday_names[weekday]
    return ''

@register.filter
def get_day_class(day, weekday_info):
    """日付のCSSクラスを取得"""
    if not weekday_info or day not in weekday_info:
        return 'weekday'
    
    info = weekday_info[day]
    if info.get('is_holiday') or info.get('is_sunday'):
        return 'holiday'
    elif info.get('is_saturday'):
        return 'saturday'
    else:
        return 'weekday'