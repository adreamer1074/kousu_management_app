import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class SessionTimeoutMiddleware:
    """セッションタイムアウトとセキュリティ管理のためのミドルウェア"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ログインページなどの認証不要ページはスキップ
        if not request.user.is_authenticated:
            response = self.get_response(request)
            return response
            
        # 非アクティブタイムアウトのチェック
        if self.check_inactive_timeout(request):
            return self.handle_timeout(request, 'inactive')
        
        # セッションハイジャック対策
        if self.check_session_security(request):
            return self.handle_timeout(request, 'security')
        
        # 最後のアクティビティ時間を更新
        self.update_last_activity(request)
        
        response = self.get_response(request)
        return response

    def check_inactive_timeout(self, request):
        """非アクティブタイムアウトをチェック"""
        inactive_timeout = getattr(settings, 'INACTIVE_TIMEOUT_MINUTES', 120) * 60  # 分を秒に変換
        last_activity = request.session.get('last_activity')
        
        if last_activity:
            current_time = time.time()
            if current_time - last_activity > inactive_timeout:
                logger.warning(f"ユーザー {request.user.username} が非アクティブタイムアウトでログアウト")
                return True
        
        return False

    def check_session_security(self, request):
        """セッションのセキュリティをチェック（IP変更検出など）"""
        # IPアドレスの変更をチェック
        current_ip = self.get_client_ip(request)
        session_ip = request.session.get('session_ip')
        
        if session_ip and session_ip != current_ip:
            logger.warning(f"ユーザー {request.user.username} のIPアドレスが変更されました: {session_ip} → {current_ip}")
            # 開発環境では警告のみ、本番環境では強制ログアウト
            if settings.DEBUG:
                # 開発環境では新しいIPを記録して続行
                request.session['session_ip'] = current_ip
                return False
            else:
                # 本番環境では強制ログアウト
                return True
        
        # 初回アクセス時はIPを記録
        if not session_ip:
            request.session['session_ip'] = current_ip
        
        return False

    def handle_timeout(self, request, reason):
        """タイムアウト処理"""
        username = request.user.username
        
        # ログアウト実行
        logout(request)
        
        # タイムアウト理由に応じたメッセージ
        if reason == 'inactive':
            messages.warning(request, 
                'セキュリティのため、一定時間非アクティブだったためログアウトしました。\n'
                'お手数ですが、再度ログインしてください。')
            logger.info(f"ユーザー {username} が非アクティブタイムアウトでログアウト")
        elif reason == 'security':
            messages.error(request, 
                'セキュリティ上の理由によりログアウトしました。\n'
                'お心当たりがない場合は、システム管理者にご相談ください。')
            logger.warning(f"ユーザー {username} がセキュリティ理由でログアウト")
        
        # ログインページにリダイレクト
        return redirect('login')

    def update_last_activity(self, request):
        """最後のアクティビティ時間を更新"""
        request.session['last_activity'] = time.time()
        
        # セッションデータのクリーンアップ（古いデータを削除）
        self.cleanup_session_data(request)

    def cleanup_session_data(self, request):
        """セッションデータのクリーンアップ"""
        # 古いセッションキーがあれば削除
        cleanup_keys = ['temp_data', 'old_session_key']
        for key in cleanup_keys:
            if key in request.session:
                del request.session[key]

    def get_client_ip(self, request):
        """クライアントのIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip