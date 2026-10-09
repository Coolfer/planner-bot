# Ежедневник-бот (контейнер для VPS)

Телеграм-бот + планировщик домашних дел с бесплатной моделью OpenRouter (`openrouter/free` или `thinkingmachines/inkling:free`).

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
| `OPENROUTER_API_KEY` | — (обязательно) |
| `OPENROUTER_MODEL` | `openrouter/free` |
| `DB_PATH` | `/data/planner.db` |

## Файлы проекта
- `bot.py` — Telegram-бот (python-telegram-bot)
- `planner.py` — CLI для планирования и консультаций
- `db.py` — SQLite (задачи, планы, настройки)
- `openrouter_client.py` — вызов OpenRouter API
- `Dockerfile`, `docker-compose.yml`, `.env.example`
