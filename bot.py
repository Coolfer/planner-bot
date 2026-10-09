#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from groq_client import call_groq
from db import init_db, get_pending_tasks, save_plan, get_plan_for_date, save_task, get_recent_plans

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Conversation states
TASK_NAME, TASK_DURATION, TASK_CONFIRM = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    await update.message.reply_text(
        "Привет! Я ежедневник-бот.\n"
        "Команды:\n"
        "/plan — план на сегодня\n"
        "/consult — совет по распределению времени\n"
        "/tasks — список дел\n"
        "/add — добавить задачу (начнёт диалог)\n"
        "/daily — показать сохранённый план\n"
        "Напиши мне текстом — я отвечу и помогу распределить дела.", parse_mode="MarkdownV2"
    )


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    existing = get_plan_for_date(today)
    if existing and existing.get("plan_text"):
        await update.message.reply_text(f"План на сегодня (сохранён):\n{existing['plan_text']}", parse_mode="MarkdownV2")
        if existing.get("advice_text"):
            await update.message.reply_text(f"Совет:\n{existing['advice_text']}", parse_mode="MarkdownV2")
    else:
        tasks = get_pending_tasks()
        task_txt = "\n".join([f"• {t['name']} ({t['category']}, {t['duration_min']} мин, приоритет {t['priority']})" for t in tasks]) or "• (нет задач)"
        recent_plans = get_recent_plans(7)
        history_txt = "\n".join([f"{p['date']}: {p['plan_text'][:200]}..." for p in recent_plans]) if recent_plans else "(нет истории планов)"
        prompt = f"Сегодня: {today}.\nНерешённые дела:\n{task_txt}\n\nИстория планов (7 дней):\n{history_txt}\n\nАнализируй историю и составь план на день с конкретным распределением дел по времени. Учитывай, что не выполнено ранее. Отвечай кратко, структурированно."
        system = "Ты — ежедневник-помощник. Форматируй ВСЕ ответы строго через Markdown-таблицы (| колонка | колонка |). НЕ используй жирный текст для заголовков таблиц. НЕ используй псевдотаблицы из тире или пробелов. Для матрицы Эйзенхауэра: заголовки Срочно / Не срочно. Для расписания: День | Утро (9-12) | День (12-17) | Вечер (17-20)."
        plan = call_groq(prompt, system)
        save_plan(today, plan)
        await update.message.reply_text(f"План на {today}:\n{plan}", parse_mode="MarkdownV2")


async def cmd_consult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    tasks = get_pending_tasks()
    task_txt = "\n".join([f"• {t['name']} ({t['duration_min']} мин)" for t in tasks]) or "• нет нерешённых задач"
    recent_plans = get_recent_plans(7)
    history_txt = "\n".join([f"{p['date']}: выполнено/не выполнено — {p['plan_text'][:150]}..." for p in recent_plans]) if recent_plans else "(нет истории)"
    prompt = f"Мои нерешённые дела:\n{task_txt}\n\nИстория планов (7 дней):\n{history_txt}\n\nАнализируй историю — что переносилось чаще всего, какие категории доминируют. Подскажи, как лучше распределить сегодня с учётом прошлых ошибок. Укажи порядок и объясни кратко."
    system = "Ты — консультант по планированию времени. Советуй, как распределить домашние дела, учитывая длительность и приоритеты. Отвечай кратко, практично, на русском."
    advice = call_groq(prompt, system)
    await update.message.reply_text(f"Совет по распределению:\n{advice}", parse_mode="MarkdownV2")


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    tasks = get_pending_tasks()
    if not tasks:
        await update.message.reply_text("Нет нерешённых задач. Добавьте через /add или текстом.", parse_mode="MarkdownV2")
        return
    lines = [f"{t['id']}. {t['name']} | {t['category']} | {t['duration_min']} мин | приоритет {t['priority']}" for t in tasks]
    await update.message.reply_text("Нерешённые дела:\n" + "\n".join(lines), parse_mode="MarkdownV2")


async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    plan = get_plan_for_date(today)
    if not plan or not plan.get("plan_text"):
        await update.message.reply_text("Плана на сегодня ещё нет. Напишите /plan или просто спросите.", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(f"План на сегодня ({today}):\n{plan['plan_text']}", parse_mode="MarkdownV2")
        if plan.get("advice_text"):
            await update.message.reply_text(f"Совет:\n{plan['advice_text']}", parse_mode="MarkdownV2")


async def cmd_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите название задачи (например: 'уборка кухни 30'):", parse_mode="MarkdownV2")
    return TASK_NAME


async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_task"] = {"name": update.message.text}
    await update.message.reply_text("Сколько минут займёт? (число, по умолчанию 30):", parse_mode="MarkdownV2")
    return TASK_DURATION


async def add_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        duration = int(update.message.text)
    except ValueError:
        duration = 30
    context.user_data["new_task"]["duration"] = duration
    await update.message.reply_text("Приоритет (1-5, по умолчанию 1):", parse_mode="MarkdownV2")
    return TASK_CONFIRM


async def add_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        priority = int(update.message.text)
    except ValueError:
        priority = 1
    init_db()
    data = context.user_data.get("new_task", {"name": "задача"})
    save_task(data["name"], duration_min=data.get("duration", 30), priority=priority)
    await update.message.reply_text(f"Добавлено: {data['name']} ({data.get('duration', 30)} мин, приоритет {priority}).", parse_mode="MarkdownV2")
    context.user_data.clear()
    return ConversationHandler.END


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    text = update.message.text
    text_lower = text.lower()
    if any(word in text_lower for word in ["список", "задач", "дел", "tasks", "list"]):
        tasks = get_pending_tasks()
        if tasks:
            lines = [f"{t['id']}. {t['name']} | {t['category']} | {t['duration_min']} мин | приоритет {t['priority']}" for t in tasks]
            await update.message.reply_text("Нерешённые дела:\n" + "\n".join(lines), parse_mode="MarkdownV2")
        else:
            await update.message.reply_text("Нет нерешённых задач.", parse_mode="MarkdownV2")
        return
    # Ответим как консультант + сохраним, если это задача
    prompt = f"Пользователь написал: '{text}'\nМои нерешённые дела:\n" + "\n".join([f"• {t['name']} ({t['duration_min']} мин)" for t in get_pending_tasks()]) + "\n\nОтветь кратко, помоги распределить или ответь на вопрос по планированию."
    system = "Ты — ежедневник-помощник, отвечаешь кратко, практично, на русском."
    reply = call_groq(prompt, system)
    await update.message.reply_text(reply, parse_mode="MarkdownV2")


def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("consult", cmd_consult))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("daily", cmd_daily))
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", cmd_add_start)],
        states={
            TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            TASK_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_duration)],
            TASK_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_confirm)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    app.add_handler(add_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started. Token set: %s", bool(TOKEN))
    app.run_polling()


if __name__ == "__main__":
    main()
