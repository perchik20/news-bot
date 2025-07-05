
### ------------------------------ 1️⃣ Парсер новостей ТАСС (economics) ------------------------------ ###

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

# from config import options

# import time
# import hashlib

# SEEN = set()
# CHECK_INTERVAL = 5  # Проверка каждую минуту

# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service, options=options)


# def fetch_news(driver):
#     print('1')
#     driver.get("https://tass.ru/ekonomika")
#     wait = WebDriverWait(driver, 40)
#     print('2')
#     articles = driver.find_elements(By.XPATH, '//*[@id="infinite_listing"]/a[1]/div[1]/div/div[1]/span/text()')
#     print('--->>>', articles)
#     news = []

#     for item in articles:
#         try:
#             title = item.text.strip()
#             link = item.get_attribute("href")
#             uid = hashlib.md5(link.encode()).hexdigest()
#             news.append({"uid": uid, "title": title, "link": link})
#         except Exception as e:
#             continue

#     return news

# def main():
#     print("🚀 Запущен парсер TASS (через Selenium)")

#     try:
#         while True:
#             news_items = fetch_news(driver)
#             for news in news_items:
#                 if news["uid"] not in SEEN:
#                     SEEN.add(news["uid"])
#                     print(f"🆕 {news['title']}\n{news['link']}\n")
#                     # send_to_bot(news['title'], news['link'])
#             time.sleep(CHECK_INTERVAL)
#     except KeyboardInterrupt:
#         print("🛑 Остановлено пользователем.")
#     finally:
#         driver.quit()

# if __name__ == "__main__":
#     main()

### ------------------------------ 2️⃣ Работа с API Мосбиржы (объем за сутки) ------------------------------ ###

# import requests
# import pandas as pd
# from datetime import datetime, timedelta

# def get_security_volumes(ticker: str, board='TQBR', limit=10):
#     """
#     Получить объемы торгов за последние дни по бумаге с MOEX.
    
#     :param ticker: тикер бумаги (например, 'SBER')
#     :param board: режим торгов (по умолчанию TQBR — основной рынок)
#     :param limit: сколько последних дней получить
#     :return: pandas DataFrame с датами и объемами
#     """
    
#     from_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    
#     url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/{board}/securities/{ticker}.json"
#     params = {
#         'iss.meta': 'off',
#         'from': from_date,  # можно указать дату начала, если нужно
#         'start': 0,
#         'limit': limit
#     }

#     response = requests.get(url, params=params)
#     response.raise_for_status()
#     data = response.json()

#     # Распаковываем таблицу 'history'
#     columns = data['history']['columns']
#     rows = data['history']['data']

#     df = pd.DataFrame(rows, columns=columns)
#     print(df)
#     df = df[['TRADEDATE', 'VOLUME', 'TRENDCLSPR']]
#     return df

# # Пример использования
# df = get_security_volumes('SBER', limit=5)
# print(df)

### ------------------------------ 3️⃣ Работа с API Мосбиржы (стакан)) ------------------------------ ###

import requests

def get_orderbook(ticker: str, depth: int = 10):
    base_url = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities"
    url = f"{base_url}/{ticker}/orderbook.json?depth={depth}"
    
    try:
        response = requests.get(url)
        
        # Выводим диагностическую информацию
        print(f"HTTP статус: {response.status_code}")
        print(f"URL запроса: {url}")
        print(f"Ответ (первые 300 символов): {response.text[:300]}")
        
        response.raise_for_status()
        data = response.json()

        bids = data['orderbook']['bids']
        offers = data['orderbook']['offers']

        return {
            'ticker': ticker,
            'bids': bids,
            'offers': offers
        }
    except Exception as e:
        return {"error": str(e)}


