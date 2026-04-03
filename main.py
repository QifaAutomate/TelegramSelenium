import time
import re
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

CHAT_NAME = "WB Партнёры — чат"
DAYS_BACK = 1
KEYWORDS = ["куплю", "ищу", "нужен", "поставщик", "опт", "закупка"]
COLLECT_PHONE = True
CHROME_PROFILE_PATH = r"C:\Users\USERNAME\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR = "Default"

cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)
excel_file = f"telegram_leads_{int(time.time())}.xlsx"
users = {}
processed_messages = set()

options = Options()
options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument(f"--profile-directory={PROFILE_DIR}")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 40)


def parse_date(date_str):
    try:
        if date_str:
            return datetime.fromisoformat(date_str.replace("Z", ""))
    except:
        return None


def is_lead(text):
    text_lower = text.lower()
    return any(k in text_lower for k in KEYWORDS)


def normalize_phone(text):
    match = re.search(r'\+?\d[\d\s\-\(\)]{10,20}', text)
    return match.group(0) if match else ""

def parse_message(msg):
    try:
        msg_id = msg.get_attribute("data-message-id")
        if not msg_id or msg_id in processed_messages:
            return None

        user_id = msg.get_attribute("data-peer-id") or msg.get_attribute("data-user-id")

        if not user_id:
            return None

        full_name = ""
        try:
            full_name = msg.find_element(By.CSS_SELECTOR, "[data-peer-id] .peer-title, .sender-title").text
        except:
            pass

        text = ""
        try:
            text = msg.find_element(By.CSS_SELECTOR, ".text-content").text
        except:
            return None

        if not text.strip():
            return None

        dt = msg.get_attribute("data-datetime")
        date = parse_date(dt)

        processed_messages.add(msg_id)

        return {
            "user_id": user_id,
            "full_name": full_name,
            "text": text,
            "date": date
        }

    except:
        return None


def add_message(data):
    uid = data["user_id"]

    if uid not in users:
        users[uid] = {
            "user_id": uid,
            "full_name": data["full_name"],
            "username": "",
            "phone": "",
            "messages": [],
            "is_lead": False,
            "first_seen": data["date"],
            "last_seen": data["date"]
        }

    users[uid]["messages"].append(data["text"])

    if data["date"]:
        users[uid]["last_seen"] = data["date"]

    if is_lead(data["text"]):
        users[uid]["is_lead"] = True


def open_profile(msg_element):
    try:
        avatar = msg_element.find_element(By.CSS_SELECTOR, "[data-peer-id]")
        avatar.click()
        time.sleep(1)
        return True
    except:
        return False


def extract_profile():
    username = ""
    phone = ""

    try:
        try:
            username_elem = driver.find_element(By.XPATH, "//*[contains(text(),'@')]")
            username = username_elem.text
        except:
            pass

        if COLLECT_PHONE:
            try:
                phone_elem = driver.find_element(By.XPATH, "//*[contains(text(), '+')]")
                phone = normalize_phone(phone_elem.text)
            except:
                pass
    except:
        pass
    return username, phone


def close_profile():
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(0.5)

def enrich_user(msg_element, user_id):
    if not open_profile(msg_element):
        return

    username, phone = extract_profile()

    if username:
        users[user_id]["username"] = username

    if phone:
        users[user_id]["phone"] = phone

    close_profile()


driver.get("https://web.telegram.org")

wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
time.sleep(5)

chats = driver.find_elements(By.CSS_SELECTOR, ".ListItem.Chat")

target = None
for chat in chats:
    if CHAT_NAME in chat.text:
        target = chat
        break

if not target:
    raise Exception("Чат не найден")

target.click()
time.sleep(3)


last_height = 0

while True:
    messages = driver.find_elements(By.CSS_SELECTOR, "[data-message-id]")

    for msg in messages:
        data = parse_message(msg)
        if not data:
            continue

        if data["date"] and data["date"] < cutoff_date:
            break

        add_message(data)

        if users[data["user_id"]]["is_lead"] and not users[data["user_id"]]["username"]:
            enrich_user(msg, data["user_id"])

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    new_height = driver.execute_script("return document.body.scrollHeight")

    if new_height == last_height:
        break

    last_height = new_height


rows = []

for user in users.values():
    rows.append({
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "username": user["username"],
        "phone": user["phone"],
        "is_lead": user["is_lead"],
        "message_count": len(user["messages"]),
        "messages": "\n\n---\n\n".join(user["messages"])
    })

df = pd.DataFrame(rows)
df.to_excel(excel_file, index=False)

print(f"Готово: {excel_file}")

driver.quit()

