import time

from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

driver.get("http://localhost:3000")

def scrape_item(item_div):
    # include try-excepts to skip timeouts that may occur for some items

    desc_div = WebDriverWait(item_div, 3).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.MuiCardContent-root > div:first-of-type")
        )
    )
    detail_btn = WebDriverWait(item_div, 3).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.MuiCardContent-root > div:last-of-type")
        )
    )

    text, *bullets = desc_div.text.replace("•", "").replace("-", "").split("\n")

    detail_btn.click()

    detail_div = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.MuiModal-root"))
    )

    detail_rows = detail_div.find_elements(By.CSS_SELECTOR, "div.MuiBox-root > div.MuiGrid-root > div.MuiGrid-container > div.MuiGrid-item:last-of-type > div:first-child > div.MuiPaper-root > table > tbody > tr")

    details = []
    for detail_row in detail_rows:
        attr_name = detail_row.find_element(By.CSS_SELECTOR, "th").text
        attr_val = detail_row.find_element(By.CSS_SELECTOR, "td").text
        details.append((attr_name, attr_val))
    
    image_src = detail_div.find_element(By.CSS_SELECTOR, "img").get_attribute("src")

    ActionChains(driver).send_keys(Keys.ESCAPE).perform()

    return ("text", text.strip()), ("bullets", [b.strip() for b in bullets]), details

last_page_btn = driver.find_element(By.CSS_SELECTOR, "ul.MuiPagination-ul > li:nth-last-child(2) > button")
next_page_btn = driver.find_element(By.CSS_SELECTOR, "ul.MuiPagination-ul > li:last-child > button")

item_css = f"main > div > div:not(:last-child) > div.MuiPaper-root > div.MuiGrid-container > div.MuiGrid-item:nth-child(2)"
item_divs = driver.find_elements(By.CSS_SELECTOR, item_css)

total_pages = int(last_page_btn.text)
for i in tqdm(range(1, total_pages), desc="Scraping Shop"):
    for item_div in item_divs:
        text, bullets, details = scrape_item(item_div)
        # print(text[:10], [b[:10] for b in bullets], [d[:10] for d in details[:10]])

    next_page_btn.click()

driver.quit()