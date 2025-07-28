from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db.models import Count, Q
from django.db import models, transaction
from django.core.exceptions import PermissionDenied
from .models import CustomUser, Department, Section
from .forms import CustomUserCreationForm, UserEditForm, ProfileEditForm, DepartmentForm, SectionForm, SuperUserEditForm
import logging
import json


logger = logging.getLogger(__name__)

def is_staff_or_superuser(user):
    """リーダーまたはスーパーユーザーかどうかを判定"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_superuser)
def register(request):
    """ユーザー登録ビュー（完全自動ログイン防止版）"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 現在のログインユーザーを確実に保存
            original_user = request.user
            original_user_id = original_user.id
            original_session_key = request.session.session_key
            
            logger.info(f"Before save: User={original_user.username}, ID={original_user_id}")
            
            # ユーザーを作成
            try:
                # commit=Falseで作成してから手動保存
                new_user = form.save(commit=False)
                new_user.created_by = original_user
                new_user.save()
                
                # 保存後のセッション状態を確認
                current_user_after_save = request.user
                logger.info(f"After save: User={current_user_after_save.username}, ID={current_user_after_save.id}")
                
                # セッションが変更された場合は強制復元
                if request.user.id != original_user_id:
                    logger.warning(f"Session hijacked! Restoring from {request.user.username} to {original_user.username}")
                    
                    # 完全にセッションをクリアして再ログイン
                    logout(request)
                    
                    # 元のユーザーで再ログイン
                    login(request, original_user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    # 再度確認
                    if request.user.id == original_user_id:
                        logger.info(f"Session successfully restored to: {request.user.username}")
                    else:
                        logger.error(f"Session restoration failed! Current: {request.user.username}")
                
                messages.success(
                    request, 
                    f'ユーザー「{new_user.username}」を作成しました。現在のログイン: {request.user.username}'
                )
                
                # リダイレクト前に再度セッション確認
                final_user = request.user
                logger.info(f"Before redirect: User={final_user.username}, ID={final_user.id}")
                
                # ユーザー一覧にリダイレクト（詳細画面ではなく）
                return redirect('users:user_list')
                
            except Exception as e:
                logger.error(f"Error during user creation: {e}")
                messages.error(request, f'ユーザー作成エラー: {e}')
        else:
            logger.warning(f"Form is invalid: {form.errors}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/user/user_register.html', {'form': form})

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """ユーザー一覧ビュー"""
    model = CustomUser
    template_name = 'users/user/user_list.html'
    context_object_name = 'users'
    paginate_by = 50
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        # すべてのユーザー（アクティブ・非アクティブ両方）を取得
        queryset = CustomUser.objects.select_related('department', 'section').order_by('-is_active', 'username')
        
        # 検索パラメータがある場合
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # 部署フィルター
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department__name=department)
            
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'staff':
            queryset = queryset.filter(is_staff=True)
        elif status == 'superuser':
            queryset = queryset.filter(is_superuser=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True).order_by('name')
        
        # デバッグ情報を追加
        all_users = CustomUser.objects.all()
        active_users = all_users.filter(is_active=True)
        inactive_users = all_users.filter(is_active=False)
        
        context['debug_info'] = {
            'total_users': all_users.count(),
            'active_users': active_users.count(),
            'inactive_users': inactive_users.count(),
        }
        
        return context

class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/user/user_detail.html'
    context_object_name = 'user_obj'

    def dispatch(self, request, *args, **kwargs):
        """リクエスト処理前にパラメータを確認"""
        pk = kwargs.get('pk')
        current_user = request.user
        
        logger.info(f"UserDetailView - Current user: {current_user.username} (ID: {current_user.id})")
        logger.info(f"UserDetailView - Requested user pk: {pk}")
        
        # pkが存在しない場合のチェック
        if not pk:
            logger.error("No pk provided in URL")
            messages.error(request, "ユーザーIDが指定されていません。")
            return redirect('users:user_list')
        
        # 存在確認
        try:
            target_user = CustomUser.objects.get(pk=pk)
            logger.info(f"UserDetailView - Target user: {target_user.username} (ID: {target_user.id})")
        except CustomUser.DoesNotExist:
            logger.error(f"User with pk {pk} does not exist")
            messages.error(request, "指定されたユーザーが見つかりません。")
            return redirect('users:user_list')
        
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """URLパラメータから明示的にオブジェクトを取得"""
        pk = self.kwargs.get('pk')
        
        if queryset is None:
            queryset = self.get_queryset()
        
        try:
            obj = queryset.get(pk=pk)
            logger.info(f"get_object - Retrieved user: {obj.username} (ID: {obj.id})")
            return obj
        except queryset.model.DoesNotExist:
            logger.error(f"get_object - User with pk {pk} not found")
            raise Http404("ユーザーが見つかりません")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 現在のログインユーザーと表示対象ユーザーを明確に分離
        current_user = self.request.user
        target_user = self.object
        
        logger.info(f"Context - Current login user: {current_user.username} (ID: {current_user.id})")
        logger.info(f"Context - Display target user: {target_user.username} (ID: {target_user.id})")
        
        # 権限判定は現在のログインユーザーで行う
        context['can_edit'] = current_user.is_superuser or current_user.is_staff
        context['can_delete'] = current_user.is_superuser
        context['current_login_user'] = current_user
        context['is_own_profile'] = current_user.id == target_user.id
        
        return context

class UserEditView(LoginRequiredMixin, UpdateView):
    """ユーザー編集ビュー"""
    model = CustomUser
    form_class = UserEditForm
    template_name = 'users/user/user_edit.html'
    context_object_name = 'user_obj'
    
    def dispatch(self, request, *args, **kwargs):
        """アクセス権限をチェック"""
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'この操作を実行する権限がありません。')
            return redirect('users:user_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """編集対象のユーザーを取得"""
        obj = super().get_object(queryset)
        
        # スーパーユーザーのみが他のスーパーユーザーを編集可能
        if obj.is_superuser and not self.request.user.is_superuser:
            messages.error(self.request, 'スーパーユーザーの編集には、スーパーユーザー権限が必要です。')
            return redirect('users:user_list')
        
        return obj
    
    def get_form_class(self):
        """編集対象に応じてフォームクラスを選択"""
        user_obj = self.get_object()
        
        # スーパーユーザーが編集する場合は完全版フォーム
        if self.request.user.is_superuser:
            return SuperUserEditForm
        # リーダーが一般ユーザーを編集する場合
        elif self.request.user.is_staff and not user_obj.is_superuser:
            return UserEditForm
        else:
            return UserEditForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # 編集可能かどうかの判定
        context['can_edit_permissions'] = (
            self.request.user.is_superuser or 
            (self.request.user.is_staff and not user_obj.is_superuser)
        )
        context['can_edit_basic_info'] = True
        context['is_editing_superuser'] = user_obj.is_superuser
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'ユーザー「{form.instance.username}」の情報を更新しました。')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('users:user_detail', kwargs={'pk': self.object.pk})

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile/profile.html'

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'users/profile/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'プロフィールを更新しました。')
        return super().form_valid(form)

