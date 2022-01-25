import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

from model import SiteConfig, SiteData


def site_config(path: str) -> SiteConfig:
    in_file = open(path, "r")
    site = SiteConfig.parse_obj(json.load(in_file))
    return site


def driver_config() -> Options:
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

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
