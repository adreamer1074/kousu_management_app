from django.contrib import admin
from .models import Project, ProjectMember, ProjectPhase

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'priority', 'manager', 'start_date', 'end_date', 'is_active']
    list_filter = ['status', 'priority', 'department', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'client', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'join_date', 'leave_date', 'is_active']
    list_filter = ['role', 'is_active', 'join_date']
    search_fields = ['project__name', 'user__username', 'role']

@admin.register(ProjectPhase)
class ProjectPhaseAdmin(admin.ModelAdmin):
    list_display = ['project', 'name', 'start_date', 'end_date', 'order', 'is_completed']
    list_filter = ['is_completed', 'start_date']
    search_fields = ['project__name', 'name']
    ordering = ['project', 'order']