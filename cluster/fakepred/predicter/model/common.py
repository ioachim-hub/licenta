import re
import dataclasses


import bs4
import requests_html


ak24_signature = re.compile(r"Mai mult despre: .+ Aktual24")
tnr_signature = re.compile(r"Noi tocmai ne-am desfăcut câte o bere TNR. .+ comentariu.")
biziday_signature = re.compile(r"Echipa Biziday .+ Susține echipa Biziday")
infoalert_signature = re.compile(r"Te așteptăm .+ mai jos:")
activenews_signature = re.compile(r"Pentru că suntem cenzurați pe Facebook .+")

spaces = re.compile(r"\s+")


@dataclasses.dataclass
class NewsInfo:
    title: str
    content: str
    link: str


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    text = text.replace("\xa0", " ")
    text = text.replace("•", " ")
    text = text.replace("\u2022", " ")
    text = text.replace("\u25e6", " ")
    text = text.replace(" +", " ")
    text = text.strip()
    text = spaces.sub(" ", text)
    text = ak24_signature.sub("", text)
    text = tnr_signature.sub("", text)
    text = biziday_signature.sub("", text)
    text = infoalert_signature.sub("", text)
    text = activenews_signature.sub("", text)
    return text


def extract_from_news(url: str) -> NewsInfo:
    empty_return = NewsInfo("", "", "")
    if url.split(".")[-1] in ["pdf", "doc", "docx", "xls", "xlsx", "txt"]:
        return empty_return

    if url.split(".")[-1] in ["jpg", "jpeg", "png"]:
        return empty_return

    if ".pdf" in url:
        return empty_return

    session = requests_html.HTMLSession()
    data = session.get(url, timeout=10)

    if "PDF" in data.text:
        return empty_return

    soup = bs4.BeautifulSoup(data.text)
    # title: str = " ".join([p.text for p in soup.find_all("title")])
    title = " ".join([p.text for p in soup.find_all("h1")])
    title = clean_text(title)

    content: str = " ".join([p.text for p in soup.find_all("p")])
    content = clean_text(content)

    content = " ".join(
        [word for word in content.split(" ")[: min(len(content.split(" ")), 1000)]]
    )

    num_words = len(content.split(" "))
    if num_words > 512:
        content = " ".join(content.split(" ")[:512])

    max_num_chars = 10000
    if len(content) > max_num_chars:
        content = content[:max_num_chars]

    return NewsInfo(title=title, content=content, link=url)
