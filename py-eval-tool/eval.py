import asyncio
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Literal, Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
import prompts
from llm import ANTHROPIC, QWEN, LLMAgent, ALL_MODELS
import tiktoken
from scrapers.syosetu.scraper import SyosetuScraper
from scrapers.kakuyomu.scraper import KakuyomuScraper

# Optional SDK (必要な場合のみインポート)
try:
    import anthropic
except Exception:
    anthropic = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


# -----------------------------
# 0) 共通: プロンプトテンプレート
# -----------------------------
PROMPT_TEMPLATE = """あなたはライトノベル編集者です。  

以下のJSON形式の小説データを読み込み、章ごとに要約したうえで、作品全体を評価してください。  

### 評価基準（1〜10点）

- 物語のテンポ  
- キャラクターの魅力  
- 文体の読みやすさ  
- 世界観の独自性  
- 読者ターゲット適合度  

### 出力フォーマット

{{
  "title": "",
  "overall_score": 数値（100点満点換算）,
  "scores": {{
    "tempo": 数値,
    "characters": 数値,
    "style": 数値,
    "worldbuilding": 数値,
    "target_fit": 数値
  }},
  "comments": {{
    "strengths": ["強み1", "強み2", "強み3"],
    "weaknesses": ["改善点1", "改善点2", "改善点3"]
  }}
}}

### 小説データ

{novel_json}
"""


# -----------------------------
# 1) 出力スキーマ（バリデーション用）
# -----------------------------
class Scores(BaseModel):
    tempo: float = Field(ge=0, le=10)
    characters: float = Field(ge=0, le=10)
    style: float = Field(ge=0, le=10)
    worldbuilding: float = Field(ge=0, le=10)
    target_fit: float = Field(ge=0, le=10)

class Comments(BaseModel):
    strengths: list[str]
    weaknesses: list[str]

class EvalOut(BaseModel):
    title: str
    overall_score: float = Field(ge=0, le=100)
    scores: Scores
    comments: Comments
    final_summary: str


