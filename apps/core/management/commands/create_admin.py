"""
管理ユーザー自動作成コマンド
使用方法: python manage.py create_admin
"""

from django.core.management.base import BaseCommand
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = '管理ユーザー(admin/admin)を自動作成します'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin'

        try:
            # 既存のadminユーザーをチェック
            if CustomUser.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'ユーザー "{username}" は既に存在します')
                )
                return

            # スーパーユーザーを作成
            user = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )

            self.stdout.write(
                self.style.SUCCESS(f'スーパーユーザー "{username}" を作成しました')
            )
            self.stdout.write(f'ユーザー名: {username}')
            self.stdout.write(f'パスワード: {password}')
            self.stdout.write(
                self.style.WARNING('⚠️  本番環境では必ずパスワードを変更してください！')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'ユーザー作成エラー: {e}')
            )