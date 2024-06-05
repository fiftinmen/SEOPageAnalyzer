from bs4 import BeautifulSoup
from urllib.parse import urlparse


MAX_LENGTH = 255


def parse_page(page):
    soup = BeautifulSoup(page, 'html.parser')
    description = ''
    h1 = str(soup.h1.text)[:MAX_LENGTH] if soup.h1 else ''
    title = str(soup.title.text)[:MAX_LENGTH] if soup.title else ''
    for tag in soup.find_all("meta"):
        tag_name = tag.get('name', '').lower()
        if tag_name == 'description':
            description = tag.get('content', '')[:MAX_LENGTH]
            break
    return h1, title, description


def normalize_url(url):
    url_parts = urlparse(url)
    return f"{url_parts.scheme}://{url_parts.netloc}"
