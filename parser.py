from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import asyncio
from collections import deque
import re

from config import options, CHANNEL_ID, DESC_TITEL_XPATH, TITEL_XPATH, bot, log


async def fetch_news(chat_id: int, main_url: str, ticker: str, stop_event: asyncio.Event) -> None:
    main_url = main_url.replace('"', '')
    seen_urls = deque(maxlen=10)
    iteration = 0
    max_iterations = 100

    driver = None

    while not stop_event.is_set():
        try:
            # Перезапускаем браузер при достижении лимита итераций или если он не был создан
            if driver is None or iteration >= max_iterations:
                if driver:
                    await asyncio.to_thread(driver.quit)
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                iteration = 0

            # --- Основная логика ---
            await asyncio.to_thread(driver.get, main_url)
            wait = WebDriverWait(driver, 20)

            elem = await asyncio.to_thread(wait.until, EC.presence_of_element_located((By.XPATH, TITEL_XPATH)))
            title = elem.text
            url = await asyncio.to_thread(elem.get_attribute, "href")

            if url and url not in seen_urls:
                seen_urls.append(url)
                await asyncio.to_thread(driver.get, url)

                elem2 = await asyncio.to_thread(
                    wait.until,
                    EC.presence_of_element_located((By.XPATH, DESC_TITEL_XPATH))
                )
                full_text = elem2.text

                match = re.search(r'2\. Содержание сообщения(.*?)3\. Подпись', full_text, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    full_text = f"#{ticker}\n\n{title}\n\n{content}\n\nСсылка на полную новость: {url}"
                    await bot.send_message(CHANNEL_ID, full_text)
                else:
                    print("Не удалось найти нужный фрагмент.")

        except Exception as ex:
            log.error("Ошибка внутри блока fetch_news:", exc_info=ex)
            if driver:
                await asyncio.to_thread(driver.quit)
            driver = None  # заставит создать браузер заново

        iteration += 1
        # print(100*'//', iteration)
        await asyncio.sleep(5)
        

    # Завершаем работу — закрываем браузер
    if driver:
        await asyncio.to_thread(driver.quit)
