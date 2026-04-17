import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains


def get_driver(chrome_profile: str) -> webdriver.Chrome:
    options = Options()
    options.add_argument(f"user-data-dir={chrome_profile}")
    return webdriver.Chrome(options=options)


def get_wait(driver: webdriver.Chrome, timeout: int = 20) -> WebDriverWait:
    return WebDriverWait(driver, timeout)


def smart_scroll_up(driver: webdriver.Chrome, steps: int = 5, step_px: int = 300, pause: float = 0.4, final_pause: float = 3.0):
    try:
        chat = driver.find_element(By.CSS_SELECTOR, ".MessageList.custom-scroll")
        current = driver.execute_script("return arguments[0].scrollTop;", chat)

        for _ in range(steps):
            current -= step_px
            if current < 0:
                current = 0
            driver.execute_script("arguments[0].scrollTop = arguments[1];", chat, current)
            time.sleep(pause)

        time.sleep(final_pause)

    except Exception as e:
        print(f"Scroll error: {e}")


def real_click(driver: webdriver.Chrome, element):
    """Клик через ActionChains — не блокируется Telegram."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.5)
    ActionChains(driver).move_to_element(element).click().perform()