#!/usr/bin/env python3
import os
from datetime import datetime
from groq_client import call_groq
from db import init_db, get_pending_tasks, save_plan, get_plan_for_date, save_task, set_user_pref, get_user_prefs


def build_plan():
    init_db()
    today = datetime.now().strftime("%Y-%m-%d")
    existing = get_plan_for_date(today)
    tasks = get_pending_tasks()
    task_txt = "\n".join([f"- {t['name']} ({t['category']}, {t['duration_min']} мин, приоритет {t['priority']})" for t in tasks]) or "- (нет задач)"

    prompt = f"""Сегодня: {today}.
Нерешённые домашние дела:
{task_txt}

Составь план на день (утро, день, вечер) с конкретным распределением дел. Укажи примерное время и длительность. Если задач много — предложи, что перенести. Будь краток, структурируй списком."""
    system = "Ты — ежедневник-помощник. Составляй реалистичный план дня с распределением домашних дел. Учитывай приоритеты и длительность. Отвечай структурированно, кратко."
    plan = call_groq(prompt, system)
    save_plan(today, plan)
    print(f"План на {today}:\n{plan}\n")


def consult():
    init_db()
    tasks = get_pending_tasks()
    task_txt = "\n".join([f"- {t['name']} ({t['duration_min']} мин)" for t in tasks]) or "- нет нерешённых задач"
    prompt = f"""Мои нерешённые дела:
{task_txt}

Подскажи, как лучше распределить время сегодня между этими делами? Укажи порядок и объясни. Отвечай кратко, практично."""
    system = "Ты — консультант по планированию времени. Советуй, как распределить домашние дела, учитывая длительность и приоритеты. Отвечай кратко, по делу."
    advice = call_groq(prompt, system)
    print(f"Совет по распределению:\n{advice}\n")


def add_task(name: str, duration: int = 30, priority: int = 1):
    init_db()
    tid = save_task(name, duration_min=duration, priority=priority)
    print(f"Задача добавлена: id={tid}, {name}")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "plan":
        build_plan()
    elif cmd == "consult":
        consult()
    elif cmd == "add":
        name = sys.argv[2] if len(sys.argv) > 2 else input("Задача: ")
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        add_task(name, duration)
    else:
        print("Команды: plan | consult | add [имя] [мин]")