# 部署管理
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'users/department/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.annotate(
            user_count=Count('users', filter=models.Q(users__is_active=True)),
            section_count=Count('sections', filter=models.Q(sections__is_active=True))
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total': Department.objects.count(),
            'active': Department.objects.filter(is_active=True).count(),
            'inactive': Department.objects.filter(is_active=False).count(),
        }
        return context

class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'users/department/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.get_object()
        context['sections'] = department.sections.filter(is_active=True)
        context['users'] = department.users.filter(is_active=True)
        return context

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'users/department/department_form.html'
    success_url = reverse_lazy('users:department_list')

    def form_valid(self, form):
        messages.success(self.request, f'部署「{form.instance.name}」を作成しました。')
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'users/department/department_form.html'
    success_url = reverse_lazy('users:department_list')

    def form_valid(self, form):
        messages.success(self.request, f'部署「{form.instance.name}」を更新しました。')
        return super().form_valid(form)

class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Department
    template_name = 'users/department/department_delete.html'
    success_url = reverse_lazy('users:department_list')

    def delete(self, request, *args, **kwargs):
        department = self.get_object()
        messages.success(request, f'部署「{department.name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# 課管理
class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'users/section/section_list.html'
    context_object_name = 'sections'

    def get_queryset(self):
        return Section.objects.select_related('department').annotate(
            user_count=Count('users', filter=models.Q(users__is_active=True))
        ).order_by('department__name', 'name')

class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = 'users/section/section_detail.html'
    context_object_name = 'section'

class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'users/section/section_form.html'
    success_url = reverse_lazy('users:section_list')

    def form_valid(self, form):
        messages.success(self.request, f'課「{form.instance.name}」を作成しました。')
        return super().form_valid(form)

class SectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'users/section/section_form.html'
    success_url = reverse_lazy('users:section_list')

    def form_valid(self, form):
        messages.success(self.request, f'課「{form.instance.name}」を更新しました。')
        return super().form_valid(form)

class SectionDeleteView(LoginRequiredMixin, DeleteView):
    model = Section
    template_name = 'users/section/section_delete.html'
    success_url = reverse_lazy('users:section_list')

    def delete(self, request, *args, **kwargs):
        section = self.get_object()
        messages.success(request, f'課「{section.name}」を削除しました。')
        return super().delete(request, *args, **kwargs)

# AJAX
def load_sections(request):
    """部署IDに基づいて課を取得するAJAX"""
    department_id = request.GET.get('department_id')
    sections = Section.objects.filter(department_id=department_id, is_active=True).order_by('name')
    return JsonResponse(list(sections.values('id', 'name')), safe=False)

def custom_logout(request):
    """カスタムログアウトビュー（GETとPOSTの両方に対応）"""
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('login')

@login_required
@user_passes_test(is_staff_or_superuser)
def user_create(request):
    """ユーザー作成（registerのエイリアス）"""
    return register(request)  # registerに転送

@login_required
def user_detail_debug(request, pk):
    """デバッグ用ユーザー詳細ビュー"""
    # ログ出力
    logger.info(f"DEBUG - Request user: {request.user.username} (ID: {request.user.id})")
    logger.info(f"DEBUG - URL pk parameter: {pk}")
    
    # ユーザーを明示的に取得
    try:
        target_user = CustomUser.objects.get(pk=pk)
        logger.info(f"DEBUG - Target user found: {target_user.username} (ID: {target_user.id})")
    except CustomUser.DoesNotExist:
        logger.error(f"DEBUG - User with pk {pk} not found")
        messages.error(request, "ユーザーが見つかりません。")
        return redirect('users:user_list')
    
    # コンテキストを明示的に作成
    context = {
        'user_obj': target_user,
        'current_login_user': request.user,
        'requested_pk': pk,
        'can_edit': request.user.is_superuser or request.user.is_staff,
        'can_delete': request.user.is_superuser,
        'debug_info': {
            'request_user': request.user.username,
            'request_user_id': request.user.id,
            'target_user': target_user.username,
            'target_user_id': target_user.id,
            'url_pk': pk,
        }
    }
    
    return render(request, 'users/user/user_detail_debug.html', context)

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """ユーザー削除ビュー"""
    model = CustomUser
    template_name = 'users/user/user_delete.html'
    success_url = reverse_lazy('users:user_list')
    
    def test_func(self):
        # スーパーユーザーのみ削除可能
        return self.request.user.is_superuser
    
    def get_object(self, queryset=None):
        user = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        
        # 自分自身の削除を防止
        if user == self.request.user:
            messages.error(self.request, '自分自身を削除することはできません。')
            return redirect('users:user_list')
        
        # スーパーユーザーの削除を防止（他のスーパーユーザーでも）
        if user.is_superuser:
            messages.error(self.request, 'スーパーユーザーを削除することはできません。')
            return redirect('users:user_list')
        
        return user
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        username = user.username
        
        try:
            # ソフト削除（is_activeをFalseにする）
            user.is_active = False
            user.save()
            
            messages.success(request, f'ユーザー「{username}」を無効化しました。')
        except Exception as e:
            messages.error(request, f'ユーザーの削除に失敗しました: {str(e)}')
        
        return redirect(self.success_url)

@login_required
@require_POST
def user_delete_ajax(request):
    """AJAX ユーザー削除"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '権限がありません。'})
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'ユーザーIDが指定されていません。'})
        
        user = get_object_or_404(CustomUser, pk=user_id)
        
        # 自分自身の削除を防止
        if user == request.user:
            return JsonResponse({'success': False, 'error': '自分自身を削除することはできません。'})
        
        # スーパーユーザーの削除を防止
        if user.is_superuser:
            return JsonResponse({'success': False, 'error': 'スーパーユーザーを削除することはできません。'})
        
        username = user.username
        
        # ソフト削除
        user.is_active = False
        user.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'ユーザー「{username}」を無効化しました。'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'削除に失敗しました: {str(e)}'})

@login_required
@require_POST 
def user_restore_ajax(request):
    """AJAX ユーザー復元"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '権限がありません。'})
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        user = get_object_or_404(CustomUser, pk=user_id)
        username = user.username
        
        # ユーザーを復元
        user.is_active = True
        user.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'ユーザー「{username}」を復元しました。'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'復元に失敗しました: {str(e)}'})

class UserPermanentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """ユーザー完全削除ビュー（物理削除）"""
    model = CustomUser
    template_name = 'users/user/user_permanent_delete.html'
    success_url = reverse_lazy('users:user_list')
    
    def test_func(self):
        # スーパーユーザーのみ完全削除可能
        return self.request.user.is_superuser
    
    def get_object(self, queryset=None):
        user = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        
        # 自分自身の削除を防止
        if user == self.request.user:
            messages.error(self.request, '自分自身を完全削除することはできません。')
            raise PermissionDenied('自分自身を削除することはできません。')
        
        # アクティブなスーパーユーザーの削除を防止
        if user.is_superuser and user.is_active:
            messages.error(self.request, 'アクティブなスーパーユーザーを完全削除することはできません。先に無効化してください。')
            raise PermissionDenied('アクティブなスーパーユーザーは削除できません。')
        
        return user
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        username = user.username
        user_id = user.id
        
        try:
            with transaction.atomic():
                # 関連データの確認とクリーンアップ
                workload_count = user.workload_set.count() if hasattr(user, 'workload_set') else 0
                project_count = user.assigned_projects.count() if hasattr(user, 'assigned_projects') else 0
                
                # 関連データがある場合は警告
                if workload_count > 0 or project_count > 0:
                    logger.warning(f"Deleting user {username} with related data: "
                                 f"{workload_count} workloads, {project_count} projects")
                
                # 物理削除実行
                user.delete()
                
                logger.info(f"User permanently deleted: {username} (ID: {user_id}) by {request.user.username}")
                messages.success(request, 
                    f'ユーザー「{username}」を完全削除しました。'
                    f'（関連する工数データ: {workload_count}件、プロジェクト: {project_count}件も削除されました）')
                
        except Exception as e:
            logger.error(f"Failed to permanently delete user {username}: {str(e)}")
            messages.error(request, f'ユーザーの完全削除に失敗しました: {str(e)}')
        
        return redirect(self.success_url)

