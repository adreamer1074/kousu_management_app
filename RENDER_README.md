# Kousu Management App - Render.com デプロイガイド

## デプロイ手順

### 1. Render.comでの設定

#### Web Service作成
1. Render.comにログイン
2. "New Web Service"を選択
3. GitHubリポジトリを接続

#### 設定項目

| 項目 | 値 |
|------|-----|
| **Name** | `kousu-management-app` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python manage.py makemigrations` |
| **Start Command** | `python manage.py migrate && python manage.py create_admin && python manage.py collectstatic --noinput && gunicorn kousu_management_app.wsgi:application` |

``` bash
#コマンド説明
python manage.py migrate &&                    # データベース更新
python manage.py create_admin &&               # 管理ユーザー自動作成
python manage.py collectstatic --noinput &&    # 静的ファイル収集
gunicorn kousu_management_app.wsgi:application  # アプリ起動
```

#### 環境変数の設定

以下の環境変数を設定してください：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `DJANGO_SETTINGS_MODULE` | `kousu_management_app.settings_render` | Render用設定ファイル |
| `SECRET_KEY` |  |  |
| `PYTHON_VERSION` | `3.9.0` | Pythonバージョン |

**重要**: `SECRET_KEY`は上記の例をそのまま使わず、必ず新しいキーを生成してください！
##### SECRET_KEYの生成方法：
```bash
# 方法1: Djangoコマンドで生成
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 方法2: オンラインジェネレーター
# https://djecrety.ir/
```

## ファイル構成

```
kousu_management_app/
├── requirements.txt               # Render用依存関係
├── requirements.render.txt        # Render専用依存関係
└── kousu_management_app/
    └── settings_render.py         # Render用設定
```

## 参考リンク

- [Render.com Django デプロイガイド](https://render.com/docs/deploy-django)
- [Django デプロイチェックリスト](https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/)
https://your-app-name.onrender.com/admin/


