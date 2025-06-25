
### ------------------------------ 1️⃣ Парсер файлов отчетности ------------------------------ ###

# import os
# import requests
# from io import BytesIO
# import zipfile
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# # --- Настройки ---
# page_url = 'https://e-disclosure.ru/portal/files.aspx?id=30052&type=4'  # ← замените на настоящий URL
# # xpath = '//*[@id="cont_wrap"]/div[2]/table/tbody/tr[2]/td[6]/a'
# save_folder = 'reports'

# # Создаём папку, если её нет
# os.makedirs(save_folder, exist_ok=True)

# for num in range (2, 6):
#     # --- Selenium: получить ссылку ---
#     options = webdriver.ChromeOptions()
#     # options.add_argument('--headless')
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     driver.get(page_url)

#     wait = WebDriverWait(driver, 10)
#     link_element = wait.until(EC.presence_of_element_located((By.XPATH, f'//*[@id="cont_wrap"]/div[2]/table/tbody/tr[{num}]/td[6]/a')))
#     file_url = link_element.get_attribute('href')

#     from urllib.parse import urljoin
#     file_url = urljoin(page_url, file_url)
#     driver.quit()

#     # --- Скачивание ZIP в память ---
#     response = requests.get(file_url)
#     zip_bytes = BytesIO(response.content)

#     # --- Извлечение PDF из архива ---
#     with zipfile.ZipFile(zip_bytes) as zip_file:
#         pdf_name = next(name for name in zip_file.namelist() if name.lower().endswith('.pdf'))
#         pdf_bytes = zip_file.read(pdf_name)  # читаем в память

#         # Путь сохранения
#         save_path = os.path.join(save_folder, os.path.basename(pdf_name))

#         # Сохраняем PDF
#         with open(save_path, 'wb') as f:
#             f.write(pdf_bytes)

#     print(f"✅ PDF-файл сохранён: {save_path}")


### ------------------------------ 2️⃣ Парсер новостей ТАСС (economics) ------------------------------ ###

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import options

import time
import hashlib

SEEN = set()
CHECK_INTERVAL = 5  # Проверка каждую минуту

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)


def fetch_news(driver):
    print('1')
    driver.get("https://tass.ru/ekonomika")
    wait = WebDriverWait(driver, 40)
    print('2')
    articles = driver.find_elements(By.XPATH, '//*[@id="infinite_listing"]/a[1]/div[1]/div/div[1]/span/text()')
    print('--->>>', articles)
    news = []

    for item in articles:
        try:
            title = item.text.strip()
            link = item.get_attribute("href")
            uid = hashlib.md5(link.encode()).hexdigest()
            news.append({"uid": uid, "title": title, "link": link})
        except Exception as e:
            continue

    return news

def main():
    print("🚀 Запущен парсер TASS (через Selenium)")

    try:
        while True:
            news_items = fetch_news(driver)
            for news in news_items:
                if news["uid"] not in SEEN:
                    SEEN.add(news["uid"])
                    print(f"🆕 {news['title']}\n{news['link']}\n")
                    # send_to_bot(news['title'], news['link'])
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Остановлено пользователем.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