# -----------------------------
# 2) JSON抽出ユーティリティ
# -----------------------------
def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    モデルがコードブロックや説明を返しても、
    JSON部分のみ安全に抽出する。
    - 最初の '{' から最後の '}' までを抽出
    - 失敗時は json.loads を直接試す
    """

    # 1) ```json ... ``` ブロックを優先
    code_block = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if code_block:
        candidate = code_block.group(1).strip()
        return json.loads(candidate)

    # 2) 最も大きい { } を抽出
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        candidate = brace_match.group(0)
        return json.loads(candidate)

    # 3) 最後の手段: 直接パース
    return json.loads(text)


# -----------------------------
# 3) モデル呼び出しアダプタ
# -----------------------------
ModelKind = Literal["chatgpt", "claude", "gemini", "qwen", "phi"]

async def call_chatgpt(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
    }

    max_retries = 6
    base_delay = 2  # 秒
    timeout = 120

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            resp = await client.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            if resp.status_code == 429:
                # Retry-After ヘッダを尊重
                retry_after: Optional[float] = None
                if "Retry-After" in resp.headers:
                    try:
                        retry_after = float(resp.headers["Retry-After"])
                    except:
                        retry_after = None

                delay = retry_after or (base_delay * (2 ** attempt))
                delay = min(delay, 60)  # 最大 60 秒
                print(f"[WARN] 429 Too Many Requests → {delay:.1f} 秒待機して再試行 ({attempt+1}/{max_retries})")
                await asyncio.sleep(delay)
                continue

            # その他のエラーは即失敗
            resp.raise_for_status()

    raise RuntimeError("429 エラーが解消されず、全てのリトライが失敗しました。")

async def call_claude(prompt: str) -> str:
    if anthropic is None:
        raise RuntimeError("anthropic パッケージがインストールされていません。")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY が設定されていません。")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    # Claude SDK の返却は list
    return "".join(part.text for part in msg.content if getattr(part, "type", "") == "text")

async def call_gemini(prompt: str) -> str:
    if genai is None:
        raise RuntimeError("google-generativeai パッケージがインストールされていません。")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY が設定されていません。")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(prompt)
    if hasattr(resp, "text") and resp.text:
        return resp.text
    return "\n".join([p.text for c in (resp.candidates or []) for p in c.content.parts if getattr(p, "text", None)])

async def call_qwen(prompt: str) -> str:
    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY (または QWEN_API_KEY) が設定されていません。")
    model = os.environ.get("QWEN_MODEL", "qwen3-235b-instruct")

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    max_retries = 6
    base_delay = 2
    timeout = 120

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            resp = await client.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            if resp.status_code == 429:
                retry_after: Optional[float] = None
                if "Retry-After" in resp.headers:
                    try:
                        retry_after = float(resp.headers["Retry-After"])
                    except Exception:
                        retry_after = None

                delay = retry_after or (base_delay * (2 ** attempt))
                delay = min(delay, 60)
                print(f"[WARN] 429 Too Many Requests → {delay:.1f} 秒待機して再試行 ({attempt+1}/{max_retries})")
                await asyncio.sleep(delay)
                continue

            resp.raise_for_status()

    raise RuntimeError("429 エラーが解消されず、全てのリトライが失敗しました。")

async def call_phi(prompt: str) -> str:
    api_key = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_API_KEY")
    if not api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY (または HF_API_KEY) が設定されていません。")
    model = os.environ.get("PHI_MODEL", "microsoft/phi-4")

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.2,
            "max_new_tokens": 1024,
        },
    }

    max_retries = 6
    base_delay = 2
    timeout = 120

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            resp = await client.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    candidate = data[0]
                    if isinstance(candidate, dict) and "generated_text" in candidate:
                        return candidate["generated_text"]
                if isinstance(data, dict) and "generated_text" in data:
                    return data["generated_text"]
                raise RuntimeError(f"Phi-4 応答形式が予期しないものでした: {data}")

            if resp.status_code in {422, 429, 503}:
                delay: Optional[float] = None
                try:
                    payload_json = resp.json()
                    delay = payload_json.get("estimated_time")
                except Exception:
                    delay = None
                if not delay:
                    delay = base_delay * (2 ** attempt)
                delay = min(delay, 60)
                print(
                    f"[WARN] Phi-4 API {resp.status_code} → {delay:.1f} 秒待機して再試行 ({attempt+1}/{max_retries})"
                )
                await asyncio.sleep(delay)
                continue

            resp.raise_for_status()

    raise RuntimeError("Phi-4 API が安定せず、全てのリトライが失敗しました。")


# -----------------------------
# 4) パス変換 input → output
# -----------------------------
def compute_output_path(input_path: Path, agent: str) -> Path:
    """
    規則:
    - パスに /input/ または \input\ が含まれていれば /output/ に置換
    - 含まれていなければ input と同階層に output/ を作成して保存
    """
    p_str = str(input_path)
    if "/input/" in p_str:
        return Path(p_str.replace("/input/", "/output/"))
    if "\\input\\" in p_str:
        return Path(p_str.replace("\\input\\", "\\output\\"))
    return input_path.parent.parent.joinpath("output", agent, input_path.name) if input_path.parent.name else input_path.parent.joinpath("output", agent, input_path.name)


# -----------------------------
# 5) メイン処理
# -----------------------------
def build_prompt(novel_json_str: str) -> str:
    return PROMPT_TEMPLATE.replace("{novel_json}", novel_json_str)


def preprocess_novel(input_file: Path) -> list[dict]:
    """Preprocess novel by grouping episodes to stay under token limits"""
    
    novel_dict = json.loads(Path(input_file).read_text(encoding="utf-8"))
    episodes = novel_dict["episodes"]
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    sub_novels = []
    current_group_tokens = 0
    current_group = []
    
    for episode in episodes:
        text = episode["text"]
        token_count = len(tokenizer.encode(text))

        # If adding this episode would exceed the limit, start a new group
        if current_group_tokens + token_count > 40000:
            sub_novels.append({**novel_dict, "episodes": current_group})
            current_group = [episode]
            current_group_tokens = token_count
        else:
            current_group.append(episode)
            current_group_tokens += token_count

    # Add the final group
    if current_group:
        sub_novels.append({**novel_dict, "episodes": current_group})

    return sub_novels


async def run_claude(input_file: Path, agent) -> Path:
    sub_novels = preprocess_novel(input_file)
    if len(sub_novels) == 1:
        novel_json_str = json.dumps(sub_novels[0], ensure_ascii=False, indent=2)
        prompt = prompts.EVAL_NOVEL_USER_PROMPT.replace("{novel_json}", novel_json_str)
        messages = [{"role": "user", "content": prompt}]
        result = await LLMAgent(agent).call(messages)
        return result
    else:
        sub_novel_results = []
        for sub_novel in sub_novels:
            novel_json_str = json.dumps(sub_novel, ensure_ascii=False, indent=2)
            prompt = prompts.EVAL_SUB_NOVEL_USER_PROMPT.replace("{novel_json}", novel_json_str)
            messages = [{"role": "user", "content": prompt}]
            result = await LLMAgent(agent).call(messages)
            await asyncio.sleep(3)
            sub_novel_results.append(result)
        
        prompt = prompts.EVAL_FULL_NOVEL_USER_PROMPT.replace("{sub_reviews}", "\n".join(sub_novel_results))
        messages = [{"role": "user", "content": prompt}]
        result = await LLMAgent(agent).call(messages)
        return result


ALL_SCRAPERS = ["syosetu", "kakuyomu"]


def run_scraper_if_needed(agent: str, scraper: str, work_id: str, episodes: int) -> str:
    file_path = f"input/{scraper}/{agent}/{work_id}.json"

    if Path(file_path).exists():
        return file_path
    else:
        data = None
        if scraper == "syosetu":
            syosetu_scraper = SyosetuScraper()
            data = syosetu_scraper.extract_novel_data(work_id, episodes)
        elif scraper == "kakuyomu":
            kakuyomu_scraper = KakuyomuScraper()
            data = kakuyomu_scraper.extract_novel_data(work_id, episodes)
        if data:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return file_path
        else:
            return None


async def run_evaluation(agent: str, work_id: str, episodes: int, stage_num:str) -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    work_file = Path(f'{base_dir}/storage/works/{work_id}.json')
    if not work_file.exists():
        return {
            "error": f"小説データの取得に失敗しました: work id = {work_id}"
        }
    
    novel_json = json.loads(Path(work_file).read_text(encoding="utf-8"))
    novel_json_str = json.dumps(novel_json, ensure_ascii=False, indent=2)

    # Read settings.json and filter by stage_num
    settings_file = Path(f'{base_dir}/storage/settings/settings.json')
    settings_json = json.loads(Path(settings_file).read_text(encoding="utf-8"))
    
    # Find the stage data
    stage_data = None
    for stage in settings_json:
        if stage.get('stage') == stage_num:
            stage_data = stage
            break
    # --- build the dynamic criteria description ---
    criteria_lines = []
    for c in stage_data.get('criteria', []):
        part = f"""- 評価基準{c['id']}
    評価名前： "{c['name']}",
    内容：" {c['prompt']}"
    最小スコア:{c['minScore']}
    最大スコア:{c['maxScore']}"""
        criteria_lines.append(part)

    criteria_text = "\n\n".join(criteria_lines)

    # --- build dynamic "scores" JSON keys ---
    scores_lines = [f'    "{c["name"]}": 数値 (評価基準{c['id']}についての評価)' for c in stage_data.get('criteria', [])]
    scores_text = ",\n".join(scores_lines)


    try:
        if agent == ANTHROPIC or agent == QWEN:
            eval_result = "" # await run_claude(work_file, agent)
        else:
            # prompt = prompts.EVAL_NOVEL_USER_PROMPT.replace("{novel_json}", novel_json_str)
            prompt = prompts.UPDATED_EVAL_NOVEL_USER_PROMPT.replace("{novel_json}", novel_json_str).replace("{criteria_text}", criteria_text).replace("{scores_text}", scores_text)
            messages = [{"role": "user", "content": prompt}]
            eval_result = await LLMAgent(agent).call(messages)    
        payload = extract_json_from_text(eval_result)
        # validated = EvalOut.model_validate(payload)

        # 出力先計算 & 保存
        output_path = Path(f"output/{work_id}-{agent}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_json = json.dumps(payload, ensure_ascii=False, indent=2)
        output_path.write_text(output_json, encoding="utf-8")
        return payload
    except Exception as e:
        return {
            "error": f"Failed to call LLM API: {e}"
        }

def main():
    load_dotenv()  # .env を自動読み込み
    parser = argparse.ArgumentParser(description="ライトノベル評価")
    parser.add_argument("--scraper", choices=ALL_SCRAPERS, required=True, help="使用するスクレイパー")
    parser.add_argument("--work_id", required=True, help="小説ID (例: n2596la)")
    parser.add_argument("--episodes", type=int, default=None, help="話数制限 (例: 5) - 省略可能")
    parser.add_argument("--model", choices=ALL_MODELS, required=True, help=f"使用する生成AI: {', '.join(ALL_MODELS)}")
    
    args = parser.parse_args()

    import asyncio
    # Windows の場合はイベントループポリシー変更
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        out_path = asyncio.run(run_evaluation(args.model, args.scraper, args.work_id, args.episodes))
        print(f"[OK] 出力完了: {out_path}")
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

