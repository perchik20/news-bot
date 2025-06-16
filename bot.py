from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from aiogram import types

import asyncio
import sys
import re

from config import ALLOWED_USERS, dp, bot, log, logging
from parser import fetch_news
from db_funcs import add_ticker, get_ticker
from db_funcs import add_company_custom, get_company_custom, del_company_custom, add_new_user, add_all_in_company_custom
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

running_tasks = [] # Задачи на выполнении
stop_event = asyncio.Event() # функция контроля задач 
is_running = False # Маркер работы парсера
COMPANIES_PER_PAGE = 6 # Ограничение по кол-во компаний в меню

 ### ---------------------------------------- Перезапускает парсер после добавления новой компании ---------------------------------------- ###

async def restart_news_tasks(chat_id: int):
    global running_tasks, stop_event, is_running

    # Остановка текущих задач
    if is_running:
        stop_event.set()
        await asyncio.gather(*running_tasks, return_exceptions=True)
        log.info("Старые задачи остановлены.")

    # Подготовка к запуску новых задач
    stop_event = asyncio.Event()
    is_running = True

    # Получение списка ссылок и запуск задач
    tickers = get_ticker()
    running_tasks = [
        asyncio.create_task(fetch_news(chat_id, main_url, ticker, stop_event))
        for _, ticker, main_url in tickers
    ]
    log.info("Новые задачи запущены.")

 ### ---------------------------------------- Создает меню компаний ---------------------------------------- ###
 
async def show_companies(callback, chat_id, custom, page=0):
    if custom:
        companies = get_company_custom(chat_id)
        text = 'Личный список компаний'
    else:
        companies = get_ticker()
        text = 'Список доступных компаний'

    start = page * COMPANIES_PER_PAGE
    end = start + COMPANIES_PER_PAGE
    current_companies = companies[start:end]

    keyboard = []
    if custom:
        for _, _, ticker in current_companies:
            keyboard.append([InlineKeyboardButton(text = f"❌ {ticker}", callback_data=f"del:{ticker}:{page}")])
        type = 'custom'
        
    else:
        companies = []
        received_companies = get_company_custom(callback.from_user.id)
        for _, _, ticker in received_companies:
            companies.append(ticker)
                
        for _, ticker, _ in current_companies:
                if ticker in companies:
                    keyboard.append([InlineKeyboardButton(text = f"✅ {ticker}", callback_data="already")])
                else:
                    keyboard.append([InlineKeyboardButton(text = f"➕ {ticker}", callback_data=f"add:{ticker}:{page}")])
            
        type = 'list'
        keyboard.append([InlineKeyboardButton(text = "Добавить все компании", callback_data="add_all")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text = "⬅️ Назад", callback_data=f"page:{page-1}:{type}"))
    if end < len(companies):
        nav_buttons.append(InlineKeyboardButton(text = "➡️ Далее", callback_data=f"page:{page+1}:{type}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text = "❎ Закрыть", callback_data="close")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # await bot.send_message(callback.message.chat.idat_id, f"📋 {text}:", reply_markup=markup)
    await bot.edit_message_text(text=f"📋 {text}:", 
                                chat_id=callback.message.chat.id, 
                                message_id=callback.message.message_id, 
                                reply_markup=markup,
                                parse_mode="Markdown")   

 ### ---------------------------------------- Вывод при использование команды /start  ---------------------------------------- ###

@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):

    add_new_user(message.chat.username, message.chat.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        
        [InlineKeyboardButton(text="🚀 Запустить", callback_data="start_news")],
        [InlineKeyboardButton(text="🛑 Остановить", callback_data="stop_news")],
        [InlineKeyboardButton(text="👁️ Мой cписок компаний", callback_data="custom_list_companies")],
        [InlineKeyboardButton(text="📋 Список компаний", callback_data="list_companies")]
        
    ])
    
    await message.answer(
        "Добро пожаловать!\n\n"
        "*Важно: Перед тем как добавит/удалить компанию, необходимо остановить парсинг*\n\n"
        "➕Для того чтобы добавить компанию надо написать текст четко по шаблону:\n"
        "Компания: #тикер - ссылка\n"
        "После этого он напишет, что добавил компанию, в ином случае укажет на ошибку\n\n"
        "*Выберите действие из пункта меню или добавьте компанию:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

### ---------------------------------------- Откликается на использование кнопки '➕ название компании' в списке компаний ---------------------------------------- ###

@dp.callback_query(F.data == "add_all")
async def delete_company(callback: CallbackQuery):
    chat_id = callback.from_user.id
    
    add_all_in_company_custom(chat_id)
    
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    chat_id = callback.from_user.id
    await show_companies(callback, chat_id, False, 0)

### ---------------------------------------- Откликается на использование кнопки '➕ название компании' в списке компаний ---------------------------------------- ###

@dp.callback_query(F.data.startswith("add:"))
async def delete_company(callback: CallbackQuery):
    _, ticker, page = callback.data.split(":")
    chat_id = callback.from_user.id
    
    add_company_custom(chat_id, ticker)
    
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    chat_id = callback.from_user.id
    await show_companies(callback, chat_id, False, int(page))

 ### ---------------------------------------- Откликается на использование кнопки '❌ название компании' в кастомном списке компаний ---------------------------------------- ###

@dp.callback_query(F.data.startswith("del:"))
async def delete_company(callback: CallbackQuery):
    _, ticker, page = callback.data.split(":")
    chat_id = callback.from_user.id
    
    del_company_custom(chat_id, ticker)
    
    # await callback.answer(f"Удалено: {ticker}", show_alert=True)
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    chat_id = callback.from_user.id
    await show_companies(callback, chat_id, True, int(page))

 ### ---------------------------------------- Откликается на использование кнопки 'Далее/Назад' в списке компаний ---------------------------------------- ### 

@dp.callback_query(F.data.startswith("page:"))
async def change_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    type = callback.data.split(":")[2]
    
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    custom = False
    if type == 'custom':
        custom = True
        
    chat_id = callback.from_user.id
    await show_companies(callback, chat_id, custom, page)

 ### ---------------------------------------- Откликается на использование кнопки 'Закрыть меню' в списке компаний ---------------------------------------- ### 

@dp.callback_query(F.data == "close")
async def close_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        
        [InlineKeyboardButton(text="🚀 Запустить", callback_data="start_news")],
        [InlineKeyboardButton(text="🛑 Остановить", callback_data="stop_news")],
        [InlineKeyboardButton(text="👁️ Мой список компаний", callback_data="custom_list_companies")],
        [InlineKeyboardButton(text="📋 Список компаний", callback_data="list_companies")]
        
    ])
    await bot.edit_message_text(text="*Главное меню:*", 
                                chat_id=callback.message.chat.id, 
                                message_id=callback.message.message_id, 
                                reply_markup=keyboard,
                                parse_mode="Markdown")   
    
 ### ---------------------------------------- Откликается на использование кнопки 'Запустить' в главном меню ---------------------------------------- ### 

