
import time
import random
from openpyxl import load_workbook, Workbook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

INPUT_FILE = "telegram_messages.xlsx"
OUTPUT_FILE = "telegram_profiles_test.xlsx"

options = Options()
options.add_argument(r"user-data-dir=C:\selen2")

driver = webdriver.Chrome(options=options)
driver.get("https://web.telegram.org/a/")

input("Открой чат и нажми Enter")

wait = WebDriverWait(driver, 20)


def get_chat():
    return wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".messages-container"))
    )


def get_messages():
    return driver.find_elements(
        By.CSS_SELECTOR,
        "div[id^='message-']:not([id^='message-group-'])"
    )


def get_first_message_id():
    try:
        msgs = get_messages()
        return msgs[0].get_attribute("id") if msgs else None
    except:
        return None

def scroll_up():
    for _ in range(15):
        try:
            chat = get_chat()
            current = driver.execute_script(
                "return arguments[0].scrollTop;", chat
            )
            new_pos = max(0, current - 300)
            driver.execute_script(
                "arguments[0].scrollTop = arguments[1];",
                chat, new_pos
            )
        except:
            pass
        time.sleep(0.4)


def find_user_message(user):
    no_change = 0
    while True:
        before = get_first_message_id()
        for msg in get_messages():
            try:
                sender = msg.find_element(By.CSS_SELECTOR, ".sender-title").text.strip()
                if user.lower() in sender.lower():
                    return msg
            except:
                continue
        scroll_up()
        time.sleep(1.5)
        after = get_first_message_id()
        if after == before:
            no_change += 1
        else:
            no_change = 0
        if no_change >= 3:
            return None


def open_profile(msg):
    try:
        clickable = msg.find_element(
            By.CSS_SELECTOR,
            ".message-title-name-container"
        )
        driver.execute_script("arguments[0].click();", clickable)

        wait.until(EC.presence_of_element_located((By.XPATH, "//span")))
        time.sleep(1.5)

        return True
    except:
        return False


def get_phone():
    try:
        elem = driver.find_element(
            By.XPATH,
            "//span[contains(text(),'Phone')]/preceding-sibling::span"
        )
        return elem.text.strip()
    except:
        return ""


def close_profile():
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys("\uE00C")  # ESC
        time.sleep(1)
    except:
        pass


wb = load_workbook(INPUT_FILE)
ws = wb.active

users = []

for row in ws.iter_rows(min_row=2, values_only=True):
    name = row[0]
    if name and name not in users:
        users.append(name)

users = users[:15]


out_wb = Workbook()
out_ws = out_wb.active
out_ws.append(["Отправитель", "Телефон"])


found = 0

for i, user in enumerate(users, 1):
    print(f"\n{i}/{len(users)} -> {user}")

    msg = find_user_message(user)

    if not msg:
        print("Не найден")
        out_ws.append([user, ""])
        continue

    if not open_profile(msg):
        print("Не открылся профиль")
        out_ws.append([user, ""])
        continue

    phone = get_phone()

    print("Телефон:", phone if phone else "нет")

    if phone:
        found += 1

    out_ws.append([user, phone])

    close_profile()
    time.sleep(random.uniform(1.5, 3))


out_wb.save(OUTPUT_FILE)

print("\nГотово")
print("Найдено телефонов:", found)

import time
import random
from openpyxl import load_workbook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

FILE = "telegram_messages.xlsx"

options = Options()
options.add_argument(r"user-data-dir=C:\selen")
driver = webdriver.Chrome(options=options)
driver.get("https://web.telegram.org/a/")
input("Enter (открой нужный чат)")

wb = load_workbook(FILE)
ws = wb.active

if ws.cell(row=1, column=3).value != "Телефон":
    ws.cell(row=1, column=3).value = "Телефон"

users = []
rows_map = {}

for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
    sender = row[0]
    if sender and sender not in users:
        users.append(sender)
        rows_map[sender] = i

users = users[:15]

for user in users:
    print("Пользователь", user)

    messages = driver.find_elements(By.CSS_SELECTOR,"div[id^='message-']:not([id^='message-group-'])")
    target_msg = None
    for msg in messages:
        try:
            sender = msg.find_element(By.CSS_SELECTOR, ".sender-title").text.strip()
            if sender == user:
                target_msg = msg
                break
        except:
            continue

    if not target_msg:
        print("Не найден в текущем DOM:", user)
        continue

    try:
        name_container = target_msg.find_element(By.CSS_SELECTOR,".message-title-name-container.interactive")
        driver.execute_script("arguments[0].click();", name_container)
        time.sleep(2)
    except Exception as e:
        print("Ошибка открытия профиля:", e)
        continue

    phone = ""

    try:
        phone_elem = driver.find_element(By.XPATH,"//span[text()='Phone']/preceding-sibling::span")
        phone = phone_elem.text.strip()
    except:
        phone = ""

    print("Телефон:", phone if phone else "не найден")

    row_index = rows_map[user]
    ws.cell(row=row_index, column=3).value = phone

    driver.back()
    time.sleep(random.uniform(3, 6))

wb.save(FILE)
print("\nГотово. Данные сохранены.")
driver.quit()