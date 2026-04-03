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