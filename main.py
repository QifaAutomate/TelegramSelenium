import time
import re
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

# ========== НАСТРОЙКИ ==========
CHAT_NAME = "WB Партнёры — чат"               # Точное имя чата
DAYS_BACK = 1                                 # За сколько дней собирать
COLLECT_PHONE = True                   # Собирать ли телефон (замедляет работу)
FIREFOX_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
PROFILE_PATH = r"C:\Users\001841\AppData\Roaming\Mozilla\Firefox\Profiles\7yx65i0f.default-release"
# ================================

def safe_filename(s):
    return re.sub(r'[\\/*?:"<>|]', "", s).replace(" ", "_")

cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)
period_str = f"за_{DAYS_BACK}_день" if DAYS_BACK == 1 else f"за_{DAYS_BACK}_дней"
safe_chat_name = safe_filename(CHAT_NAME)
excel_file = f"telegram_users_{safe_chat_name}_{period_str}.xlsx"

print(f"Период: {period_str}, сообщения не старше {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")

# Настройка Firefox
firefox_options = Options()
firefox_options.binary_location = FIREFOX_PATH
firefox_options.add_argument("-profile")
firefox_options.add_argument(PROFILE_PATH)

service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=firefox_options)

# Глобальные переменные для сохранения при прерывании
users = {}
processed_messages = set()

def save_data():
    """Сохраняет текущие данные в Excel (для защиты при ошибках)"""
    if users:
        data_list = list(users.values())
        df = pd.DataFrame(data_list)
        df["message_count"] = df["messages"].apply(lambda x: x.count("\n") + 1)
        df.to_excel(excel_file, index=False)
        print(f"\n[Сохранено] Данные записаны в {excel_file} (пользователей: {len(users)})")

