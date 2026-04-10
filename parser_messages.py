import time
import random
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_FILE = "telegram_messages_new.xlsx"

wb = Workbook()
ws = wb.active
ws.append(["Отправитель", "Все сообщения"])

options = Options()
options.add_argument(r"user-data-dir=C:\papka")

driver = webdriver.Chrome(options=options)
driver.get("https://web.telegram.org/a/")
input("Enter")

def get_chat():
    return driver.find_element(By.CSS_SELECTOR, ".MessageList.custom-scroll")

def get_messages():
    return driver.find_elements(
        By.CSS_SELECTOR,
        "div[id^='message-']:not([id^='message-group-'])"
    )

def get_first_message_id():
    messages = get_messages()
    return messages[0].get_attribute("id") if messages else None

def smart_scroll_up():
    try:
        chat = driver.find_element(By.CSS_SELECTOR, ".MessageList.custom-scroll")
        current = driver.execute_script("return arguments[0].scrollTop;", chat)

        for _ in range(5):
            current -= 00
            if current < 0:
                current = 0
            driver.execute_script(
                "arguments[0].scrollTop = arguments[1];",
                chat, current
            )
            time.sleep(0.4)

        # ждём пока Telegram подгрузит старые сообщения в DOM
        time.sleep(3)

    except Exception as e:
        print("Scroll error:", e)

time.sleep(2)

seen_ids = set()
last_sender = "Unknown"
user_messages = {}
no_growth_rounds = 0

for i in range(100):
    before_id = get_first_message_id()
    messages = get_messages()
    
    print(f"Раунд {i}, найдено сообщений: {len(messages)}, first_id: {before_id}")

    for msg in messages:
        try:
            msg_id = msg.get_attribute("id")
            if not msg_id or msg_id in seen_ids:
                continue

            seen_ids.add(msg_id)

            sender_elements = msg.find_elements(
                By.CSS_SELECTOR,
                ".message-title-name-container"
            )

            if sender_elements:
                sender = sender_elements[0].text.strip()
                last_sender = sender
            else:
                sender = last_sender

            if not sender:
                sender = last_sender or "Unknown"

            text_elements = msg.find_elements(By.CSS_SELECTOR, ".text-content")
            if not text_elements:
                continue

            text = text_elements[0].text.strip()
            if not text:
                continue

            user_messages.setdefault(sender, []).append(text)
            print("OK:", msg_id, sender)

        except:
            continue

    smart_scroll_up()

    after_id = get_first_message_id()
    print(f"before: {before_id} | after: {after_id}")

    if after_id == before_id:
        no_growth_rounds += 1
        print("Нет сдвига:", no_growth_rounds)
    else:
        no_growth_rounds = 0

    if no_growth_rounds >= 8:
        print("Достигнут верх")
        break

for sender in sorted(user_messages.keys()):
    all_text = "\n\n".join(user_messages[sender])
    ws.append([sender, all_text])

wb.save(OUTPUT_FILE)
print("Готово:", OUTPUT_FILE)
driver.quit()