@dp.callback_query(F.data == "start_news")
async def handle_start_news(callback: CallbackQuery):
    global running_tasks, stop_event, is_running
    chat_id = callback.message.chat.id

    print(">> Запуск от", chat_id)

    if is_running:
        log.warning("Задачи уже запущены. Повторный запуск отменён.")
        await callback.answer("Уже запущено!", show_alert=True)
        return

    stop_event.clear()
    is_running = True
    running_tasks = [
        asyncio.create_task(fetch_news(chat_id, main_url, ticker, stop_event))
        for _, ticker, main_url in get_ticker()
    ]
    await callback.message.answer("🚀 Запустил отправку новостей.")
    await callback.answer()

 ### ---------------------------------------- Откликается на использование кнопки 'Остановить' в главном меню ---------------------------------------- ### 

@dp.callback_query(F.data == "stop_news")
async def handle_stop_news(callback: CallbackQuery):
    global running_tasks, stop_event, is_running

    if not is_running:
        await callback.answer("✅ Цикл уже остановлен.")
        return

    stop_event.set()

    for task in running_tasks:
        task.cancel()
    await asyncio.gather(*running_tasks, return_exceptions=True)
    
    running_tasks = []
    is_running = False 

    await callback.message.answer("🛑 Остановил цикл отправки.")
    await callback.answer()

 ### ---------------------------------------- Откликается на использование кнопки 'Список компаний' в главном меню ---------------------------------------- ### 

@dp.callback_query(F.data == "list_companies")
async def handle_list_companies(callback: CallbackQuery):
    
    chat_id = callback.from_user.id
    await show_companies(callback, chat_id, False, page=0)
    
### ---------------------------------------- Откликается на использование кнопки 'Мой список компаний' в главном меню ---------------------------------------- ### 

@dp.callback_query(F.data == "custom_list_companies")
async def handle_custom_list_companies(callback: CallbackQuery):

    chat_id = callback.from_user.id
    await show_companies(callback, chat_id, True, page=0)
    
 ### ---------------------------------------- Обрабатывает добавление компании (откликается на любой рукописный текст)  ---------------------------------------- ### 

@dp.message(F.text)
async def handle_company_message(message: types.Message):
    user = message.from_user

    # Проверка, разрешён ли пользователь
    if user.username not in ALLOWED_USERS:
        await message.answer("У вас нет прав для отправки данных.")
        return
    pattern = re.compile( r'^компания:\s+#([A-Z0-9]+)\s*-\s*(https?://[^\s]+)$', re.IGNORECASE)
    match = pattern.match(message.text.strip())
    chat_id = message.chat.id
    
    if match:
        ticker = match.group(1).upper()
        link = match.group(2)
        try:
            add_ticker(ticker, link)
            
        except:
            await message.answer(f"Тикер: {ticker} уже существует")
        
        await message.answer(f"Принято:\nТикер: #{ticker}\nСсылка: {link}")
        print(">> Запуск от", chat_id)
        await restart_news_tasks(chat_id)
        await message.answer("🔄 Парсер новостей перезапущен.")
    else:
        await message.answer(
            "Неверный формат.\nПример:\nКомпания: #SVCB - https://example.com"
        )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())