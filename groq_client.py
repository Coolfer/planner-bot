import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)


def call_groq(prompt: str, system_msg: str = "") -> str:
    if not client:
        return "[Ошибка: GROQ_API_KEY не задан]"
    try:
        messages = [
            {"role": "system", "content": system_msg or "Ты — помощник-ежедневник. Составляй планы на день, распределяй домашние дела, советуй по времени. Отвечай кратко, по делу, на русском."},
            {"role": "user", "content": prompt},
        ]
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.5,
            max_tokens=1200,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Groq request failed: %s", exc)
        return f"[Ошибка API: {exc}]"
