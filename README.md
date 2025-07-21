# 工数管理アプリ (Workload Management Application)

このプロジェクトは、工数管理アプリケーションの開発を目的としています。以下は、プロジェクトの概要と構成です。

## 技術スタック
- **バックエンド**: Django
- **フロントエンド**: HTML, CSS, JavaScript
- **データベース**: MySQL
- **認証**: Django標準認証 + 部署別権限管理

## 画面構成
1. ログイン画面
2. 案件リスト登録画面
3. 工数登録画面 (カレンダー形式)
4. 工数集計画面 (フィルター・検索機能付き)
5. 外注費登録画面
6. 料金マスタ
7. レポート出力画面
8. 管理者画面 (ユーザー・案件管理)

## データベース設計
- `auth_group`               : 権限グループ管理
- `auth_group_permissions`   : グループ権限割当
- `auth_permission`          : 権限情報
- `users_customuser`         : カスタムユーザー(login users)
- `users_department`         : 部署管理
- `users_section`            : 課管理
- `projects_project`         : 案件管理
- `project_details`          : 案件詳細
- `projects_projectticket`   : チケット管理
- `workloads`                : 工数入力

**未実装**
- `external_costs`           : 外注費管理
- `workload_filters`         : 工数集計フィルター設定
- `workload_search_history`  : 工数集計検索履歴
- `report_exports`           : レポート出力ログ
- `cost_master`              : 単価・費用マスタ
- `workload_summaries`       : 工数集計


## 機能仕様
- ユーザー認証機能
- 管理者画面の機能(CRUD ユーザー・案件管理)
- 所属管理機能（CRUD 部署・課の管理）
- 案件管理機能(CRUD project-ticket)
- 工数登録画面の機能(カレンダー形式での工数入力)
**未実装**
- 工数集計機能(CRUD 工数集計)
- 外注費登録画面の機能(CRUD 外注費管理)
- 料金マスタの機能(CRUD 単価・費用マスタ)
- レポート出力画面の機能(CRUD レポート出力)
- レポート出力ログ機能(CRUD レポート出力ログ)

## インストールとセットアップ
1. リポジトリをクローンします。
2. 必要なパッケージをインストールします。
   ```
   pip install -r requirements.txt
   ```
3. データベースのマイグレーションを実行します。
   ```
   python manage.py migrate
   ```
4. スーパーユーザーを作成します。
   ```
   python manage.py createsuperuser
   ```
5. 開発サーバーを起動します。
   ```
   python manage.py runserver
   ```

## 使用方法
- アプリケーションにアクセスするには、ブラウザで `http://127.0.0.1:8000` に移動します。

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。