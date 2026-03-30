import time
import random
import pandas as pd
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

CHAT_NAME = "WB Партнёры — чат"
DAYS_BACK = 10

CHROME_PROFILE_PATH = r"C:\Users\Ирина Сулла\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR = "Default"

cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)
OUTPUT_FILE = f"telegram_raw_{int(time.time())}.xlsx"

users = {}
processed_messages = set()

options = Options()
options.add_argument("--user-data-dir=C:/Users/Ирина Сулла/AppData/Local/Google/Chrome/User Data")
options.add_argument("--profile-directory=Default")

options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)


def parse_date(date_str):
    try:
        if date_str:
            return datetime.fromisoformat(date_str.replace("Z", ""))
    except:
        return None


def parse_message(msg):
    try:
        msg_id = msg.get_attribute("data-message-id")
        if not msg_id or msg_id in processed_messages:
            return None

        user_id = msg.get_attribute("data-peer-id") or msg.get_attribute("data-user-id")
        if not user_id:
            return None

        try:
            text = msg.find_element(By.CSS_SELECTOR, ".text-content").text
        except:
            return None

        if not text.strip():
            return None

        try:
            full_name = msg.find_element(By.CSS_SELECTOR, ".sender-title").text
        except:
            full_name = ""

        dt = msg.get_attribute("data-datetime")
        date = parse_date(dt)

        processed_messages.add(msg_id)

        return {
            "user_id": str(user_id),
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
            "messages": []
        }

    users[uid]["messages"].append(data["text"])


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


stop = False
last_count = 0

while True:

    messages = driver.find_elements(By.CSS_SELECTOR, "[data-message-id]")

    for msg in messages:
        data = parse_message(msg)
        if not data:
            continue

        if data["date"] and data["date"] < cutoff_date:
            stop = True
            break

        add_message(data)

    if stop:
        print("Достигли нужной даты")
        break

    if len(processed_messages) == last_count:
        print("Больше нет новых сообщений")
        break

    last_count = len(processed_messages)

    try:
        container = driver.find_element(By.CSS_SELECTOR, ".messages-container")
        driver.execute_script("arguments[0].scrollTop = 0;", container)
    except:
        driver.execute_script("window.scrollTo(0, 0);")

    time.sleep(random.uniform(1.5, 3.5))


rows = []

for user in users.values():
    rows.append({
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "message_count": len(user["messages"]),
        "messages": "\n\n---\n\n".join(user["messages"])
    })

df = pd.DataFrame(rows)
df.to_excel(OUTPUT_FILE, index=False)

print(f"Готово: {OUTPUT_FILE}")

driver.quit()