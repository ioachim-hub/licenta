import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

from licenta_code.scrapper.model import SiteConfig, SiteData


def site_config(path: str) -> SiteConfig:
    in_file = open(path, "r")
    site: SiteConfig = SiteConfig.parse_obj(json.load(in_file))
    return site


def driver_config() -> Options:
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    chrome_prefs: dict[str, dict[str, int]] = {}
    options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return options


def get_driver() -> webdriver.Chrome:
    options = driver_config()
    driver = webdriver.Chrome(
        executable_path=ChromeDriverManager().install(), options=options
    )
    return driver


def dump_model(model: SiteData, path: str):
    with open(path, "wb") as out:
        out.write(json.dumps(model.dict(), indent=4, ensure_ascii=False).encode("utf8"))


def convert_date(date: str) -> str:
    """
    16 septembrie, 2009
    ->
    16 09 2009
    """
    datelist = date.split(" ")

    enrichment = {
        "ianuarie,": "1",
        "februarie,": "2",
        "martie,": "3",
        "aprilie,": "4",
        "mai,": "5",
        "iunie,": "6",
        "iulie,": "7",
        "august,": "8",
        "septembrie,": "9",
        "octombrie,": "10",
        "noiembrie,": "11",
        "decembrie,": "12",
    }

    return f"{datelist[0]} {enrichment[datelist[1].lower()]} {datelist[2]}"
