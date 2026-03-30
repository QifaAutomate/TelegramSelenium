import time
import random
import pandas as pd
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


CHAT_NAME = "WB Партнёры — чат"
INPUT_FILE = "telegram_raw.xlsx"
OUTPUT_FILE = "telegram_enriched.xlsx"

MAX_USERS = 15

CHROME_PROFILE_PATH = r"C:\Users\Ирина Сулла\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR = "Default"


df = pd.read_excel(INPUT_FILE)

df = df.sort_values(by="message_count", ascending=False)
users = df.to_dict("records")[:MAX_USERS]


options = Options()
options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
options.add_argument(f"--profile-directory={PROFILE_DIR}")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)


def normalize_phone(text):
    match = re.search(r'\+?\d[\d\s\-\(\)]{10,20}', text)
    return match.group(0) if match else ""


def match_user(msg, target):
    msg_uid = msg.get_attribute("data-peer-id") or msg.get_attribute("data-user-id")

    if str(msg_uid) == str(target["user_id"]):
        return True

    try:
        name = msg.find_element(By.CSS_SELECTOR, ".sender-title").text.lower()
        if target["full_name"] and target["full_name"].lower() in name:
            return True
    except:
        pass

    return False


def open_profile(msg):
    try:
        avatar = msg.find_element(By.CSS_SELECTOR, "[data-peer-id]")
        avatar.click()
        time.sleep(random.uniform(1.5, 2.5))
        return True
    except:
        return False


def extract_profile():
    username = ""
    phone = ""

    try:
        elems = driver.find_elements(By.XPATH, "//*[contains(text(),'@')]")
        for el in elems:
            text = el.text.strip()
            if text.startswith("@"):
                username = text
                break

        elems = driver.find_elements(By.XPATH, "//*[contains(text(), '+')]")
        for el in elems:
            phone = normalize_phone(el.text)
            if phone:
                break

    except:
        pass

    return username, phone


def close_profile():
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(random.uniform(0.5, 1.5))


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


results = []

for user in users:
    print(f"\nОбрабатываем {user['user_id']}")

    found = False

    for _ in range(30):

        messages = driver.find_elements(By.CSS_SELECTOR, "[data-message-id]")

        for msg in messages:
            if match_user(msg, user):

                if open_profile(msg):
                    username, phone = extract_profile()
                    close_profile()

                    user["username"] = username
                    user["phone"] = phone

                    print(f"username: {username}, phone: {phone}")

                    results.append(user)

                    time.sleep(random.uniform(3, 6))

                    found = True
                    break

        if found:
            break

        try:
            container = driver.find_element(By.CSS_SELECTOR, ".messages-container")
            driver.execute_script("arguments[0].scrollTop = 0;", container)
        except:
            driver.execute_script("window.scrollTo(0, 0);")

        time.sleep(random.uniform(2, 4))

    if not found:
        print("не найден")

df_out = pd.DataFrame(results)
df_out.to_excel(OUTPUT_FILE, index=False)

print(f"Готово: {OUTPUT_FILE}")

driver.quit()