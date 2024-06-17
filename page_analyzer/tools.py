from bs4 import BeautifulSoup
from urllib.parse import urlparse
from http import HTTPStatus

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
