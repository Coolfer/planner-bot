import os
import http.client
import json
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")


def call_openrouter(prompt: str, system_msg: str = "") -> str:
    if not OPENROUTER_API_KEY:
        return "[Ошибка: OPENROUTER_API_KEY не задан]"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg or "Ты — помощник-ежедневник. Составляй планы на день, распределяй домашние дела, советуй по времени. Отвечай кратко, по делу, на русском."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 1200,
    }
    conn = http.client.HTTPSConnection("openrouter.ai", timeout=60)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://daily-bot.local",
        "X-Title": "daily-bot",
    }
    try:
        conn.request("POST", "/api/v1/chat/completions", body=json.dumps(payload), headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        result = json.loads(data)
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"].strip()
        if "error" in result:
            logger.error("OpenRouter error: %s", result.get("error"))
            return f"[Ошибка API: {result.get('error', 'неизвестно')}]"
        return "[Пустой ответ от модели]"
    except Exception as exc:
        logger.error("OpenRouter request failed: %s", exc)
        return f"[Ошибка сети/API: {exc}]"
    finally:
        conn.close()
