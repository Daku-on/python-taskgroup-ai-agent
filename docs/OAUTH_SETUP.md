# Google OAuth認証 & SSO設定ガイド

## 🔐 概要

面接スケジューリングシステムでGoogle API（Calendar、Gmail、Meet）を利用するための認証設定について説明します。企業のGoogle Workspace環境でのSSO（Single Sign-On）対応も含みます。

## 🚀 Quick Setup（個人・開発用）

### 1. Google Cloud Console初期設定

```bash
# 1. Google Cloud Consoleアクセス
https://console.cloud.google.com/

# 2. 新しいプロジェクト作成
プロジェクト名: interview-scheduler
プロジェクトID: interview-scheduler-XXXXX
```

### 2. API有効化

```bash
# 以下のAPIを有効化（APIs & Services → Library）
✅ Google Calendar API
✅ Gmail API  
✅ Google People API（オプション）

# Google Meet APIは自動で有効化されます
```

### 3. OAuth同意画面設定

```bash
# APIs & Services → OAuth consent screen

# 外部ユーザータイプを選択（開発用）
User Type: External

# 必須情報入力
App name: Interview Scheduler
User support email: your-email@example.com
Developer contact: your-email@example.com

# スコープ追加
../auth/calendar
../auth/gmail.send
../auth/calendar.events
```

### 4. OAuth認証情報作成

```bash
# APIs & Services → Credentials → Create Credentials

Application type: Web application
Name: Interview Scheduler OAuth

# 承認済みJavaScript生成元
http://localhost:3000
http://localhost:5173

# 承認済みリダイレクトURI
http://localhost:8000/auth/callback
http://localhost:3000/auth/callback

# Downloadをクリック → credentials.jsonとして保存
```

### 5. 認証ファイル配置

```bash
# プロジェクトルートに配置
cp ~/Downloads/credentials.json ./credentials.json

# または手動でcredentials.example.jsonをコピー
cp credentials.example.json credentials.json
# → client_id, client_secretを編集
```

## 🏢 Google Workspace SSO設定（企業用）

### 1. 管理者による事前設定

**Google Admin Consoleでの設定（IT管理者が実行）:**

```bash
# 1. Google Admin Console アクセス
https://admin.google.com/

# 2. セキュリティ → API制御 → アプリアクセス制御
- OAuth アプリ名前許可リストに追加
- App ID: your-client-id.apps.googleusercontent.com

# 3. 必要なスコープを許可
✅ https://www.googleapis.com/auth/calendar
✅ https://www.googleapis.com/auth/gmail.send
✅ https://www.googleapis.com/auth/calendar.events
✅ https://www.googleapis.com/auth/userinfo.email
✅ https://www.googleapis.com/auth/userinfo.profile
```

### 2. 内部アプリとして設定

```bash
# OAuth同意画面設定変更
User Type: Internal（ドメイン内部ユーザーのみ）

# 対象ドメイン設定
Authorized domains: your-company.com

# 自動承認設定
Internal user consent: Auto-approve for internal users
```

### 3. SSO自動ログイン設定

**.envファイル設定:**

```bash
# Google Workspace SSO設定
GOOGLE_SSO_ENABLED=true
GOOGLE_SSO_DOMAIN=your-company.com
GOOGLE_SSO_AUTO_LOGIN=true
GOOGLE_ADMIN_EMAIL=admin@your-company.com

# 認証設定
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:3000
```

### 4. 高度なSSO設定

**企業ポリシー適用（optional）:**

```python
# src/auth/sso_config.py
SSO_CONFIG = {
    "domain_restriction": "your-company.com",
    "require_email_verification": True,
    "auto_create_users": True,
    "default_role": "user",
    "admin_domains": ["admin@your-company.com"],
    "session_timeout": 3600,  # 1時間
    "force_reauth_interval": 86400  # 24時間
}
```

## 🔧 トラブルシューティング

### よくあるエラーと解決法

#### 1. "redirect_uri_mismatch" エラー

