from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def is_superuser(user):
    """管理者権限チェック"""
    return user.is_authenticated and user.is_superuser

def is_leader_or_superuser(user):
    """リーダーまたは管理者権限チェック"""
    return user.is_authenticated and (user.is_leader or user.is_superuser)

def is_active_user(user):
    """アクティブユーザーチェック"""
    return user.is_authenticated and user.is_active

# デコレータ定義（403エラーを返す）
def superuser_required_403(function):
    """管理者権限チェック - 403エラーを返す"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        if not is_superuser(request.user):
            return HttpResponseForbidden("このページは管理者のみアクセス可能です。")
        
        return function(request, *args, **kwargs)
    return wrapper

def leader_or_superuser_required_403(function):
    """リーダー・管理者権限チェック - 403エラーを返す"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        if not is_leader_or_superuser(request.user):
            return HttpResponseForbidden("このページにアクセスする権限がありません。")
        
        return function(request, *args, **kwargs)
    return wrapper

# 従来のリダイレクト版デコレータ（ホームページが存在する場合）
superuser_required = user_passes_test(
    is_superuser,
    login_url='/'  # ホームページにリダイレクト
)

leader_or_superuser_required = user_passes_test(
    is_leader_or_superuser,
    login_url='/'  # ホームページにリダイレクト
)

active_user_required = user_passes_test(
    is_active_user,
    login_url='users:login'
)

# クラスベースビュー用Mixin（403エラーを返す）
class SuperuserRequiredMixin(UserPassesTestMixin):
    """管理者権限が必要なMixin - 403エラーを返す"""
    
    def test_func(self):
        return is_superuser(self.request.user)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return HttpResponseForbidden("このページは管理者のみアクセス可能です。")

class LeaderOrSuperuserRequiredMixin(UserPassesTestMixin):
    """リーダーまたは管理者権限が必要なMixin - 403エラーを返す"""
    
    def test_func(self):
        return is_leader_or_superuser(self.request.user)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return HttpResponseForbidden("このページにアクセスする権限がありません。")

class ActiveUserRequiredMixin(UserPassesTestMixin):
    """アクティブユーザー権限が必要なMixin"""
    
    def test_func(self):
        return is_active_user(self.request.user)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return HttpResponseForbidden("アカウントが無効です。管理者にお問い合わせください。")