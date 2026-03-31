import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


GROUP_URL = "https://web.telegram.org/a/#-1002429877587"
OUTPUT_FILE = "telegram_messages.xlsx"


options = Options()
options.add_argument(r"--user-data-dir=C:\selenium_profile")
options.add_argument("--profile-directory=Default")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 40)


driver.get(GROUP_URL)


# ЖДЁМ ИМЕННО СООБЩЕНИЯ (не canvas, не input!)
wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//div[@data-message-id]")
    )
)

print("Чат открыт, начинаю парсинг...")


# контейнер скролла
scroll_container = wait.until(
    EC.presence_of_element_located(
        (By.XPATH, "//div[contains(@class,'Scrollable')]")
    )
)


data = []
seen_ids = set()


for i in range(30):  # сколько "экранов" прокрутить
    messages = driver.find_elements(By.XPATH, "//div[@data-message-id]")

    for msg in messages:
        try:
            message_id = msg.get_attribute("data-message-id")
            if not message_id or message_id in seen_ids:
                continue

            seen_ids.add(message_id)

            # текст
            try:
                text = msg.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'text-content')]"
                ).text.strip()
            except:
                continue

            if not text:
                continue

            # пользователь
            try:
                user = msg.find_element(
                    By.XPATH,
                    ".//span[contains(@class,'message-title')]"
                ).text.strip()
            except:
                user = "unknown"

            data.append({
                "id": message_id,
                "user": user,
                "message": text
            })

        except:
            continue

    print(f"Шаг {i+1}: собрано {len(data)} сообщений")

    # прокрутка вверх
    driver.execute_script("arguments[0].scrollTop = 0;", scroll_container)
    time.sleep(1.5)


df = pd.DataFrame(data)
df.to_excel(OUTPUT_FILE, index=False)

print("Готово:", OUTPUT_FILE)

driver.quit()