import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


from licenta_code.scrapper.model import Entry
from licenta_code.scrapper.common import get_driver

total_index: int = 0


driver = get_driver()


def search_logic(
    url: str, existing_entries: list[Entry], driver: webdriver.Chrome
) -> list[Entry]:
    entries: list[Entry] = []
    print(f"searching from: {url})")

    exist_link = [link.link for link in existing_entries]

    articles = WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#main > ul")
        )
    )
    try:
        driver.switch_to.frame(
            driver.find_element_by_css_selector("#_ao-cmp-ui > iframe")
        )
        driver.find_element_by_css_selector(
            "body > div:nth-child(1) > div > div > div > div.modal-footer > div > button.btn.btn-success"
        ).click()
        driver.switch_to.default_content()
    except Exception:
        pass

    current_index: int = 0
    while current_index <= 100:
        time.sleep(3)
        button = WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#more")
            )
        )

        if button is not None:
            button[0].click()

        links = []

        elems_links = articles[0].find_elements_by_css_selector("a")

        for index in range(current_index, len(elems_links)):
            link = elems_links[index].get_attribute("href")
            if link not in exist_link and link not in links:
                links.append(link)
                current_index += 1
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        for link in links:
            entries.append(Entry(site=url, link=link))

    return entries
