from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from aiogram import types

import asyncio
import sys
import re

from config import ALLOWED_USERS, dp, bot, log, logging
from parser import fetch_news
from db_funcs import add_ticker, get_ticker, del_ticker
# Словарь для хранения фоновых задач по chat_id
# tasks: dict[int, asyncio.Task] = {}

running_tasks = []
stop_event = asyncio.Event()
is_running = False 
company_urls = {}
        
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    global running_tasks, stop_event, is_running

    chat_id = message.chat.id
    print(">> Запуск от", chat_id)

    if is_running:
        log.warning("Задачи уже запущены. Повторный запуск отменён.")
        await message.answer("✅ Цикл парсинга уже запущен.")
        return

    stop_event.clear()
    is_running = True

    running_tasks = [
        asyncio.create_task(fetch_news(chat_id, main_url, ticker, stop_event))
        for id, ticker, main_url in get_ticker()
    ]

    await message.answer("🚀 Запустил отправку новостей.")    
    

@dp.message(Command(commands=["stop"]))
async def cmd_stop(message: Message):
    global running_tasks, stop_event, is_running

    if not is_running:
        await message.answer("✅ Цикл уже остановлен.")
        return

    stop_event.set()

    for task in running_tasks:
        task.cancel()

    await asyncio.gather(*running_tasks, return_exceptions=True)
    running_tasks = []
    is_running = False 

    await message.answer("🛑 Остановил цикл отправки.")

@dp.message(Command(commands=["remove"]))
async def cmd_remove(message: Message):
    if message.from_user.username not in ALLOWED_USERS:
        await message.answer("У вас нет прав.")
        return
    text = message.text.strip()
    match = re.match(r'/remove\s+#([A-Z0-9]+)', text, re.IGNORECASE)
    if match:
        ticker = match.group(1).upper()
        company_urls = get_ticker()
        for i in company_urls:
            if ticker in i:
                del_ticker(ticker)
                await message.answer(f"Компания #{ticker} удалена.")
            else:
                await message.answer(f"Компания #{ticker} не найдена.")
    else:
        await message.answer("Формат: /remove #TICKER")

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
        try:
            add_ticker(ticker, link)
        except:
            await message.answer(f"Тикер: {ticker} уже существует")
        
        await message.answer(f"Принято:\nТикер: #{ticker}\nСсылка: {link}")
    else:
        await message.answer(
            "Неверный формат.\nПример:\nКомпания: #SVCB - https://example.com"
        )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())