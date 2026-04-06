import time
import random
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OUTPUT_FILE = "telegram_messages_new.xlsx"
wb = Workbook()
ws = wb.active
ws.append(["Отправитель", "Все сообщения"])

options = Options()
options.add_argument(r"user-data-dir=C:\selen2")
driver = webdriver.Chrome(options=options)
driver.get("https://web.telegram.org/a/")

input("Enter")

chat = driver.find_element(By.CSS_SELECTOR, ".messages-container")

def smart_scroll_up(chat):
    current = driver.execute_script("return arguments[0].scrollTop;", chat)

    for _ in range(5):
        current -= 300
        if current < 0:
            current = 0

        driver.execute_script(
            "arguments[0].scrollTop = arguments[1];",
            chat, current
        )
        time.sleep(0.3)


def get_first_message_id():
    messages = driver.find_elements(
        By.CSS_SELECTOR,
        "div[id^='message-']:not([id^='message-group-'])"
    )
    if not messages:
        return None
    return messages[0].get_attribute("id")


time.sleep(2)

seen_ids = set()
no_growth_rounds = 0
last_sender = "Unknown"
user_messages = {}

prev_first_id = None


for _ in range(100):

    before_id = get_first_message_id()

    smart_scroll_up(chat)
    time.sleep(random.uniform(1.5, 2.5))

    after_id = get_first_message_id()

    messages = driver.find_elements(
        By.CSS_SELECTOR,
        "div[id^='message-']:not([id^='message-group-'])"
    )

    current_count = len(messages)
    print("Сообщений:", current_count)

    for msg in messages:
        raw_id = msg.get_attribute("id")
        if not raw_id:
            continue

        msg_id = raw_id.strip()

        if msg_id in seen_ids:
            continue

        seen_ids.add(msg_id)

        sender_elements = msg.find_elements(By.CSS_SELECTOR, ".sender-title")
        if sender_elements:
            sender = sender_elements[0].text.strip()
            last_sender = sender
        else:
            sender = last_sender

        if not sender:
            sender = last_sender or "Unknown"

        text_elements = msg.find_elements(By.CSS_SELECTOR, ".text-content")
        if text_elements:
            text = text_elements[0].text.strip()
        else:
            continue

        if not text:
            continue

        if sender not in user_messages:
            user_messages[sender] = []

        user_messages[sender].append({
            "id": msg_id,
            "text": text
        })

        print("OK:", msg_id, sender, text)

    # --- НОВАЯ логика остановки ---
    if after_id == before_id:
        no_growth_rounds += 1
        print("Нет сдвига вверх:", no_growth_rounds)
    else:
        no_growth_rounds = 0

    if no_growth_rounds >= 5:
        print("Достигнут верх истории")
        break


for sender in sorted(user_messages.keys()):
    messages = user_messages[sender]
    all_text = "\n\n".join(msg["text"] for msg in messages)
    ws.append([sender, all_text])

wb.save(OUTPUT_FILE)
print("Готово:", OUTPUT_FILE)

driver.quit()