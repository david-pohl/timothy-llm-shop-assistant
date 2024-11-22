from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By

# since the page is paginated, the dom is not rebuild allowing us to keep hold of the dom elements and save a lot of processing time

driver = webdriver.Chrome()

driver.get("http://localhost:3000")

def scrape_item(item):
    desc = item.find_element(By.CSS_SELECTOR, "div.MuiGrid-container > div.MuiGrid-item:nth-child(2) > div > div:first-of-type")
    # TODO details button
    
    text, *bullets = desc.text.replace("•", "").replace("-", "").split("\n")

    return text.strip(), [b.strip() for b in bullets]


items = driver.find_elements(By.CSS_SELECTOR, "main > div > div:not(:last-child)")

last_page_button = driver.find_element(By.CSS_SELECTOR, "ul.MuiPagination-ul > li:nth-last-child(2) > button")
next_page_button = driver.find_element(By.CSS_SELECTOR, "ul.MuiPagination-ul > li:last-child > button")

total_pages = int(last_page_button.text)
for i in tqdm(range(1, total_pages), desc="Scraping Shop"):
    for item in items:
        scrape_item(item)
    next_page_button.click()
    driver.implicitly_wait(1)

driver.quit()