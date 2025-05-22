import asyncio
import logging
import sys
from os import getenv
from collections import deque
import re
# import asyncio

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from aiogram import types

options = webdriver.ChromeOptions()
#     options.add_argument("--headless=new")
options.add_argument(f"--window-size=1920x1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# driver.implicitly_wait(10)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

TOKEN = getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не установлена")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для хранения фоновых задач по chat_id
tasks: dict[int, asyncio.Task] = {}
seen_urls = deque(maxlen=10)

TITEL_XPATH = '//*[@id="cont_wrap"]/div[4]/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/a'
# qqqqx5qqqqqq= '//*[@id="cont_wrap"]/div[2]/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/a' Другое описание - структура
#Примеры на строке 44 и 46-47. Удалить если что
# qqqqlkohqqq= '//*[@id="cont_wrap"]/div[4]/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/a'
# qqqqgazpqqq= '//*[@id="cont_wrap"]/div[4]/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/a'
DESC_TITEL_XPATH = '//*[@id="cont_wrap"]/div[2]'


CHANNEL_ID = "-1002354540369"

ALLOWED_USERS = {"prich_x", "FFMFak"}

company_urls = {}

async def fetch_news(chat_id: int) -> None:
    """
    Асинхронно обходит страницу событий и, если находит новое событие,
    переходит по ссылке и вытаскивает нужный блок текста.
    """
    try:
        while True:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            # 1) Открываем главную страницу
            for company_name in company_urls:
                await asyncio.to_thread(driver.get, company_urls[company_name])
                print(company_urls[company_name])
                wait = WebDriverWait(driver, 20)

                # 2) Ждём появления нужного элемента
                try:
                    elem = await asyncio.to_thread(wait.until, EC.presence_of_element_located((By.XPATH, TITEL_XPATH)))
                except Exception as ex:
                    log.error("Не удалось получить доступ к странице событий", exc_info=ex)
                    return

                title = elem.text

                # 3) Берём ссылку
                try:
                    url = await asyncio.to_thread(elem.get_attribute, "href")
                except Exception as ex:
                    log.error("Не удалось получить ссылку на событие", exc_info=ex)
                    return

                # 4) Если ссылка новая — переходим и парсим описание
                if url not in seen_urls:
                    seen_urls.append(url)
                    await asyncio.to_thread(driver.get, url)

                    try:
                        elem2 = await asyncio.to_thread(
                            wait.until,
                            EC.presence_of_element_located((By.XPATH, DESC_TITEL_XPATH))
                        )
                    except Exception as ex:
                        log.error("Не удалось получить доступ к странице описания события", exc_info=ex)
                        return

                    full_text = elem2.text

                    # 5) Регэксп для нужного блока
                    try:
                        match = re.search(r'2\. Содержание сообщения(.*?)3\. Подпись', full_text, re.DOTALL)
                        if match:
                            content = match.group(1).strip()
                            # print(content)
                        else:
                            print("Не удалось найти нужный фрагмент.")
                    except Exception as ex:
                        log.error("Не удалось вытащить текст из описания события", exc_info=ex)
                        return

                    # 6) Выводим результат
                    full_text = f"#{company_name}\n\n{title}\n\n{content}\n\nСсылка на полную новость: {url}"
                    await bot.send_message(CHANNEL_ID, full_text)
            await asyncio.sleep(5)
    except Exception as ex:
        log.info(f"Задача для чата {chat_id} отменена.")
        log.error("Ошибка внутри блока fetch_full_text:", exc_info=ex)
        
    finally:
        await driver.quit()


# async def send_hello_loop(chat_id: int):
#     try:
#         while True:
#             await bot.send_message(chat_id, "Привет, мир!")
#             await asyncio.sleep(5)
#     except asyncio.CancelledError:
#         # Задача отменена — можно тут что-то залогировать, если нужно
#         pass


@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    chat_id = message.chat.id
    print(20*'-->>', chat_id)
    if chat_id in tasks and not tasks[chat_id].done():
        await message.answer("Цикл уже запущен!")
        return

    task = asyncio.create_task(fetch_news(chat_id))
    tasks['parser_working'] = task
    await message.answer("Запустил отправку новостей")
    # else:
        # await message.answer("Нет компаний для запуска парсинга")     
    

@dp.message(Command(commands=["stop"]))
async def cmd_stop(message: Message):
    # chat_id = message.chat.id
    task = tasks.get('parser_working')
    if not task or task.done():
        await message.answer("Нечего останавливать — цикл не запущен.")
        return
    task.cancel()
    await message.answer("Остановил цикл отправки.")
    # Можно убрать задачу из словаря
    del tasks['parser_working']


@dp.message(F.text)
async def handle_company_message(message: types.Message):
    user = message.from_user
    '''
    Сделать удаление добавленных компаний
    '''
    # Проверка, разрешён ли пользователь
    if user.username not in ALLOWED_USERS:
        await message.answer("У вас нет прав для отправки данных.")
        return
    pattern = re.compile( r'^компания:\s+#([A-Z0-9]+)\s*-\s*(https?://[^\s]+)$', re.IGNORECASE)
    match = pattern.match(message.text.strip())
    
    if match:
        ticker = match.group(1).upper()
        link = match.group(2)
        company_urls.update({ticker: link})
        print(company_urls)
        await message.answer(f"Принято:\nТикер: #{ticker}\nСсылка: {link}")
    else:
        await message.answer(
            "Неверный формат.\nПример:\nКомпания: #SVCB - https://example.com"
        )

@dp.message(Command(commands=["remove"]))
async def cmd_remove(message: Message):
    if message.from_user.username not in ALLOWED_USERS:
        await message.answer("У вас нет прав.")
        return
    text = message.text.strip()
    match = re.match(r'/remove\s+#([A-Z0-9]+)', text, re.IGNORECASE)
    if match:
        ticker = match.group(1).upper()
        if ticker in company_urls:
            del company_urls[ticker]
            await message.answer(f"Компания #{ticker} удалена.")
        else:
            await message.answer(f"Компания #{ticker} не найдена.")
    else:
        await message.answer("Формат: /remove #TICKER")

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
