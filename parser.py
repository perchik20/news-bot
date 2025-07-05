from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import asyncio
from collections import deque
import re
import json
import os

from config import options, DESC_TITEL_XPATH, bot, log, FILENAME, DEBUG_ID
from key_words import k_w
from db_funcs import get_users_by_chatid

def load_seen_urls():
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, "r") as f:
                data = json.load(f)
                return deque(data, maxlen=50)
        except json.JSONDecodeError:
            # Файл существует, но пуст или повреждён — игнорируем
            return deque(maxlen=50)
    return deque(maxlen=50)

def save_seen_urls(seen_urls):
    with open(FILENAME, "w") as f:
        json.dump(list(seen_urls), f)
        
async def fetch_news(chat_id: int, main_url: str, ticker: str, stop_event: asyncio.Event) -> None:
    main_url = main_url.replace('"', '')
    seen_urls = load_seen_urls()
    iteration = 0
    max_iterations = 100

    driver = None
    
    while not stop_event.is_set():
        # print(main_url, iteration)
        try:
            # Перезапускаем браузер при достижении лимита итераций или если он не был создан
            if driver is None or iteration >= max_iterations:
                if driver:
                    await asyncio.to_thread(driver.quit)
                service = Service(ChromeDriverManager().install())
                # service = Service("/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=options)
                iteration = 0

            # --- Основная логика ---
            await asyncio.to_thread(driver.get, main_url)
            wait = WebDriverWait(driver, 50)
            urls = {}
            try:
                for num in range(6, 1, -1):
                    xpath = f'//*[@id="cont_wrap"]/div[4]/div[2]/div/div[2]/table/tbody/tr[{num}]/td[3]/a'
                    elem = await asyncio.to_thread(wait.until, EC.presence_of_element_located((By.XPATH, xpath)))
                    
                    title = elem.text
                    
                    url = await asyncio.to_thread(elem.get_attribute, "href")
                    print(f'---------\n{ticker}\nNews {num} - title {title} - link {url}')
                    if url and title in k_w and url not in seen_urls:
                        # print('{', f'{title}: {url}', '}')
                        urls.update({title: url})
                        
            except Exception as ex:
                error_text = "Не найден элемент по XPATH-1. Возможно, изменился путь или страница не загрузилась полностью."
                await bot.send_message(DEBUG_ID, error_text)
                log.error(error_text, exc_info=ex)

            if urls:
                print(urls)
                for title, url in urls.items():

                    seen_urls.append(url)
                    save_seen_urls(seen_urls)
                    await asyncio.to_thread(driver.get, url)

                    try:
                        elem2 = await asyncio.to_thread(wait.until, EC.presence_of_element_located((By.XPATH, DESC_TITEL_XPATH)))
                    
                    except Exception as ex:
                        error_text = "Не найден элемент по XPATH-2. Возможно, изменился путь или страница не загрузилась полностью."
                        await bot.send_message(DEBUG_ID, error_text)
                        log.error(error_text, exc_info=ex)
                        
                    full_text = elem2.text

                    match = re.search(r'2\. Содержание сообщения(.*?)3\. Подпись', full_text, re.DOTALL)
                    try:
                        if match:
                            content = match.group(1).strip()
                            full_text = f"#{ticker}\n\n{title}\n\n{content}\n\nСсылка на полную новость: {url}"
                            print(full_text)
                            print(ticker)
                            for user_id in set(get_users_by_chatid(ticker)):
                                print(user_id)
                                if len(full_text) > 4096:
                                    await bot.send_message(user_id, f'{full_text[0:3984]}\n\nСсылка на полную новость:{url}')
                                else:
                                    await bot.send_message(user_id, full_text)
                                    
                    except Exception as ex:
                        error_text = "Не удалось найти нужный фрагмент."
                        await bot.send_message(DEBUG_ID, error_text)
                        log.error(error_text, exc_info=ex)
            
        except Exception as ex:
            error_text = "Ошибка внутри парсера новостей"
            await bot.send_message(DEBUG_ID, error_text)
            log.error(error_text, exc_info=ex)
            
            if driver:
                await asyncio.to_thread(driver.quit)
            driver = None  # заставит создать браузер заново

        iteration += 1
        # print(100*'//', iteration)
        await asyncio.sleep(5)

    # Завершаем работу — закрываем браузер
    if driver:
        await asyncio.to_thread(driver.quit)
