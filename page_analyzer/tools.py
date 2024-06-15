from collections import namedtuple
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from http import HTTPStatus

UrlLastCheck = namedtuple('UrlLastCheck',
                          ['id', 'name', 'status_code', 'created_at'])
MAX_LENGTH = 255

REDIRECTION_MESSAGE = "Перенаправляем на главную страницу."
ERROR_MESSAGES = {
    HTTPStatus.BAD_REQUEST: "Ваш запрос содержит ошибку.",
    HTTPStatus.NOT_FOUND: "Страница не найдена.",
    HTTPStatus.INTERNAL_SERVER_ERROR: "Внутренняя ошибка сервера.",
    HTTPStatus.METHOD_NOT_ALLOWED: "Ваш запрос содержит ошибку.",
    'UNEXPECTED': 'Произошла непредвиденная ошибка',
    'WRONG_URL_ID': 'URL с таким id не существует.',
}


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


def parse_error(error):
    status_code = getattr(error, "code", HTTPStatus.INTERNAL_SERVER_ERROR)
    status_code = getattr(status_code, "value", status_code)
    description = getattr(error, "description", None)
    messages = [ERROR_MESSAGES.get(status_code,
                                   ERROR_MESSAGES['UNEXPECTED'])]
    if description in ERROR_MESSAGES:
        messages.append(ERROR_MESSAGES[description])
    messages.append(REDIRECTION_MESSAGE)
    messages = ' '.join(messages)
    return status_code, messages


def get_created_at(record):
    return record.created_at or datetime.datetime.min


def get_checks_by_url(checks, url):
    return [rec for rec in checks
            if rec.url_id == url.id]


def get_last_checks_for_urls(urls, checks):
    if not urls:
        return
    if not checks:
        return urls

    urls_last_checks = []
    for url in urls:
        last_check = None
        if checks_by_url := get_checks_by_url(checks, url):
            last_check = max(checks_by_url, key=get_created_at)
        url_last_check = UrlLastCheck(
            id=url.id,
            name=url.name,
            created_at=getattr(last_check, 'created_at', None),
            status_code=getattr(last_check, 'status_code', ''),
        )
        urls_last_checks.append(url_last_check)
    return urls_last_checks
