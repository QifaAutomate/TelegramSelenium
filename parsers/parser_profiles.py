import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import ProjectConfig
from core.browser import get_driver, smart_scroll_up, real_click
from core.excel import read_xlsx, write_xlsx


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


def open_profile(driver, wait, sender_span) -> bool:
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sender_span)
        time.sleep(2)
        real_click(driver, sender_span)
        print("  Клик по sender-title выполнен")

        time.sleep(4)

        opened = False
        for attempt in range(4):
            try:
                info_els = driver.find_elements(By.CSS_SELECTOR, ".MiddleHeader .info")
                if not info_els:
                    print(f"  Шапка не найдена (попытка {attempt + 1})")
                    time.sleep(2)
                    continue

                info_el = info_els[-1]
                real_click(driver, info_el)
                print(f"  Клик по шапке чата (попытка {attempt + 1})")

                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#RightColumn .close-button")
                ))
                opened = True
                break
            except Exception as e:
                print(f"  Панель не открылась: {e}")
                time.sleep(2)

        if not opened:
            print("  Панель профиля не открылась")
            return False

        time.sleep(1.5)
        return True

    except Exception as e:
        print("open_profile error:", e)
        return False


def get_username(driver) -> str:
    try:
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "div.multiline-item span.title")
        for item in items:
            text = item.text.strip()
            if text.startswith("@"):
                return text
        return ""
    except:
        return ""


def get_phone_number(driver) -> str:
    try:
        time.sleep(2)
        items = driver.find_elements(By.CSS_SELECTOR, "div.multiline-item")
        for item in items:
            subtitle = item.find_element(By.CSS_SELECTOR, "span.subtitle")
            if subtitle.text.strip() == "Phone":
                title = item.find_element(By.CSS_SELECTOR, "span.title")
                return title.text.strip()
        return ""
    except:
        return ""


def close_profile_and_go_back(driver, wait, chat_name: str):
    try:
        close_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#RightColumn .close-button")
        ))
        real_click(driver, close_btn)
        print("  Профиль закрыт")
        time.sleep(2)
    except Exception as e:
        print("  Ошибка закрытия профиля:", e)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".chat-item-clickable")))
        chat_items = driver.find_elements(By.CSS_SELECTOR, ".chat-item-clickable")
        for item in chat_items:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, "h3.fullName")
                if chat_name.lower() in title_el.text.lower():
                    real_click(driver, item)
                    print("  Вернулись в групповой чат")
                    time.sleep(3)
                    break
            except:
                continue
    except Exception as e:
        print("  Ошибка возврата в чат:", e)


def parse_profiles(config: ProjectConfig):
    driver = get_driver(config.chrome_profile)
    driver.get("https://web.telegram.org/a/")
    wait = WebDriverWait(driver, 20)

    time.sleep(3)

    if not open_chat(driver, wait, config.chat_name):
        print("Не удалось открыть чат, завершаем")
        driver.quit()
        return

    rows = read_xlsx(config.leads_file)
    sender_names = []
    for row in rows:
        name = row[0]
        if name and name not in sender_names:
            sender_names.append(name)
        if len(sender_names) >= config.max_profiles:
            break

    results = {name: {"username": "", "phone": ""} for name in sender_names}
    remaining = set(sender_names)

    print(f"Уникальных отправителей: {len(sender_names)}")
    print("Ищем:", remaining)

    seen_ids = set()
    no_growth_rounds = 0

    for i in range(1000):
        before_id = get_first_message_id(driver)
        messages = get_messages(driver)

        print(f"\nРаунд {i}, сообщений: {len(messages)}, осталось: {len(remaining)}")

        for msg in messages:
            try:
                msg_id = msg.get_attribute("id")
                if not msg_id or msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                sender_spans = msg.find_elements(By.CSS_SELECTOR, "span.sender-title")
                if not sender_spans:
                    continue

                sender = sender_spans[0].text.strip()
                if not sender:
                    continue

                matched = None
                for name in remaining:
                    if name.lower() == sender.lower():
                        matched = name
                        break

                if not matched:
                    continue

                print(f"  -> Найден: {matched} (msg_id: {msg_id})")

                if open_profile(driver, wait, sender_spans[0]):
                    username = get_username(driver)
                    phone = get_phone_number(driver)
                    print(f"  Username: {username if username else 'нет публичного юзернейма'}")
                    print(f"  Phone: {phone if phone else 'нет номера телефона'}")
                    results[matched]["username"] = username