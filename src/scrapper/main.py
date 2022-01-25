import json
import time


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import *


from requests_html import HTMLSession

from model import SiteData, Domain
from common import site_config, get_driver, dump_model


total_index: int = 0


def main():
    global total_index

    site = site_config(
        "/home/ioachimlihor/Licenta/Project/licenta/src/scrapper/config.json"
    )
    driver = get_driver()

    site_data = SiteData(site="Times New Roman")

    for route in site.routes:
        print(route)
        domain = Domain(name=route)

        driver.get(site.url + route)
        time.sleep(10)

        links = []
        index = 0
        site_data.domains.append(domain)
        print("Am facut append")
        while True:

            total_index += index
            if total_index / 6 % 10 == 0 and total_index > 0:
                session = HTMLSession()
                for link in links:
                    data = session.get(link)

                    title = data.html.find("h1")[0].text.encode("utf-8").decode()
                    content = ""
                    for paragraph in data.html.find(
                        'div[class^="content-container"] > p'
                    ):
                        if "class" not in paragraph.attrs:
                            content += paragraph.text.encode("utf-8").decode()

                    domain.articles.append({"title": title, "content": content})

                site_data.domains[-1].articles.extend(domain.articles)
                dump_model(
                    site_data,
                    "/home/ioachimlihor/Licenta/Project/licenta/data/raw/scrapped_data/timesnewroman/data.json",
                )
                domain = Domain(name=route)
                links = []

            articles = WebDriverWait(driver, 3).until(
                expected_conditions.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'article[class^="article-box"]')
                )
            )
            if index == len(articles):
                break

            for idx in range(index, len(articles)):
                elems = articles[idx].find_elements_by_css_selector("span + a")
                new_links = [el.get_attribute("href") for el in elems]

                if new_links != []:
                    for link in new_links:
                        if link not in links:
                            links.append(link)
                            index += 1
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                load_more_btn = WebDriverWait(driver, 3).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[class$="load-more"] > img')
                    )
                )
                load_more_btn.click()
                time.sleep(3)
            except Exception as exc:
                print(exc)
                driver.close()
                break

            print(f"From router: {route} we got: {len(links)}")

        session = HTMLSession()
        for link in links:
            data = session.get(link)

            title = data.html.find("h1")[0].text.encode("utf-8").decode()
            content = ""
            for paragraph in data.html.find('div[class^="content-container"] > p'):
                if "class" not in paragraph.attrs:
                    content += paragraph.text.encode("utf-8").decode()

            domain.articles.append({"title": title, "content": content})

        site_data.domains[-1].articles.extend(domain.articles)

    dump_model(
        site_data,
        "/home/ioachimlihor/Licenta/Project/licenta/data/raw/scrapped_data/timesnewroman/data.json",
    )

    driver.close()


if __name__ == "__main__":
    main()