try:
    driver.get("https://web.telegram.org")
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Страница загружена")

    # Ждём появления списка чатов
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ListItem.Chat")))
    print("Список чатов найден")

    # Закрываем возможные оверлеи
    try:
        overlay = driver.find_element(By.CSS_SELECTOR, ".oL7XcRwI")
        if overlay.is_displayed():
            print("Обнаружен оверлей, закрываем...")
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, ".close-button, [aria-label='Close']")
                close_btn.click()
                time.sleep(1)
            except:
                pass
            WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".oL7XcRwI")))
    except:
        pass

    # Активация интерфейса (клик по первому чату)
    print("Активируем интерфейс...")
    first_chat = driver.find_element(By.CSS_SELECTOR, ".ListItem.Chat")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_chat)
    time.sleep(0.5)
    try:
        first_chat.click()
    except:
        driver.execute_script("arguments[0].click();", first_chat)

    # Ждём загрузки хотя бы одного сообщения в первом чате
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".Message, .message, .im-message, [data-message-id], .content-inner")))
    print("Интерфейс активен")

    # Поиск целевого чата
    print(f"Ищем чат '{CHAT_NAME}'...")
    # Сначала скроллим список чатов, чтобы найти
    chat_list = driver.find_element(By.CSS_SELECTOR, ".chatlist-wrapper, .chat-list")
    driver.execute_script("arguments[0].scrollTop = 0", chat_list)  # в начало списка
    time.sleep(1)

    target_chat = None
    for _ in range(3):  # несколько попыток с прокруткой
        chats = driver.find_elements(By.CSS_SELECTOR, ".ListItem.Chat")
        for chat in chats:
            try:
                name_elem = chat.find_element(By.CSS_SELECTOR, "h3.fullName")
                if CHAT_NAME in name_elem.text:
                    target_chat = chat
                    break
            except:
                continue
        if target_chat:
            break
        # прокручиваем список вниз
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", chat_list)
        time.sleep(2)

    if not target_chat:
        raise Exception(f"Чат '{CHAT_NAME}' не найден.")

    # Открываем целевой чат
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_chat)
    time.sleep(1)
    try:
        target_chat.click()
    except:
        driver.execute_script("arguments[0].click();", target_chat)

    # Ждём загрузки сообщений
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".Message, .message, .im-message, [data-message-id], .content-inner")))
    print(f"Чат '{CHAT_NAME}' открыт")

    # Функции парсинга
    def parse_date(date_str):
        try:
            if '.' in date_str:
                date_str = date_str.split('.')[0]
            if '+' in date_str:
                date_str = date_str.split('+')[0]
            if 'Z' in date_str:
                date_str = date_str.replace('Z', '')
            return datetime.fromisoformat(date_str)
        except:
            return None

    def get_user_phone(user_id):
        """Пытается извлечь телефон из профиля (опционально, замедляет)"""
        if not COLLECT_PHONE:
            return ""
        try:
            # Клик на аватарку/имя пользователя (нужно найти элемент)
            # Это сложно и медленно, для простоты вернём пустую строку
            # Можно реализовать позже, если нужно
            return ""
        except:
            return ""

    def parse_message(msg_element):
        try:
            # user_id
            user_id = msg_element.get_attribute("data-user-id")
            if not user_id:
                # пробуем взять из аватарки
                try:
                    avatar = msg_element.find_element(By.CSS_SELECTOR, ".Avatar[data-peer-id]")
                    user_id = avatar.get_attribute("data-peer-id")
                except:
                    pass
            if not user_id:
                return None

            # username
            username = ""
            try:
                username_elem = msg_element.find_element(By.CSS_SELECTOR, ".sender-title, .peer-name, .author")
                username = username_elem.text.strip()
            except:
                pass

            # текст
            try:
                text_elem = msg_element.find_element(By.CSS_SELECTOR, ".text-content, .message-text")
                message_text = text_elem.text.strip()
            except:
                message_text = ""

            # дата
            msg_date = None
            dt_attr = msg_element.get_attribute("data-datetime")
            if dt_attr:
                msg_date = parse_date(dt_attr)
            else:
                # пробуем извлечь время из .message-time (только время, не полная дата)
                try:
                    time_elem = msg_element.find_element(By.CSS_SELECTOR, ".message-time")
                    time_str = time_elem.text.strip()
                    # Если нет полной даты, пропускаем (не будем фильтровать)
                except:
                    pass

            phone = get_user_phone(user_id) if COLLECT_PHONE else ""

            return {
                "user_id": user_id,
                "username": username,
                "phone": phone,
                "message": message_text,
                "date": msg_date
            }
        except Exception as e:
            return None

    def add_message_to_user(user_data):
        uid = user_data["user_id"]
        msg = user_data["message"]
        if uid in users:
            users[uid]["messages"] += f"\n{msg}"
        else:
            users[uid] = {
                "user_id": uid,
                "username": user_data["username"],
                "phone": user_data["phone"],
                "messages": msg
            }

    # Прокрутка истории (вниз, в прошлое)
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    stop_scroll = False
    print("Начинаем сбор сообщений (прокрутка истории)...")

    while scroll_attempts < 20 and not stop_scroll:
        # Получаем все сообщения (используем гибкие селекторы)
        messages = []
        for selector in [".Message", ".message", ".im-message", "[data-message-id]", ".content-inner"]:
            messages = driver.find_elements(By.CSS_SELECTOR, selector)
            if messages:
                break

        current_count = len(messages)
        print(f"Найдено сообщений: {current_count}, уникальных ID: {len(processed_messages)}, пользователей: {len(users)}")

        # Обрабатываем новые сообщения
        oldest_in_batch = None
        for msg in messages:
            msg_id = msg.get_attribute("data-message-id")
            if msg_id and msg_id in processed_messages:
                continue

            data = parse_message(msg)
            if data:
                if data["date"] and data["date"] < cutoff_date:
                    print(f"Достигнута граница: сообщение от {data['date']}. Останавливаем сбор.")
                    stop_scroll = True
                    break
                add_message_to_user(data)

            if msg_id:
                processed_messages.add(msg_id)

            if data and data["date"]:
                if oldest_in_batch is None or data["date"] < oldest_in_batch:
                    oldest_in_batch = data["date"]

        if oldest_in_batch and oldest_in_batch < cutoff_date:
            stop_scroll = True

        if stop_scroll:
            break

        # Прокручиваем вниз (к старым сообщениям)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # пауза для загрузки

        # Проверяем, изменилась ли высота (если нет — больше не грузится)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
            print(f"Высота не изменилась ({scroll_attempts}/20)")
        else:
            scroll_attempts = 0
            last_height = new_height

        # Сохраняем промежуточные результаты каждые 5 итераций (на случай прерывания)
        if len(processed_messages) % 50 == 0:
            save_data()

    print(f"\nСбор завершён. Всего сообщений: {len(processed_messages)}, уникальных пользователей: {len(users)}")

    # Финальное сохранение
    save_data()

except KeyboardInterrupt:
    print("\nПрерывание пользователем. Сохраняем набранные данные...")
    save_data()

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
    save_data()

finally:
    driver.quit()
    # Ещё раз сохраняем на всякий случай
    save_data()