import json
import time
import urllib.request
import urllib.parse
import os
from pathlib import Path
from dotenv import load_dotenv

from config.settings import ProjectConfig
from core.excel import read_xlsx

load_dotenv()

SUBDOMAIN = os.environ["AMO_SUBDOMAIN"]
CLIENT_ID = os.environ["AMO_CLIENT_ID"]
CLIENT_SECRET = os.environ["AMO_CLIENT_SECRET"]
AUTH_CODE = os.environ["AMO_AUTH_CODE"]
REDIRECT_URI = os.environ.get("AMO_REDIRECT_URI", "https://example.com")

BASE_URL = f"https://{SUBDOMAIN}.amocrm.ru"
TOKEN_FILE = Path(__file__).parent.parent / "amo_tokens.json"


def amo_request(method: str, endpoint: str, data=None, token=None) -> dict:
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  HTTP ошибка {e.code}: {error_body}")
        raise
    except Exception as e:
        print(f"  Ошибка запроса: {e}")
        raise


def save_tokens(tokens: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def load_tokens() -> dict | None:
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None


def get_tokens_by_code() -> str:
    print("Получаю токены по коду авторизации...")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": AUTH_CODE,
        "redirect_uri": REDIRECT_URI
    }
    tokens = amo_request("POST", "/oauth2/access_token", data)
    save_tokens(tokens)
    print("Токены получены и сохранены!")
    return tokens["access_token"]


def refresh_tokens() -> str:
    print("Обновляю токены...")
    saved = load_tokens()
    if not saved or "refresh_token" not in saved:
        raise Exception("Нет сохранённого refresh_token. Получите новый код авторизации.")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": saved["refresh_token"],
        "redirect_uri": REDIRECT_URI
    }
    tokens = amo_request("POST", "/oauth2/access_token", data)
    save_tokens(tokens)
    print("Токены обновлены!")
    return tokens["access_token"]


def get_access_token() -> str:
    saved = load_tokens()
    if saved and "access_token" in saved:
        try:
            amo_request("GET", "/api/v4/account", token=saved["access_token"])
            print("Используем сохранённый токен")
            return saved["access_token"]
        except:
            try:
                return refresh_tokens()
            except:
                pass
    return get_tokens_by_code()


def create_contact(token: str, lead: dict) -> int:
    contact_data = [{"name": lead["name"], "custom_fields_values": []}]

    phones = []
    if lead["phone"]:
        phones.append({"value": lead["phone"], "enum_code": "WORK"})
    if lead["phone2"]:
        phones.append({"value": lead["phone2"], "enum_code": "MOB"})
    if lead["phone3"]:
        phones.append({"value": lead["phone3"], "enum_code": "OTHER"})
    if phones:
        contact_data[0]["custom_fields_values"].append({
            "field_code": "PHONE",
            "values": phones
        })

    emails = []
    if lead["email"]:
        emails.append({"value": lead["email"], "enum_code": "WORK"})
    if lead["email2"]:
        emails.append({"value": lead["email2"], "enum_code": "OTHER"})
    if lead["email3"]:
        emails.append({"value": lead["email3"], "enum_code": "OTHER"})
    if emails:
        contact_data[0]["custom_fields_values"].append({
            "field_code": "EMAIL",
            "values": emails
        })

    result = amo_request("POST", "/api/v4/contacts", contact_data, token)
    contact_id = result["_embedded"]["contacts"][0]["id"]
    print(f"  Контакт создан: ID {contact_id}")

    note_parts = []
    if lead["inn"]:
        note_parts.append(f"ИНН: {lead['inn']}")
    if lead["website"]:
        note_parts.append(f"Сайт: {lead['website']}")
    if lead["activity"]:
        note_parts.append(f"Основной вид деятельности: {lead['activity']}")
    if lead["other_activities"]:
        note_parts.append(f"Другие виды деятельности:\n{lead['other_activities']}")

    if note_parts:
        note_data = [{"note_type": "common", "params": {"text": "\n".join(note_parts)}}]
        try:
            amo_request("POST", f"/api/v4/contacts/{contact_id}/notes", note_data, token)
            print(f"  Примечание добавлено")
        except:
            print(f"  Ошибка примечания")

    return contact_id


def create_lead_deal(token: str, lead: dict, contact_id: int) -> int:
    deal_data = [{
        "name": f"Лид: {lead['name']}",
        "price": 0,
        "_embedded": {"contacts": [{"id": contact_id}]}
    }]
    result = amo_request("POST", "/api/v4/leads", deal_data, token)
    lead_id = result["_embedded"]["leads"][0]["id"]
    print(f"  Сделка создана: ID {lead_id}")
    return lead_id


def push_to_amo(config: ProjectConfig, input_file: Path = None):
    print("=" * 50)
    print("  PUSH LEADS TO AMOCRM")
    print("=" * 50)

    token = get_access_token()
    account = amo_request("GET", "/api/v4/account", token=token)
    print(f"Аккаунт: {account.get('name', 'N/A')}\n")

    source_file = input_file or config.profiles_file
    rows = read_xlsx(source_file)

    leads = []
    for row in rows:
        name = row[0]
        if not name:
            continue
        leads.append({
            "name": str(name).strip(),
            "inn": str(row[1]).strip() if row[1] else "",
            "phone": str(row[2]).strip() if row[2] else "",
            "phone2": str(row[3]).strip() if row[3] else "",
            "phone3": str(row[4]).strip() if row[4] else "",
            "email": str(row[5]).strip() if row[5] else "",
            "email2": str(row[6]).strip() if row[6] else "",
            "email3": str(row[7]).strip() if row[7] else "",
            "website": str(row[8]).strip() if len(row) > 8 and row[8] else "",
            "activity": str(row[9]).strip() if len(row) > 9 and row[9] else "",
            "other_activities": str(row[10]).strip() if len(row) > 10 and row[10] else "",
        })

    print(f"Всего лидов для загрузки: {len(leads)}")
    print("-" * 50)

    success = 0
    errors = 0

    for i, lead in enumerate(leads):
        print(f"\n[{i+1}/{len(leads)}] {lead['name']}")
        try:
            contact_id = create_contact(token, lead)
            create_lead_deal(token, lead, contact_id)
            success += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ОШИБКА: {e}")
            errors += 1
            time.sleep(1)

    print("\n" + "=" * 50)
    print(f"  Готово! Успешно: {success}, Ошибок: {errors}")
    print("=" * 50)