import sys
import os

import time
import re
import json
from datetime import datetime

from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def scrape(is_backend_running):
    scraping_url = os.getenv("SCRAPING_URL")
    selenium_chrome_url = os.getenv("SELENIUM_CHROME_URL")


    print(scraping_url)
    print(selenium_chrome_url)

    driver = webdriver.Remote(
        command_executor="http://selenium:4444/wd/hub",
        options=webdriver.ChromeOptions()
    )

    
    print("driver created")

    driver.get(scraping_url)
    print(driver.title)

    print("website received")

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

    filename_date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

    if not is_backend_running:
        with open(f"data/scraped_{filename_date}.json", "w") as f:
            json.dump(scraped_items, f, indent=4)


    def new_parent_entry(item):
        return {
            "name": item["name"],
            "size": item["size"],
            "price": item["price ($)"],
            "categories": item["categories"],
            "description": item["text"],
            "features": item["bullets"],
            "colors": set(),
            "variants": set(),
        }

    parent2info = {}

    for item in scraped_items:
        parent_id = item["parent"]
        if parent_id == "NA":
            parent2info[item["sku"]] = new_parent_entry(item)

    for item in scraped_items:
        parent_id = item["parent"]
        if parent_id != "NA":
            size, color = item["name"].split("-")[-2:]
            if parent_id not in parent2info:
                parent2info[parent_id] = new_parent_entry(item)
            else:
                if size not in parent2info[parent_id]["size"]:
                    parent2info[parent_id]["size"].append(size)

            parent2info[parent_id]["colors"].add(color)
            parent2info[parent_id]["variants"].add((item["id"], size, color, item["stock"]))

    for parent_id, info in parent2info.items():
        parent2info[parent_id]["colors"] = sorted(list(parent2info[parent_id]["colors"]))
        parent2info[parent_id]["variants"] = sorted(list(parent2info[parent_id]["variants"]))

    if not is_backend_running:
        with open(f"data/products_{filename_date}.json", "w") as f:
            json.dump(parent2info, f, indent=4)

    driver.quit()

    return parent2info, filename_date
