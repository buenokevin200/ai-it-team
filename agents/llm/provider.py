from typing import Optional

from langchain_openai import ChatOpenAI


class LLMProvider:
    def __init__(self):
        self._deepseek_key: Optional[str] = None
        self._deepseek_url: Optional[str] = None
        self._deepseek_model: Optional[str] = None
        self._ready = False

    def configure(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat") -> None:
        self._deepseek_key = api_key
        self._deepseek_url = base_url
        self._deepseek_model = model
        self._ready = bool(api_key)

    def load_from_db(self):
        from tools.db import get_config_sync
        key = get_config_sync("ai_deepseek_api_key")
        url = get_config_sync("ai_deepseek_base_url") or "https://api.deepseek.com"
        model = get_config_sync("ai_deepseek_model") or "deepseek-chat"
        if key:
            self.configure(key, url, model)

    @property
    def is_ready(self) -> bool:
        return self._ready

    def get_chat_llm(self, temperature: float = 0.1) -> ChatOpenAI:
        if not self._ready:
            self.load_from_db()
        if not self._ready:
            raise RuntimeError(
                "Deepseek no configurado. Ve a Configuracion > Inteligencia Artificial "
                "e ingresa tu API Key de Deepseek."
            )
        return ChatOpenAI(
            model=self._deepseek_model,
            api_key=self._deepseek_key,
            base_url=self._deepseek_url,
            temperature=temperature,
            timeout=15,
            max_retries=0,
        )

    def get_reasoning_llm(self) -> ChatOpenAI:
        return self.get_chat_llm(temperature=0.0)


_provider: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = LLMProvider()
        _provider.load_from_db()
    return _provider
