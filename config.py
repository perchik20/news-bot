from selenium import webdriver
from os import getenv
from aiogram import Bot, Dispatcher

import logging
from logging.handlers import RotatingFileHandler

FILENAME = "seen_urls.json"

# TITEL_XPATH = '//*[@id="cont_wrap"]/div[4]/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/a'
DESC_TITEL_XPATH = '//*[@id="cont_wrap"]/div[2]'

CHANNEL_ID = "587386190" #Поменял
DEBUG_ID = "587386190"
ALLOWED_USERS = {"prich_x", "FFMFak"}

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1920x1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

TOKEN = getenv("BOT_TOKEN") #Поменял
if not TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не установлена")
bot = Bot(token=TOKEN)
dp = Dispatcher()

console = logging.StreamHandler()
console.setLevel(logging.ERROR) 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler("parser.log", maxBytes=5_000_000, backupCount=2, encoding='utf-8'),
        console
    ]
)

log = logging.getLogger(__name__)
