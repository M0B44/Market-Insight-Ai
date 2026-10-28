from __future__ import annotations

import json
import os
from typing import Any

import requests


def _get_api_key() -> str | None:
    return os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')


def llm_available() -> bool:
    return bool(_get_api_key())


def call_llm_json(prompt: str, model: str | None = None) -> Any | None:
    api_key = _get_api_key()
    if not api_key:
        return None

    provider = (os.getenv('LLM_PROVIDER') or 'openai').lower()
    if provider == 'openai':
        endpoint = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')
        payload = {
            'model': model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
        }
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
    else:
        return None

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        return json.loads(content)
    except Exception:
        return None
