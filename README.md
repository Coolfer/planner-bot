# Ежедневник-бот (контейнер для VPS)

Телеграм-бот + планировщик домашних дел с Groq API (`openai/gpt-oss-120b` — OpenAI 120B).

## Быстрый запуск

1) Скопируйте `.env.example` в `.env` и заполните ключи:
```bash
cp .env.example .env
# Откройте .env и вставьте OPENROUTER_API_KEY и TELEGRAM_BOT_TOKEN
```

2) Соберите и запустите:
```bash
docker compose up -d --build
```

3) Проверьте логи:
```bash
docker logs -f daily-bot
```

## Команды в Telegram
- `/start` — приветствие
- `/plan` — составить план на сегодня (автоматически или по запросу)
- `/consult` — совет по распределению времени
- `/tasks` — список нерешённых дел
- `/daily` — показать сохранённый план
- `/add` — добавить задачу (диалог)
- Любой текст — ответ-консультант с учётом текущих дел

## Автоматическое планирование
В контейнере настроен `cron`:
- 07:30 — генерация плана (`plan`)
- 09:00 — совет по распределению (`consult`)

Результаты сохраняются в SQLite (`/data/planner.db`) и в логах (`/data/daily_plan.log`).

## Работа с задачами через CLI (контейнер)
```bash
docker exec daily-bot python planner.py add "уборка кухни" 30
docker exec daily-bot python planner.py plan
docker exec daily-bot python planner.py consult
```

## Переменные окружения
| Переменная | Значение по умолчанию |
|---|---|
| `TELEGRAM_BOT_TOKEN` | — (обязательно) |
| `GROQ_API_KEY` | — (обязательно) |
| `GROQ_MODEL` | `openai/gpt-oss-120b` |
| `DB_PATH` | `/data/planner.db` |

## Файлы проекта
- `bot.py` — Telegram-бот (python-telegram-bot)
- `planner.py` — CLI для планирования и консультаций
- `db.py` — SQLite (задачи, планы, настройки)
- `groq_client.py` — вызов Groq API (`openai/gpt-oss-120b`)
- `Dockerfile`, `docker-compose.yml`, `.env.example`
# Deployed via GitHub Actions