@login_required
@require_POST
def user_permanent_delete_ajax(request):
    """AJAX ユーザー完全削除"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '権限がありません。'})
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        confirm_text = data.get('confirm_text', '')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'ユーザーIDが指定されていません。'})
        
        user = get_object_or_404(CustomUser, pk=user_id)
        username = user.username
        
        # 確認テキストの検証
        if confirm_text.upper() != 'DELETE':
            return JsonResponse({'success': False, 'error': '確認テキストが正しくありません。「DELETE」と入力してください。'})
        
        # 自分自身の削除を防止
        if user == request.user:
            return JsonResponse({'success': False, 'error': '自分自身を完全削除することはできません。'})
        
        # アクティブなスーパーユーザーの削除を防止
        if user.is_superuser and user.is_active:
            return JsonResponse({'success': False, 'error': 'アクティブなスーパーユーザーを完全削除することはできません。先に無効化してください。'})
        
        try:
            with transaction.atomic():
                # 関連データ数を取得
                workload_count = user.workload_set.count() if hasattr(user, 'workload_set') else 0
                project_count = user.assigned_projects.count() if hasattr(user, 'assigned_projects') else 0
                
                # 物理削除実行
                user.delete()
                
                logger.info(f"User permanently deleted via AJAX: {username} (ID: {user_id}) by {request.user.username}")
                
                return JsonResponse({
                    'success': True, 
                    'message': f'ユーザー「{username}」を完全削除しました。'
                              f'（工数データ: {workload_count}件、プロジェクト: {project_count}件も削除）'
                })
                
        except Exception as e:
            logger.error(f"Failed to permanently delete user {username} via AJAX: {str(e)}")
            return JsonResponse({'success': False, 'error': f'完全削除に失敗しました: {str(e)}'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSONデータの解析に失敗しました。'})
    except Exception as e:
        logger.error(f"Permanent delete AJAX error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'完全削除処理でエラーが発生しました: {str(e)}'})

@login_required
@require_POST
def cleanup_inactive_users(request):
    """非アクティブユーザーの一括完全削除"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '権限がありません。'})
    
    try:
        data = json.loads(request.body)
        days_threshold = data.get('days_threshold', 365)  # デフォルト1年
        confirm_text = data.get('confirm_text', '')
        
        if confirm_text.upper() != 'CLEANUP':
            return JsonResponse({'success': False, 'error': '確認テキストが正しくありません。「CLEANUP」と入力してください。'})
        
        from datetime import datetime, timedelta
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        
        # 削除対象ユーザーを取得
        target_users = CustomUser.objects.filter(
            is_active=False,
            is_superuser=False,
            last_login__lt=threshold_date
        ).exclude(
            id=request.user.id  # 自分自身は除外
        )
        
        deleted_count = 0
        deleted_users = []
        
        try:
            with transaction.atomic():
                for user in target_users:
                    username = user.username
                    workload_count = user.workload_set.count() if hasattr(user, 'workload_set') else 0
                    
                    deleted_users.append({
                        'username': username,
                        'workload_count': workload_count,
                        'last_login': user.last_login.strftime('%Y-%m-%d') if user.last_login else 'なし'
                    })
                    
                    user.delete()
                    deleted_count += 1
                
                logger.info(f"Bulk cleanup: {deleted_count} inactive users deleted by {request.user.username}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'{deleted_count}名の非アクティブユーザーを完全削除しました。',
                    'deleted_users': deleted_users,
                    'deleted_count': deleted_count
                })
                
        except Exception as e:
            logger.error(f"Bulk cleanup failed: {str(e)}")
            return JsonResponse({'success': False, 'error': f'一括削除に失敗しました: {str(e)}'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSONデータの解析に失敗しました。'})
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return JsonResponse({'success': False, 'error': f'クリーンアップ処理でエラーが発生しました: {str(e)}'})