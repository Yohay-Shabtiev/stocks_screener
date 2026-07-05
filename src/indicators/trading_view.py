from lists import nasdaq_tickers
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def open_urls(tickers):
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)

    # Open the first URL
    first = tickers[0]
    if first in nasdaq_tickers:
        driver.get(f"https://il.tradingview.com/chart/?symbol=NASDAQ%3A{first.upper()}")
    else:
        driver.get(f"https://il.tradingview.com/chart/?symbol=NYSE%3A{first.upper()}")

    answer = input("Do you want to start opening more tabs? (y/n): ").lower()
    if answer != 'y':
        return

    for i, ticker in enumerate(tickers):
        driver.switch_to.new_window('tab')  # this works better than window.open()
        
        if ticker in nasdaq_tickers:
            driver.get(f"https://il.tradingview.com/chart/?symbol=NASDAQ%3A{ticker.upper()}")
        else:
            driver.get(f"https://il.tradingview.com/chart/?symbol=NYSE%3A{ticker.upper()}")

        time.sleep(1.5)

        if i % 10 == 0:
            answer = input("Open 10 more tabs? (y/n): ").lower()
            if answer != 'y':
                break
