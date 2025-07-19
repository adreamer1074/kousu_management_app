from django.contrib.auth.models import AbstractUser
from django.db import models

class Department(models.Model):
    """部署モデル"""
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="部署名"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="説明"
    )
    manager = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name="マネージャー"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="アクティブ"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="作成日時"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新日時"
    )

    class Meta:
        verbose_name = "部署"
        verbose_name_plural = "部署"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def user_count(self):
        """所属ユーザー数を返す"""
        return self.users.filter(is_active=True).count()

class CustomUser(AbstractUser):
    """カスタムユーザーモデル"""
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="所属部署"
    )
    
    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"
    
    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    # Additional profile fields can be added here

    def __str__(self):
        return self.user.username