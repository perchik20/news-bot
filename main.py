import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from collections import deque

import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

options = webdriver.ChromeOptions()
# if headless:
#     options.add_argument("--headless=new")
options.add_argument(f"--window-size=1920x1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# любые другие опции: прокси, user-agent и т.п.

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(10)
    
seen_urls = deque(maxlen=10)

TITEL_XPATH = '//*[@id="cont_wrap"]/div[4]/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/a'
DECS_TITEL_XPATH = '//*[@id="cont_wrap"]/div[2]'

try:
    driver.get("https://e-disclosure.ru/portal/company.aspx?id=30052")
    wait = WebDriverWait(driver, 10)
    
    try:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, TITEL_XPATH)))
    except Exception as ex:
        log.error("Не удалось получить доступ к странице событий", exc_info=ex)
        
    title = elem.text
    
    try:
        url = elem.get_attribute("href")
    except Exception as ex:
        log.error("Не удалось получить ссылку на событие", exc_info=ex)

    if url not in seen_urls:
        seen_urls.append(url)
        driver.get(url)
        
        try:
            elem2 = wait.until(EC.presence_of_element_located((By.XPATH, DECS_TITEL_XPATH)))
        except Exception as ex:
            log.error("Не удалось получить доступ к странице описания события", exc_info=ex)
            
        full_text = elem2.text
        
        try:
            match = re.search(
                r"(2\. Содержание сообщения.*?)(?=\n3\. Подпись.)",
                full_text, re.DOTALL
            )
            section = match.group(1).strip()
        except Exception as ex:
            log.error("Не удалось вытащить текст из описания события", exc_info=ex)

        full_text = f"*{title}*\n\n{section}"
        print(full_text)
        
except Exception as ex:
    log.error("Ошибка внутри блока try:", exc_info=ex)
    
finally:
    driver.quit()

