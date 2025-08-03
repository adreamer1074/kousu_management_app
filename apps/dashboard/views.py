from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange

from apps.core.decorators import (
    leader_or_superuser_required_403,
    LeaderOrSuperuserRequiredMixin
)
from apps.reports.models import WorkloadAggregation
from apps.workloads.models import Workload 
from apps.projects.models import Project, Case
from apps.cost_master.models import OutsourcingCost

@login_required
@leader_or_superuser_required_403
def admin_dashboard(request):
    """管理者ダッシュボード"""
    
    # 現在の日付情報
    now = timezone.now()
    current_month = now.strftime('%Y年%m月')
    first_day_of_month = now.replace(day=1)
    last_month_first_day = (first_day_of_month - timedelta(days=1)).replace(day=1)
    last_month_last_day = first_day_of_month - timedelta(days=1)
    
    try:
        # === 基本統計 ===
        # 総工数登録数（実際の工数入力データ + 工数集計データ）
        workload_count = Workload.objects.count() if hasattr(Workload, 'objects') else 0
        aggregation_count = WorkloadAggregation.objects.count()
        total_workload_entries = workload_count + aggregation_count
        
        # 進行中チケット数
        active_tickets_count = WorkloadAggregation.objects.filter(
            status__in=['planning', 'in_progress'],
            case_name__isnull=False
        ).count()
        
        # 期限超過チケット数
        overdue_tickets_count = WorkloadAggregation.objects.filter(
            planned_end_date__lt=now.date(),
            status__in=['planning', 'in_progress'],
            case_name__isnull=False
        ).count()
        
        # === 収益統計（正確なデータ取得） ===
        print("=== 収益統計計算開始 ===")
        
        # WorkloadAggregationから収益データを取得
        revenue_query = WorkloadAggregation.objects.all()
        print(f"総レコード数: {revenue_query.count()}")
        
        # 各項目の合計を個別に計算
        total_billing = revenue_query.aggregate(
            total=Sum('billing_amount_excluding_tax')
        )['total'] or 0
        
        total_outsourcing = revenue_query.aggregate(
            total=Sum('outsourcing_cost_excluding_tax')
        )['total'] or 0
        
        print(f"総請求金額（税抜）: ¥{total_billing:,}")
        print(f"総外注費（税抜）: ¥{total_outsourcing:,}")
        
        # 万円単位に変換
        total_revenue = total_billing / 10000  # 万円単位
        total_outsourcing_cost = total_outsourcing / 10000  # 万円単位
        gross_profit = total_revenue - total_outsourcing_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"総請求金額（万円）: ¥{total_revenue:,.1f}")
        print(f"総外注費（万円）: ¥{total_outsourcing_cost:,.1f}")
        print(f"粗利益（万円）: ¥{gross_profit:,.1f}")
        print(f"利益率: {profit_margin:.1f}%")
        
        # === 今月の工数統計 ===
        # 今月の工数集計データ
        this_month_aggregation = WorkloadAggregation.objects.filter(
            created_at__gte=first_day_of_month
        ).aggregate(
            total_workdays=Sum('used_workdays'),
            count=Count('id')
        )
        
        # 実際の工数入力データ（もしWorkloadモデルが存在する場合）
        try:
            this_month_workload = Workload.objects.filter(
                work_date__gte=first_day_of_month.date(),
                work_date__lte=now.date()
            ).aggregate(
                total_hours=Sum('hours')
            )
            this_month_hours = this_month_workload['total_hours'] or 0
            this_month_workdays_from_workload = this_month_hours / 8.0  # 8時間=1日
        except:
            this_month_workdays_from_workload = 0
        
        # 合計工数
        this_month_workdays = (this_month_aggregation['total_workdays'] or 0) + this_month_workdays_from_workload
        
        # 今月の営業日数計算
        working_days_this_month = 0
        current_date = first_day_of_month.date()
        while current_date <= now.date():
            if current_date.weekday() < 5:  # 平日のみ
                working_days_this_month += 1
            current_date += timedelta(days=1)
        
        # 1日平均工数
        avg_daily_workdays = this_month_workdays / working_days_this_month if working_days_this_month > 0 else 0
        
        # === 前月比較 ===
        # 前月の工数集計データ
        last_month_aggregation = WorkloadAggregation.objects.filter(
            created_at__gte=last_month_first_day,
            created_at__lte=last_month_last_day
        ).aggregate(
            total_workdays=Sum('used_workdays')
        )
        
        # 前月の工数入力データ
        try:
            last_month_workload = Workload.objects.filter(
                work_date__gte=last_month_first_day.date(),
                work_date__lte=last_month_last_day.date()
            ).aggregate(
                total_hours=Sum('hours')
            )
            last_month_hours = last_month_workload['total_hours'] or 0
            last_month_workdays_from_workload = last_month_hours / 8.0
        except:
            last_month_workdays_from_workload = 0
        
        last_month_workdays = (last_month_aggregation['total_workdays'] or 0) + last_month_workdays_from_workload
        
        # 前月比成長率
        workdays_growth = ((this_month_workdays - last_month_workdays) / last_month_workdays * 100) if last_month_workdays > 0 else 0
        
        # === 目標達成率 ===
        monthly_target_workdays = working_days_this_month * 0.8  # 1日0.8人日を目標
        target_achievement = (this_month_workdays / monthly_target_workdays * 100) if monthly_target_workdays > 0 else 0
        
        # === チケットステータス別統計（正確なデータ取得） ===
        print("=== チケットステータス別統計計算開始 ===")
        
        ticket_status_stats = []
        
        # case_nameがあるもので、ステータス別に集計
        status_query = WorkloadAggregation.objects.filter(
            case_name__isnull=False
        )
        
        print(f"チケット対象レコード数: {status_query.count()}")
        
        status_data = status_query.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('billing_amount_excluding_tax')
        ).order_by('-total_amount')
        
        # ステータス別の色設定
        status_colors = {
            'planning': 'secondary',
            'in_progress': 'primary', 
            'testing': 'info',
            'completed': 'success',
            'on_hold': 'warning',
            'cancelled': 'danger',
            'pending': 'secondary',
            'review': 'info',
            'approved': 'success',
            'rejected': 'danger'
        }
        
        # ステータス別表示名の設定
        status_display_names = {
            'planning': '企画中',
            'in_progress': '進行中',
            'testing': 'テスト中',
            'completed': '完了',
            'on_hold': '保留',
            'cancelled': 'キャンセル',
            'pending': '承認待ち',
            'review': 'レビュー中',
            'approved': '承認済み',
            'rejected': '却下'
        }
        
        for item in status_data:
            status_value = item['status']
            count = item['count']
            amount = item['total_amount'] or 0
            
            print(f"ステータス: {status_value}, 件数: {count}, 金額: ¥{amount:,}")
            
            # 表示名を取得
            try:
                # まず定義済みの表示名を確認
                if status_value in status_display_names:
                    display_name = status_display_names[status_value]
                else:
                    # サンプルインスタンスから取得を試行
                    sample_instance = WorkloadAggregation.objects.filter(
                        status=status_value
                    ).first()
                    
                    if sample_instance and hasattr(sample_instance, 'get_status_display'):
                        display_name = sample_instance.get_status_display()
                    else:
                        display_name = str(status_value).replace('_', ' ').title()
            except Exception as e:
                print(f"ステータス表示名取得エラー ({status_value}): {e}")
                display_name = str(status_value).replace('_', ' ').title()
            
            ticket_status_stats.append({
                'name': display_name,
                'count': count,
                'total_amount': amount / 10000,  # 万円単位
                'color': status_colors.get(status_value, 'secondary')
            })
        
        print(f"チケットステータス統計: {len(ticket_status_stats)}件")
        
        # === 最近の工数登録 ===
        recent_workload_entries = []
        
        # 工数集計データから最近の登録を取得
        recent_aggregations = WorkloadAggregation.objects.select_related(
            'case_name'
        ).order_by('-created_at')[:5]
        
        for aggregation in recent_aggregations:
            recent_workload_entries.append({
                'project_name': aggregation.project_name or '未設定',
                'case_name': {
                    'title': aggregation.case_name.title if aggregation.case_name else '未設定'
                },
                'used_workdays': aggregation.used_workdays or 0,
                'created_at': aggregation.created_at
            })
        
        # === 注意が必要なチケット ===
        attention_tickets = []
        
        # 期限超過チケット
        try:
            overdue_tickets = WorkloadAggregation.objects.filter(
                planned_end_date__lt=now.date(),
                status__in=['planning', 'in_progress'],
                case_name__isnull=False
            ).select_related('case_name')[:3]
            
            for ticket in overdue_tickets:
                days_overdue = (now.date() - ticket.planned_end_date).days
                
                try:
                    if hasattr(ticket, 'get_status_display'):
                        status_display = ticket.get_status_display()
                    else:
                        status_display = status_display_names.get(ticket.status, ticket.status)
                except:
                    status_display = str(ticket.status)
                
                attention_tickets.append({
                    'ticket_title': ticket.case_name.title if ticket.case_name else '未設定',
                    'project_name': ticket.project_name,
                    'reason': f'予定終了日を{days_overdue}日超過',
                    'alert_level': 'danger',
                    'status_display': status_display,
                    'days_overdue': days_overdue
                })
        except Exception as e:
            print(f"期限超過チケット取得エラー: {e}")
        
        # 締切間近のチケット（3日以内）
        try:
            upcoming_deadline_tickets = WorkloadAggregation.objects.filter(
                planned_end_date__gte=now.date(),
                planned_end_date__lte=now.date() + timedelta(days=3),
                status__in=['planning', 'in_progress'],
                case_name__isnull=False
            ).select_related('case_name')[:2]
            
            for ticket in upcoming_deadline_tickets:
                days_until = (ticket.planned_end_date - now.date()).days
                
                try:
                    if hasattr(ticket, 'get_status_display'):
                        status_display = ticket.get_status_display()
                    else:
                        status_display = status_display_names.get(ticket.status, ticket.status)
                except:
                    status_display = str(ticket.status)
                
                attention_tickets.append({
                    'ticket_title': ticket.case_name.title if ticket.case_name else '未設定',
                    'project_name': ticket.project_name,
                    'reason': f'あと{days_until}日で予定終了',
                    'alert_level': 'warning',
                    'status_display': status_display
                })
        except Exception as e:
            print(f"締切間近チケット取得エラー: {e}")
    
    except Exception as e:
        print(f"ダッシュボードデータ取得エラー: {e}")
        import traceback
        traceback.print_exc()
        
        # デフォルト値を設定
        total_workload_entries = 0
        active_tickets_count = 0
        total_revenue = 0
        overdue_tickets_count = 0
        this_month_workdays = 0
        avg_daily_workdays = 0
        workdays_growth = 0
        target_achievement = 0
        ticket_status_stats = []
        recent_workload_entries = []
        attention_tickets = []
        total_outsourcing_cost = 0
        gross_profit = 0
        profit_margin = 0
    
    # デバッグ情報をコンソールに出力
    # print("=== ダッシュボードコンテキスト ===")
    # print(f"総工数登録数: {total_workload_entries}")
    # print(f"進行中チケット: {active_tickets_count}")
    # print(f"総請求金額: ¥{total_revenue:.1f}万円")
    # print(f"総外注費: ¥{total_outsourcing_cost:.1f}万円")
    # print(f"粗利益: ¥{gross_profit:.1f}万円")
    # print(f"利益率: {profit_margin:.1f}%")
    # print(f"チケットステータス統計数: {len(ticket_status_stats)}")
    
    context = {
        'title': '管理者ダッシュボード',
        'current_month': current_month,
        # 基本統計
        'total_workload_entries': total_workload_entries,
        'active_tickets_count': active_tickets_count,
        'total_revenue': total_revenue,
        'overdue_tickets_count': overdue_tickets_count,
        # 工数統計
        'this_month_workdays': this_month_workdays,
        'avg_daily_workdays': avg_daily_workdays,
        'workdays_growth': workdays_growth,
        'target_achievement': target_achievement,
        # チケット統計
        'ticket_status_stats': ticket_status_stats,
        # 最近の活動
        'recent_workload_entries': recent_workload_entries,
        'attention_tickets': attention_tickets,
        # 収益サマリー
        'total_outsourcing_cost': total_outsourcing_cost,
        'gross_profit': gross_profit,
        'profit_margin': profit_margin,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)