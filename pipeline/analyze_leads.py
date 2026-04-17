# pipeline/analyze_leads.py
import json
import time
import urllib.request
import urllib.parse
import ssl
import os
import uuid
from dotenv import load_dotenv

from config.settings import ProjectConfig
from core.excel import read_xlsx, write_xlsx

load_dotenv()

GIGACHAT_CREDENTIALS = os.environ["GIGACHAT_CREDENTIALS"]
GIGACHAT_SCOPE = os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
GIGACHAT_MODEL = os.environ.get("GIGACHAT_MODEL", "GigaChat-2-Pro")


def get_token() -> str:
    data = urllib.parse.urlencode({"scope": GIGACHAT_SCOPE}).encode()
    req = urllib.request.Request(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        data=data,
        headers={
            "Authorization": f"Basic {GIGACHAT_CREDENTIALS}",
            "Content-Type": "application/x-www-form-urlencoded",
            "RqUID": str(uuid.uuid4()),
            "Accept": "application/json"
        }
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        result = json.loads(resp.read())
        print("Токен получен")
        return result["access_token"]


def analyze_user(token: str, name: str, messages: str) -> dict:
    prompt = f"""Ты анализируешь сообщения участника Telegram чата WB Партнёры (чат продавцов Wildberries).

Имя: {name}
Сообщения: {messages[:1500]}

Определи: является ли этот человек активным продавцом или покупателем товаров — то есть он продаёт на маркетплейсах, работает с товарами, закупает продукцию, ищет поставщиков, занимается логистикой/фулфилментом, упоминает артикулы/остатки/поставки/склад.

Считай лидом ШИРОКО: любой кто явно работает с товарами на маркетплейсе — даже если жалуется на ВБ, это всё равно активный селлер.

НЕ считай лидом только тех кто: вообще не упоминает товары/продажи, только спрашивает про технические проблемы не связанные с торговлей.

Ответь ТОЛЬКО в формате JSON без лишнего текста:
{{"is_lead": true/false, "reason": "краткое объяснение на русском (1 предложение)", "score": 1-10}}"""

    data = json.dumps({
        "model": GIGACHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.1
    }).encode("utf-8")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)


def analyze_leads(config: ProjectConfig):
    print("=== Анализ лидов через GigaChat ===")

    rows = read_xlsx(config.messages_file)
    users = [(row[0], row[1]) for row in rows if row[0] and row[1]]
    print(f"Всего пользователей: {len(users)}")

    token = get_token()
    leads = []
    token_refresh_counter = 0

    for i, (name, messages) in enumerate(users):
        print(f"[{i+1}/{len(users)}] Анализирую: {name}...")

        if token_refresh_counter >= 50:
            token = get_token()
            token_refresh_counter = 0
            print("Токен обновлён")

        try:
            result = analyze_user(token, name, messages)
            if result.get("is_lead"):
                leads.append({
                    "name": name,
                    "reason": result.get("reason", ""),
                    "score": result.get("score", 0)
                })
                print(f"  ЛИД! Оценка: {result['score']} — {result['reason']}")
            else:
                print(f"  Не лид")
            token_refresh_counter += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  Ошибка: {e}")
            time.sleep(1)

    leads.sort(key=lambda x: x["score"], reverse=True)

    output_rows = [[lead["name"], lead["reason"], lead["score"]] for lead in leads]
    write_xlsx(config.leads_file, ["Отправитель", "Причина", "Оценка (1-10)"], output_rows)

    print(f"\nГотово! Найдено лидов: {len(leads)} из {len(users)}")
    print(f"Результат: {config.leads_file}")