import httpx
from dotenv import load_dotenv
import asyncio
from typing import Optional
import os

try:
    import anthropic
except Exception:
    anthropic = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

MAX_RETRIES = 6
BASE_DELAY = 2
TIMEOUT_MAX = 120

OPENAI = "chatgpt"
ANTHROPIC = "claude"
GEMINI = "gemini"
QWEN = "qwen"
PHI = "phi"
DEEPSEEK = "deepseek"

ALL_MODELS = [OPENAI, ANTHROPIC, GEMINI, QWEN, PHI, DEEPSEEK]

class LLMAgent:
    def __init__(self, agent: str):
        self.agent = agent
        self.config = self._load_config(agent)
    
    async def call(self, prompts) -> str:
        if self.agent == OPENAI:
            return await self._call_openai(prompts)
        elif self.agent == ANTHROPIC:
            return self._call_anthropic(prompts)
        elif self.agent == GEMINI:
            return self._call_gemini(prompts)
        elif self.agent == QWEN:
            return await self._call_qwen(prompts)
        elif self.agent == PHI:
            return await self._call_phi(prompts)
        elif self.agent == DEEPSEEK:
            return await self._call_deepseek(prompts)
        else:
            raise ValueError(f"Invalid agent: {self.agent}")

    def _load_config(self, agent: str) -> dict:
        load_dotenv()
        api_key_name = "OPENAI_API_KEY"
        model_name = "OPENAI_MODEL"
        if agent == ANTHROPIC:
            api_key_name = "ANTHROPIC_API_KEY"
            model_name = "ANTHROPIC_MODEL"
        elif agent == GEMINI:
            api_key_name = "GOOGLE_API_KEY"
            model_name = "GEMINI_MODEL"
        elif agent == QWEN:
            api_key_name = "QWEN_API_KEY"
            model_name = "QWEN_MODEL"
        elif agent == PHI:
            api_key_name = "PHI_API_KEY"
            model_name = "PHI_MODEL"
        elif agent == DEEPSEEK:
            api_key_name = "DEEPSEEK_API_KEY"
            model_name = "DEEPSEEK_MODEL"

        api_key = os.environ.get(api_key_name)
        if not api_key:
            raise RuntimeError(f"{api_key_name} が設定されていません。")
        model = os.environ.get(model_name, "gpt-4o-mini")

        return {
            "api_key": api_key,
            "model": model
        }
    
    async def _call_openai(self, prompts) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        payload = {
            "model": self.config["model"],
            "messages": prompts,
            "temperature": 0.7,
        }
        return await self._call_api(url, headers, payload)

    def _call_anthropic(self, prompts) -> str:
        if anthropic is None:
            raise RuntimeError("anthropic パッケージがインストールされていません。")
        client = anthropic.Anthropic(api_key=self.config["api_key"])
        msg = client.messages.create(
            model=self.config["model"],
            max_tokens=4096,
            temperature=0.2,
            messages=prompts,
        )
        return "".join(part.text for part in msg.content if getattr(part, "type", "") == "text")
    
    def _call_gemini(self, prompts) -> str:
        if genai is None:
            raise RuntimeError("google-generativeai パッケージがインストールされていません。")
        genai.configure(api_key=self.config["api_key"])
        model = genai.GenerativeModel(self.config["model"])
        user_prompt = "".join(prompt["content"] for prompt in prompts if prompt["role"] == "user")
        # for m in genai.list_models():
        #     pprint.pprint(m)
        response = model.generate_content(user_prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        return "\n".join([p.text for c in (response.candidates or []) for p in c.content.parts if getattr(p, "text", None)])
    
    async def _call_qwen(self, prompts) -> str:
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config["model"],
            "messages": prompts
        }
        return await self._call_api(url, headers, payload)
    
    async def _call_phi(self, prompts) -> str:
        url = f"https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config["model"],
            "messages": prompts
        }
        return await self._call_api(url, headers, payload)
    
    async def _call_deepseek(self, prompts) -> str:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config["model"],
            "messages": prompts
        }
        return await self._call_api(url, headers, payload)

    async def _call_api(self, url, headers, payload) -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT_MAX) as client:
            for attempt in range(MAX_RETRIES):
                response = await client.post(url, headers=headers, json=payload)
                print("API Response: ", response.json())
                status_code = response.status_code
                if status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                if status_code == 429:
                    # Retry-After ヘッダを尊重
                    retry_after: Optional[float] = None
                    if "Retry-After" in response.headers:
                        try:
                            retry_after = float(response.headers["Retry-After"])
                        except:
                            retry_after = None

                    delay = retry_after or (BASE_DELAY * (2 ** attempt))
                    delay = min(delay, 60)  # 最大 60 秒
                    print(f"[WARN] 429 Too Many Requests → {delay:.1f} 秒待機して再試行 ({attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue

                # その他のエラーは即失敗
                response.raise_for_status()
        raise RuntimeError("429 エラーが解消されず、全てのリトライが失敗しました。")