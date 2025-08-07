
import calendar
from datetime import datetime, date
import jpholiday

def get_calendar_info(year, month):
    """カレンダー情報を取得（曜日、土日祝日判定）"""
    calendar_info = {}
    
    # その月の日数を取得
    _, last_day = calendar.monthrange(year, month)
    
    for day in range(1, last_day + 1):
        target_date = date(year, month, day)
        weekday = target_date.weekday()  # 0=月曜, 6=日曜
        
        # 曜日名（短縮形）
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        weekday_name = weekday_names[weekday]
        
        # 土日祝日判定
        is_saturday = weekday == 5  # 土曜日
        is_sunday = weekday == 6    # 日曜日
        is_holiday = jpholiday.is_holiday(target_date)  # 祝日
        
        # CSSクラス決定
        css_class = ''
        if is_holiday or is_sunday:
            css_class = 'holiday-cell'  # 祝日・日曜日（薄い赤）
        elif is_saturday:
            css_class = 'saturday-cell'  # 土曜日（薄い青）
        else:
            css_class = 'weekday-cell'  # 平日
        
        calendar_info[day] = {
            'weekday': weekday,
            'weekday_name': weekday_name,
            'is_saturday': is_saturday,
            'is_sunday': is_sunday,
            'is_holiday': is_holiday,
            'css_class': css_class,
            'display_text': f"{day}{weekday_name}"
        }
    
    return calendar_info