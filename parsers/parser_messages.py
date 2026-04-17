import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import ProjectConfig
from core.browser import get_driver, smart_scroll_up
from core.excel import write_xlsx


def open_chat(driver, wait, name: str) -> bool:
    try:
        search = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#telegram-search-input")))
        search.click()
        search.send_keys(name)
        time.sleep(3)
        result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".chat-item-clickable.search-result")))
        result.click()
        time.sleep(3)
        print(f"Чат '{name}' открыт")
        return True
    except Exception as e:
        print("Не удалось открыть чат:", e)
        return False


def get_messages(driver):
    return driver.find_elements(
        By.CSS_SELECTOR,
        "div[id^='message-']:not([id^='message-group-'])"
    )


def get_first_message_id(driver):
    messages = get_messages(driver)
    return messages[0].get_attribute("id") if messages else None


def parse_messages(config: ProjectConfig):
    driver = get_driver(config.chrome_profile)
    driver.get("https://web.telegram.org/a/")
    wait = WebDriverWait(driver, 20)

    time.sleep(3)

    if not open_chat(driver, wait, config.chat_name):
        print("Не удалось открыть чат, завершаем")
        driver.quit()
        return

    time.sleep(2)

    seen_ids = set()
    last_sender = "Unknown"
    user_messages = {}
    no_growth_rounds = 0

    for i in range(config.max_scroll_rounds):
        before_id = get_first_message_id(driver)
        messages = get_messages(driver)

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

        rows = [[sender, "\n\n".join(user_messages[sender])] for sender in sorted(user_messages.keys())]
        write_xlsx(config.messages_file, ["Отправитель", "Все сообщения"], rows)
        print(f"Сохранено: {len(user_messages)} пользователей")

        if len(user_messages) >= config.target_users:
            print(f"Достигнуто {config.target_users} уникальных пользователей")
            break

        smart_scroll_up(driver, final_pause=3.0)

        after_id = get_first_message_id(driver)
        print(f"before: {before_id} | after: {after_id}")

        if after_id == before_id:
            no_growth_rounds += 1
            print(f"Нет сдвига: {no_growth_rounds}/{config.no_growth_limit}")
        else:
            no_growth_rounds = 0

        if no_growth_rounds >= config.no_growth_limit:
            print("Достигнут верх чата")
            break

    driver.quit()