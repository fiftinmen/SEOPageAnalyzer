from flask import (
    render_template,
    Flask,
    request,
    flash,
    get_flashed_messages,
    redirect,
)
import os
import validators
from bs4 import BeautifulSoup
from requests import get
from requests.exceptions import RequestException
from urllib.parse import urlparse
import page_analyzer.db as db

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

ADD_URL_MESSAGES = {
    "success": "Страница успешно добавлена",
    "warning": "Страница уже существует",
    "danger": "Некорректный URL"
}
CHECK_URL_MESSAGES = {
    "success": "Страница успешно проверена",
    "danger": "Произошла ошибка при проверке"
}
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


@app.route('/')
def index():
    return render_template(
        'index.html',
        messages=get_flashed_messages(with_categories=True))


@app.post('/urls')
def add_url():
    url = request.form.to_dict().get('url')
    url = normalize_url(url)
    if not validators.url(url):
        flash(ADD_URL_MESSAGES['danger'], "danger")
    else:
        data = db.get_url_data_by_field('name', url)
        if url in data:
            flash(ADD_URL_MESSAGES['success'], 'success')
            db.insert_url(url)
        else:
            flash(ADD_URL_MESSAGES['warning'], 'warning')
        url_id = db.get_url_data_by_field('name', url)[0]
        return redirect(f'urls/{url_id}', 302)
    return render_template(
        'index.html',
        messages=get_flashed_messages(with_categories=True)
    ), 422


@app.get('/urls')
def show_urls_list():
    return render_template(
        'urls.html',
        messages=get_flashed_messages(with_categories=True),
        urls=db.get_urls_list()
    )


@app.get('/urls/<url_id>')
def show_url_data(url_id):
    url_data = db.get_url_data_by_field('id', url_id)
    return render_template(
        'url.html',
        messages=get_flashed_messages(with_categories=True),
        id=url_id,
        name=url_data[1],
        created_at=url_data[2].date(),
        checks=db.get_checks_data(url_id)
    )


@app.post('/urls/<url_id>/checks')
def check_url(url_id):
    data = db.get_url_data_by_field('id', url_id)
    try:
        url = data[1]
        response = get(url)
        response.raise_for_status()
        h1, title, description = parse_page(response.text)
        db.insert_check(url_id, response.status_code, h1, title, description)
        flash(CHECK_URL_MESSAGES['success'], 'success')
    except RequestException:
        flash(CHECK_URL_MESSAGES['danger'], 'danger')
    return redirect(f'/urls/{url_id}', 302)
