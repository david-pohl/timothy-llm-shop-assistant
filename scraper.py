import time
import re
import json
from datetime import datetime

from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

driver.get("http://localhost:4000")

unused_attrs = set()

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

    text, *bullets = desc_div.text.split("\n")
    text = text.strip()
    bullets = "; ".join([re.sub(r"[\n]*•\s", "", b).strip(".") for b in bullets])

    detail_btn.click()

    detail_div = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.MuiModal-root"))
    )

    detail_rows = detail_div.find_elements(By.CSS_SELECTOR, "div.MuiBox-root > div.MuiGrid-root > div.MuiGrid-container > div.MuiGrid-item:last-of-type > div:first-child > div.MuiPaper-root > table > tbody > tr")

    scraped = {}
    for detail_row in detail_rows:
        attr_name = detail_row.find_element(By.CSS_SELECTOR, "th").text.lower().strip()
        attr_text = detail_row.find_element(By.CSS_SELECTOR, "td").text

        if attr_name == "":
            attr_name = detail_row.find_element(By.CSS_SELECTOR, "th").get_attribute("textContent").lower().strip()
        if attr_text == "":
            attr_text = detail_row.find_element(By.CSS_SELECTOR, "td").get_attribute("textContent")

        if attr_name in ["name", "sku", "parent"]:
            attr_val = attr_text.strip()
        elif attr_name in ["id", "price ($)", "stock"]:
            try:
                attr_val = int(attr_text)
            except:
                attr_val = None
        elif attr_name == "size":
            attr_val = re.split(r"[,\n;]+", attr_text)
        elif attr_name == "categories":
            lines = re.split(r"\n+", attr_text)
            attr_val = [l.split(">") for l in lines]
        else:
            # Omitting unused attributes
            unused_attrs.add(attr_name)
            continue

        scraped[attr_name] = attr_val
    
    image_src = detail_div.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
    scraped["img"] = image_src

    ActionChains(driver).send_keys(Keys.ESCAPE).perform()

    scraped["text"] = text
    scraped["bullets"] = bullets

    return scraped

last_page_btn = driver.find_element(By.CSS_SELECTOR, "ul.MuiPagination-ul > li:nth-last-child(2) > button")
next_page_btn = driver.find_element(By.CSS_SELECTOR, "ul.MuiPagination-ul > li:last-child > button")

item_css = f"main > div > div:not(:last-child) > div.MuiPaper-root > div.MuiGrid-container > div.MuiGrid-item:nth-child(2)"
item_divs = driver.find_elements(By.CSS_SELECTOR, item_css)

scraped_items = []

total_pages = int(last_page_btn.text)
for i in tqdm(range(1, total_pages), desc="Scraping Shop"):
    for item_div in item_divs:
        scraped = scrape_item(item_div)
        scraped_items.append(scraped)

    next_page_btn.click()

print(unused_attrs)
with open(f"backend/data/scraped_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.json", "w") as f:
    json.dump(scraped_items, f, indent=4)

driver.quit()