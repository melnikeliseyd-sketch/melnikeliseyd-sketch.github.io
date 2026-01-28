
from requests import options
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

opts = Options()
service = Service(ChromeDriverManager().install())
drv = webdriver.Chrome(service=service, options=opts)

drv.get("https://quotes.toscrape.com")
WebDriverWait(drv, timeout=10).until(EC.presence_of_element_located((By.CLASS_NAME, "quote")))
quotes = drv.find_elements(By.CLASS_NAME, 'quote')
result = ''
for quote in quotes:
    quote_text = quote.find_element(By.CLASS_NAME, 'text').text
    author = quote.find_element(By.CLASS_NAME, 'author').text
    result += quote_text + '\n'
    result += author + '\n'

print(result)