```bash
# 原因: リダイレクトURIの不一致
# 解決: Google Cloud Consoleで正確なURIを設定

正しい設定:
http://localhost:8000/auth/callback  # 開発用
https://your-domain.com/auth/callback  # 本番用
```

#### 2. "access_blocked" エラー

```bash
# 原因: OAuth同意画面の未設定
# 解決: OAuth consent screenを適切に設定

必要な設定:
- App name, email設定
- Privacy policy URL（本番時）
- Scopes設定
```

#### 3. "insufficient_scope" エラー

```bash
# 原因: 必要なスコープが許可されていない
# 解決: スコープを追加してre-authorize

必要なスコープ:
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/calendar.events
```

### 4. SSO関連のトラブル

```bash
# Workspace管理者に確認すべき項目:

1. APIアクセスが有効化されているか
2. アプリが承認済みアプリリストにあるか  
3. 必要なスコープが許可されているか
4. ユーザーのAPIアクセス権限があるか
```

## 🌐 本番環境設定

### 1. 本番用OAuth設定

```bash
# 本番用リダイレクトURI追加
https://your-domain.com/auth/callback

# 本番用JavaScript origins
https://your-domain.com

# 環境変数設定
OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback
FRONTEND_URL=https://your-domain.com
```

### 2. セキュリティ強化

```bash
# .env設定（本番用）
OAUTH_SECURE_COOKIES=true
OAUTH_SAME_SITE=strict
SESSION_SECRET=your-secure-random-secret

# HTTPS必須設定
FORCE_HTTPS=true
HSTS_ENABLED=true
```

### 3. OAuth同意画面の公開

```bash
# Google Cloud Console → OAuth consent screen
Publishing status: In production

# 必須項目:
- Privacy Policy URL
- Terms of Service URL  
- App Domain verification
- Scopes justification
```

## 🔍 テスト用アカウント

### 開発中のテストアカウント追加

```bash
# OAuth consent screen → Test users
test1@your-domain.com
test2@your-domain.com
developer@your-domain.com

# 注意: External app + Development状態では、
# Test usersのみアクセス可能
```

## 📋 認証フロー詳細

### 1. 標準OAuth2フロー

```
1. ユーザーが「Googleでログイン」クリック
     ↓
2. Google認証ページへリダイレクト
     ↓
3. ユーザーが権限許可
     ↓
4. Authorization codeでコールバック
     ↓
5. Codeをaccess_tokenに交換
     ↓
6. API呼び出し可能状態
```

### 2. SSO自動ログインフロー

```
1. 社内ドメインからアクセス検出
     ↓
2. Google Workspace SSOページへ自動リダイレクト
     ↓
3. 企業認証（SAML/OIDC等）
     ↓
4. 権限自動承認（管理者設定済み）
     ↓
5. アプリへ自動ログイン完了
```

## 🚨 セキュリティベストプラクティス

### 1. 権限最小化

```bash
# 必要最小限のスコープのみ要求
calendar.readonly  # 読み取り専用可能な場合
gmail.send        # 送信のみ（読み取り不要）
```

### 2. トークン管理

```python
# トークンの安全な保存
- 暗号化してDB保存
- refresh_tokenの適切な管理
- 定期的なトークンローテーション
```

### 3. アクセス制御

```bash
# IP制限（企業環境）
- 社内IPからのみアクセス許可
- VPN経由のアクセス制御

# ドメイン制限
- 特定ドメインのユーザーのみ許可
```

## 📞 サポート

### Google Workspace管理者向け

```bash
# 管理者用設定チェックリスト
□ OAuth Appの承認
□ 必要スコープの許可  
□ ユーザーAPIアクセス権限
□ ドメイン設定確認
□ セキュリティポリシー確認
```

### 開発者向け

```bash
# 問題発生時の確認項目
□ credentials.jsonの配置確認
□ APIの有効化確認
□ スコープ設定確認
□ リダイレクトURI確認
□ ログの確認
```

---

このガイドに従って設定すれば、個人開発から企業のGoogle Workspace環境まで、安全で効率的なOAuth認証が利用できます。SSO設定により、企業内での採用システム導入が大幅に簡素化されます。