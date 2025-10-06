# 小説AI評価システム 基本設計書

## 1. システム概要

### 1.1 システム名
小説AI評価システム (Novel AI Evaluation System)

### 1.2 目的
「小説家になろう」などの小説投稿サイトから作品データを取得し、AI（ChatGPT等）を用いて自動評価を行い、評価基準に基づいて作品の合否判定を行うシステム。

### 1.3 主要機能
- 小説データのスクレイピング機能
- AI評価実行機能
- 評価基準設定機能
- 評価済み作品管理機能

---

## 2. システム構成

### 2.1 技術スタック
- **フロントエンド**: Next.js 15 (App Router), React, TypeScript
- **スタイリング**: Tailwind CSS v4
- **バックエンド**: Next.js API Routes / Server Actions
- **データベース**: PostgreSQL (Supabase / Neon 推奨)
- **AI**: OpenAI API (ChatGPT) / AI SDK
- **スクレイピング**: Cheerio / Puppeteer

### 2.2 アーキテクチャ
\`\`\`
┌─────────────────┐
│  フロントエンド   │
│   (Next.js)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  API Layer      │
│ (Server Actions)│
└────┬───────┬────┘
     │       │
┌────▼───┐ ┌▼──────┐
│   DB   │ │ AI API│
│(Postgres)│ │(OpenAI)│
└────────┘ └───────┘
\`\`\`

---

## 3. データベース設計

### 3.1 ER図概要
\`\`\`
novels (作品) ──< evaluations (評価結果)
                      │
evaluation_settings ──┘
(評価設定)
\`\`\`

### 3.2 テーブル定義

#### 3.2.1 novels (作品テーブル)
小説投稿サイトから取得した作品情報を保存

| カラム名 | 型 | NULL | 説明 |
|---------|-----|------|------|
| id | UUID | NOT NULL | 主キー |
| source_site | VARCHAR(255) | NOT NULL | 取得元サイト (例: syosetu.com) |
| source_url | TEXT | NOT NULL | 作品URL |
| title | VARCHAR(500) | NOT NULL | 作品タイトル |
| author | VARCHAR(255) | NOT NULL | 作者名 |
| summary | TEXT | NULL | あらすじ |
| trial_text | TEXT | NULL | 試し読みテキスト |
| character_count | INTEGER | NULL | 文字数 |
| genre | VARCHAR(100) | NULL | ジャンル |
| tags | TEXT[] | NULL | タグ配列 |
| scraped_at | TIMESTAMP | NOT NULL | 取得日時 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- PRIMARY KEY (id)
- INDEX idx_novels_source_url (source_url)
- INDEX idx_novels_created_at (created_at)

**制約:**
- UNIQUE (source_url)

---

#### 3.2.2 evaluation_settings (評価設定テーブル)
AI評価の基準と項目を管理

| カラム名 | 型 | NULL | 説明 |
|---------|-----|------|------|
| id | UUID | NOT NULL | 主キー |
| name | VARCHAR(255) | NOT NULL | 設定名 |
| stage | VARCHAR(100) | NOT NULL | 評価段階 (第一段階、第二段階等) |
| scope | VARCHAR(100) | NOT NULL | 評価範囲 (試し読み、全文等) |
| ai_model | VARCHAR(100) | NOT NULL | AIモデル (gpt-4o, claude-3等) |
| passing_score | INTEGER | NOT NULL | 合格ライン |
| is_active | BOOLEAN | NOT NULL | 有効フラグ |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- PRIMARY KEY (id)
- INDEX idx_evaluation_settings_is_active (is_active)

---

#### 3.2.3 evaluation_criteria (評価項目テーブル)
評価設定に紐づく個別の評価項目

| カラム名 | 型 | NULL | 説明 |
|---------|-----|------|------|
| id | UUID | NOT NULL | 主キー |
| setting_id | UUID | NOT NULL | 評価設定ID (FK) |
| order_index | INTEGER | NOT NULL | 表示順序 |
| criterion_name | VARCHAR(255) | NOT NULL | 評価項目名 |
| prompt | TEXT | NOT NULL | AIへのプロンプト |
| max_score | INTEGER | NOT NULL | 最大スコア |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- PRIMARY KEY (id)
- INDEX idx_evaluation_criteria_setting_id (setting_id)
- INDEX idx_evaluation_criteria_order (setting_id, order_index)

**外部キー:**
- FOREIGN KEY (setting_id) REFERENCES evaluation_settings(id) ON DELETE CASCADE

---

#### 3.2.4 evaluations (評価結果テーブル)
実行された評価の結果を保存

| カラム名 | 型 | NULL | 説明 |
|---------|-----|------|------|
| id | UUID | NOT NULL | 主キー |
| novel_id | UUID | NOT NULL | 作品ID (FK) |
| setting_id | UUID | NOT NULL | 評価設定ID (FK) |
| total_score | INTEGER | NOT NULL | 総合スコア |
| passing_score | INTEGER | NOT NULL | 合格ライン |
| is_passed | BOOLEAN | NOT NULL | 合否 |
| stage | VARCHAR(100) | NOT NULL | 評価段階 |
| evaluated_at | TIMESTAMP | NOT NULL | 評価実行日時 |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**インデックス:**
- PRIMARY KEY (id)
- INDEX idx_evaluations_novel_id (novel_id)
- INDEX idx_evaluations_is_passed (is_passed)
- INDEX idx_evaluations_evaluated_at (evaluated_at)

**外部キー:**
- FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
- FOREIGN KEY (setting_id) REFERENCES evaluation_settings(id) ON DELETE RESTRICT

---

#### 3.2.5 evaluation_details (評価詳細テーブル)
各評価項目ごとの詳細結果

| カラム名 | 型 | NULL | 説明 |
|---------|-----|------|------|
| id | UUID | NOT NULL | 主キー |
| evaluation_id | UUID | NOT NULL | 評価結果ID (FK) |
| criterion_id | UUID | NOT NULL | 評価項目ID (FK) |
| criterion_name | VARCHAR(255) | NOT NULL | 評価項目名 (スナップショット) |
| score | INTEGER | NOT NULL | スコア |
| max_score | INTEGER | NOT NULL | 最大スコア |
| confidence | INTEGER | NULL | 確信度 (1-10) |
| reason | TEXT | NULL | 評価理由 |
| ai_response | JSONB | NULL | AI応答の生データ |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |

**インデックス:**
- PRIMARY KEY (id)
- INDEX idx_evaluation_details_evaluation_id (evaluation_id)

**外部キー:**
- FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE
- FOREIGN KEY (criterion_id) REFERENCES evaluation_criteria(id) ON DELETE RESTRICT

---

## 4. API設計

### 4.1 作品データ取得API

#### POST /api/scraping/fetch
小説投稿サイトから作品データを取得

**リクエスト:**
\`\`\`json
{
  "sourceUrl": "https://syosetu.com/...",
  "workUrl": "https://syosetu.com/..."
}
\`\`\`

**レスポンス:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "作品タイトル",
    "author": "作者名",
    "summary": "あらすじ",
    "trialText": "試し読みテキスト",
    "characterCount": 50000
  }
}
\`\`\`

---

### 4.2 評価実行API

#### POST /api/evaluation/execute
AI評価を実行

**リクエスト:**
\`\`\`json
{
  "novelId": "uuid",
  "settingId": "uuid",
  "title": "作品タイトル",
  "stage": "第一段階",
  "scope": "試し読み",
  "aiModel": "gpt-4o"
}
\`\`\`

**レスポンス:**
\`\`\`json
{
  "success": true,
  "data": {
    "evaluationId": "uuid",
    "totalScore": 58,
    "passingScore": 40,
    "isPassed": true,
    "details": [
      {
        "criterionName": "評価1",
        "score": 9,
        "maxScore": 10,
        "confidence": 10,
        "reason": "テキストテキストテキスト"
      }
    ]
  }
}
\`\`\`

---

### 4.3 評価設定API

#### GET /api/settings
評価設定一覧を取得

**レスポンス:**
\`\`\`json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "第一段階評価",
      "stage": "第一段階",
      "scope": "試し読み",
      "aiModel": "gpt-4o",
      "passingScore": 40,
      "criteria": [
        {
          "id": "uuid",
          "criterionName": "評価項目1",
          "prompt": "プロンプト内容",
          "maxScore": 10
        }
      ]
    }
  ]
}
\`\`\`

#### POST /api/settings
評価設定を作成

**リクエスト:**
\`\`\`json
{
  "name": "第一段階評価",
  "stage": "第一段階",
  "scope": "試し読み",
  "aiModel": "gpt-4o",
  "passingScore": 40,
  "criteria": [
    {
      "criterionName": "評価項目1",
      "prompt": "プロンプト内容",
      "maxScore": 10
    }
  ]
}
\`\`\`

#### PUT /api/settings/:id
評価設定を更新

#### DELETE /api/settings/:id
評価設定を削除

---

### 4.4 評価済み作品API

#### GET /api/results
評価済み作品一覧を取得

**クエリパラメータ:**
- `page`: ページ番号 (デフォルト: 1)
- `limit`: 取得件数 (デフォルト: 20)
- `stage`: 評価段階でフィルタ
- `isPassed`: 合否でフィルタ (true/false)

**レスポンス:**
\`\`\`json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "novelTitle": "作品名",
        "author": "作者名",
        "stage": "第一段階",
        "totalScore": 32,
        "passingScore": 40,
        "isPassed": false,
        "evaluatedAt": "2025-09-26T17:25:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "totalPages": 5
    }
  }
}
\`\`\`

#### GET /api/results/:id
評価詳細を取得

**レスポンス:**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "uuid",
    "novel": {
      "title": "作品名",
      "author": "作者名",
      "summary": "あらすじ"
    },
    "totalScore": 58,
    "passingScore": 40,
    "isPassed": true,
    "details": [
      {
        "criterionName": "評価1",
        "score": 9,
        "maxScore": 10,
        "confidence": 10,
        "reason": "評価理由テキスト"
      }
    ]
  }
}
\`\`\`

---

## 5. 画面設計

### 5.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| P01 | 作品データ取得画面 | /scraping | 小説サイトから作品データを取得 |
| P02 | AI評価画面 | /evaluation | AI評価を実行 |
| P03 | 評価設定画面 | /settings | 評価基準と項目を設定 |
| P04 | 評価済み作品一覧画面 | /results | 評価結果を一覧表示 |

---

### 5.2 P01: 作品データ取得画面

**機能:**
- 取得サイトURLの入力
- 作品URLの入力
- データ取得実行
- 取得結果の表示（タイトル、作者名、あらすじ、試し読みテキスト、文字数）

**主要コンポーネント:**
- URLインプットフィールド × 2
- 取得ボタン
- 結果表示カード

**バリデーション:**
- URL形式チェック
- 必須項目チェック

---

### 5.3 P02: AI評価画面

**機能:**
- 作品タイトル入力
- 評価段階選択
- 評価範囲選択
- AIモデル選択
- 評価実行
- 評価結果表示（各項目の確信度、スコア、評価理由）

**主要コンポーネント:**
- フォーム入力フィールド
- セレクトボックス
- 評価実行ボタン
- 評価結果カード（複数）

**処理フロー:**
1. フォーム入力
2. 評価設定の取得
3. AI APIへのリクエスト送信
4. 結果の解析と保存
5. 結果表示

---

### 5.4 P03: 評価設定画面

**機能:**
- 評価段階の選択（タブ切り替え）
- 評価項目の追加・編集・削除
- 各項目のプロンプト設定
- スコア上限設定
- 総合計スコア表示
- 合格ラインの設定

**主要コンポーネント:**
- タブナビゲーション
- 評価項目リスト（動的追加可能）
- インプットフィールド（項目名、プロンプト、スコア上限）
- 追加ボタン
- スコア表示エリア

**バリデーション:**
- 項目名必須
- プロンプト必須
- スコア上限は正の整数
- 合格ラインは総合計スコア以下

---

### 5.5 P04: 評価済み作品一覧画面

**機能:**
- 評価済み作品の一覧表示
- フィルタリング（評価段階、合否）
- ソート機能
- ページネーション
- 詳細表示へのリンク

**主要コンポーネント:**
- データテーブル
- フィルタコントロール
- ページネーションコントロール

**表示項目:**
- 作品名
- 評価段階
- 評価スコア
- 合否

---

## 6. セキュリティ設計

### 6.1 認証・認可
- 将来的にSupabase Authを使用した認証機能の実装を推奨
- Row Level Security (RLS) によるデータアクセス制御

### 6.2 データ保護
- 環境変数によるAPIキーの管理
- HTTPS通信の強制
- SQLインジェクション対策（パラメータ化クエリ）
- XSS対策（入力値のサニタイズ）

### 6.3 レート制限
- AI API呼び出しのレート制限
- スクレイピングのレート制限（サイトへの負荷軽減）

---

## 7. パフォーマンス設計

### 7.1 キャッシング戦略
- 評価設定のクライアントサイドキャッシュ（SWR）
- 評価結果一覧のページネーション

### 7.2 非同期処理
- AI評価の非同期実行（長時間処理対応）
- スクレイピングの非同期実行

### 7.3 最適化
- データベースインデックスの適切な設定
- N+1クエリの回避
- 画像の遅延読み込み

---

## 8. エラーハンドリング

### 8.1 エラー種別
- **バリデーションエラー**: 入力値の不正
- **ネットワークエラー**: API通信失敗
- **スクレイピングエラー**: サイト構造変更、アクセス拒否
- **AI APIエラー**: レート制限、モデルエラー
- **データベースエラー**: 接続失敗、制約違反

### 8.2 エラー表示
- トースト通知による非侵襲的なエラー表示
- フォームフィールドごとのバリデーションエラー表示
- エラーログの記録

---

## 9. 今後の拡張性

### 9.1 機能拡張
- 複数サイト対応（カクヨム、アルファポリス等）
- 評価履歴の比較機能
- 評価レポートのエクスポート（PDF、CSV）
- 評価の再実行機能
- 作品のブックマーク機能

### 9.2 技術的拡張
- バックグラウンドジョブキュー（Vercel Queues）
- リアルタイム通知（WebSocket）
- マルチテナント対応
- 管理者ダッシュボード

---

## 10. 運用設計

### 10.1 デプロイ
- Vercelへのデプロイ
- 環境変数の設定（本番/開発）
- データベースマイグレーション

### 10.2 監視
- エラーログの監視
- API使用量の監視
- データベースパフォーマンスの監視

### 10.3 バックアップ
- データベースの定期バックアップ
- 評価設定のエクスポート機能

---

## 付録A: データベースマイグレーションSQL

\`\`\`sql
-- novels テーブル作成
CREATE TABLE novels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_site VARCHAR(255) NOT NULL,
  source_url TEXT NOT NULL UNIQUE,
  title VARCHAR(500) NOT NULL,
  author VARCHAR(255) NOT NULL,
  summary TEXT,
  trial_text TEXT,
  character_count INTEGER,
  genre VARCHAR(100),
  tags TEXT[],
  scraped_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_novels_source_url ON novels(source_url);
CREATE INDEX idx_novels_created_at ON novels(created_at);

-- evaluation_settings テーブル作成
CREATE TABLE evaluation_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  stage VARCHAR(100) NOT NULL,
  scope VARCHAR(100) NOT NULL,
  ai_model VARCHAR(100) NOT NULL,
  passing_score INTEGER NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evaluation_settings_is_active ON evaluation_settings(is_active);

-- evaluation_criteria テーブル作成
CREATE TABLE evaluation_criteria (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  setting_id UUID NOT NULL REFERENCES evaluation_settings(id) ON DELETE CASCADE,
  order_index INTEGER NOT NULL,
  criterion_name VARCHAR(255) NOT NULL,
  prompt TEXT NOT NULL,
  max_score INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evaluation_criteria_setting_id ON evaluation_criteria(setting_id);
CREATE INDEX idx_evaluation_criteria_order ON evaluation_criteria(setting_id, order_index);

-- evaluations テーブル作成
CREATE TABLE evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
  setting_id UUID NOT NULL REFERENCES evaluation_settings(id) ON DELETE RESTRICT,
  total_score INTEGER NOT NULL,
  passing_score INTEGER NOT NULL,
  is_passed BOOLEAN NOT NULL,
  stage VARCHAR(100) NOT NULL,
  evaluated_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evaluations_novel_id ON evaluations(novel_id);
CREATE INDEX idx_evaluations_is_passed ON evaluations(is_passed);
CREATE INDEX idx_evaluations_evaluated_at ON evaluations(evaluated_at);

-- evaluation_details テーブル作成
CREATE TABLE evaluation_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
  criterion_id UUID NOT NULL REFERENCES evaluation_criteria(id) ON DELETE RESTRICT,
  criterion_name VARCHAR(255) NOT NULL,
  score INTEGER NOT NULL,
  max_score INTEGER NOT NULL,
  confidence INTEGER,
  reason TEXT,
  ai_response JSONB,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evaluation_details_evaluation_id ON evaluation_details(evaluation_id);

-- updated_at自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_novels_updated_at BEFORE UPDATE ON novels
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evaluation_settings_updated_at BEFORE UPDATE ON evaluation_settings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evaluation_criteria_updated_at BEFORE UPDATE ON evaluation_criteria
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
\`\`\`

---

## 付録B: 環境変数一覧

\`\`\`env
# Database
DATABASE_URL=postgresql://...

# AI API
OPENAI_API_KEY=sk-...
XAI_API_KEY=...
GROQ_API_KEY=...

# Application
NEXT_PUBLIC_APP_URL=https://...
NODE_ENV=production

# Supabase (将来的な認証用)
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
\`\`\`

---

**文書バージョン**: 1.0  
**作成日**: 2025-09-30  
**最終更新日**: 2025-09-30
