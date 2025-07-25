from django.apps import AppConfig


class CostMasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cost_master'
    verbose_name = '外注費管理'
    
    def ready(self):
        """アプリ初期化時の処理"""
        # シグナルの登録など必要に応じて追加
        pass