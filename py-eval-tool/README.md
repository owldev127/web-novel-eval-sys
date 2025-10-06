# 小説評価コマンドツール README

本ツールは、長文の小説データ（JSON）をモデルに投入し、章ごとの要約と作品全体の評価をJSONで出力するコマンドラインツールです。

## 特長（Purpose）
- 作品全体を評価（テンポ、キャラクター、文体、世界観、ターゲット適合度など）
- 長文の入力に対して、モデルのコンテキスト制限を超えないように自動でエピソードをグルーピング
- Claude 使用時は Map-Reduce 方式で分割レビュー→最終統合レビューを実行
- 出力は必ず JSON（スキーマは `prompts.py` の記述に準拠）

## 動作環境
- Python 3.12 以上を推奨

## インストール
```bash
# 仮想環境の作成（任意）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 依存関係のインストール
pip install -r requirements.txt
```

## 環境変数
各モデル毎に API キーとモデル名を `.env` もしくは環境変数で設定します（`llm.py` の `_load_config` を参照）。

- OpenAI
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`（例: `gpt-4o-mini` など）
- Anthropic（Claude）
  - `ANTHROPIC_API_KEY`
  - `ANTHROPIC_MODEL`（例: `claude-3-5-sonnet-20240620` など）
- Google Gemini
  - `GOOGLE_API_KEY`
  - `GEMINI_MODEL`
- Qwen
  - `QWEN_API_KEY`
  - `QWEN_MODEL`
- Phi（Hugging Face Inference）
  - `PHI_API_KEY`
  - `PHI_MODEL`
- DeepSeek
  - `DEEPSEEK_API_KEY`
  - `DEEPSEEK_MODEL`

`.env` の例:
```env
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
OPENAI_API_KEY=sk-openai-xxx
OPENAI_MODEL=gpt-4o-mini
# 以降、必要に応じて…
```

## 対応モデル（agent）
`eval.py` の `run(input_file: Path, agent: str)` および `ALL_MODELS` に準拠：
- `chatgpt`（OpenAI）
- `claude`（Anthropic）
- `gemini`（Google）
- `qwen`
- `phi`
- `deepseek`

## 入力ファイル（JSON 形式）
`input/xxx.json` のような JSON を想定。最低限 `episodes` 配列が必要で、各要素に `text` フィールドを含めます。

例：
```json
{
  "title": "作品タイトル",
  "episodes": [
    { "number": 1, "text": "第1話の本文…" },
    { "number": 2, "text": "第2話の本文…" }
  ]
}
```

## 出力ファイル
`eval.py` の `compute_output_path(input_path, agent)` により、入力パスを `output/<agent>/...` に変換して保存します。出力は JSON（モデル応答を抽出・検証後）です。

例：
```
input/input_16818792438679825898.json
→ output/claude/input_16818792438679825898.json
```

## エラー処理と制限
- レート制限（429）：`llm.py` では HTTP レベルの再試行を実装。必要に応じて待機を追加してください。
- コンテキスト上限：モデル毎に異なるため、長文は Claude の分割統合を推奨。
- JSON 抽出失敗：`extract_json_from_text` で ```json … ``` ブロック優先抽出→フォールバック。失敗時はエラーを返します。
- JSON スキーマ検証失敗：`EvalOut.model_validate` で検証し、詳細エラーを表示します。

## ディレクトリ構成（抜粋）
```
/home/icodex/Desktop/summarizer/
  ├─ input/                      # 入力 JSON
  ├─ output/                     # 出力 JSON（model 別サブフォルダ）
  ├─ eval.py                     # メインロジック（分割/実行/保存）
  ├─ llm.py                      # 各モデル呼び出し
  ├─ prompts.py                  # 評価用プロンプト（目的・出力形式）
  └─ requirements.txt            # 依存関係
```

## よくある質問（FAQ）
- Q: 入力がとても長いのですが？
  - A: Claude を使用し、分割→統合のフローを使うのが安定です。
- Q: 出力が JSON ではないと言われる
  - A: モデル応答に説明文が混ざると抽出に失敗します。`prompts.py` は「JSONのみ出力」を強制していますが、モデルの挙動次第で失敗することがあります。その場合は再実行、またはプロンプトの厳しさ調整をご検討ください。
- Q: OpenAI/Gemini/Qwen 等で長文は？
  - A: それぞれのコンテキスト制限内であれば可。超える場合は自前で要約・分割を追加してください。

---
必要に応じて `prompts.py` を編集することで、評価軸や出力スキーマを自由に拡張できます。
