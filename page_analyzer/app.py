from flask import (
    render_template,
    Flask,
    request,
    flash,
    redirect,
    url_for,
    abort
)
from http import HTTPStatus
import sys
import traceback
import os
import validators
import requests
from requests.exceptions import RequestException
import page_analyzer.db as db
from dotenv import load_dotenv
from page_analyzer.tools import parse_page, normalize_url


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for Flask application")

ADD_URL_MESSAGES = {
    "success": "Страница успешно добавлена",
    "warning": "Страница уже существует",
    "danger": "Некорректный URL"
}
CHECK_URL_MESSAGES = {
    "success": "Страница успешно проверена",
    "danger": "Произошла ошибка при проверке"
}
REDIRECT_DELAY_SECONDS = 5
REDIRECTION_MESSAGE = "Перенаправляем на главную страницу."
ERROR_MESSAGES = {
    HTTPStatus.BAD_REQUEST: "Ваш запрос содержит ошибку.",
    HTTPStatus.NOT_FOUND: "Страница не найдена.",
    HTTPStatus.INTERNAL_SERVER_ERROR: "Кажется, что-то пошло не так."
}


@app.route('/')
def index():
    return render_template(
        'index.html',
    )


@app.post('/urls')
def add_url():
    conn = db.get_connection(DATABASE_URL)
    url = request.form.to_dict().get('url')
    url = normalize_url(url)
    if not validators.url(url):
        flash(ADD_URL_MESSAGES['danger'], "danger")
        db.close_connection(conn)
        return render_template(
            'index.html',
        ), 422
    if db.get_url_by_name(conn, url) is None:
        flash(ADD_URL_MESSAGES['success'], 'success')
        db.insert_url(conn, url)
        db.commit(conn)
    else:
        flash(ADD_URL_MESSAGES['warning'], 'warning')
    url_id = db.get_url_by_name(conn, url).id
    db.close_connection(conn)
    return redirect(url_for('show_url', url_id=url_id), HTTPStatus.FOUND)


@app.get('/urls')
def show_urls():
    conn = db.get_connection(DATABASE_URL)
    urls = db.get_urls(conn)
    db.close_connection(conn)
    return render_template(
        'urls.html',
        urls=urls,
    )


@app.get('/urls/<url_id>')
def show_url(url_id):
    conn = db.get_connection(DATABASE_URL)
    url = db.get_url_by_id(conn, url_id)
    if url is None:
        error_message = {'message': 'URL с такими параметрами не существует.'}
        abort(HTTPStatus.BAD_REQUEST, error_message)

    checks = db.get_url_checks(conn, url_id)
    db.close_connection(conn)
    return render_template(
        'url.html',
        url=url,
        checks=checks,
    )


@app.post('/urls/<url_id>/checks')
def check_url(url_id):
    conn = db.get_connection(DATABASE_URL)
    url = db.get_url_by_id(conn, url_id)
    try:
        url_name = url.name
        response = requests.get(url_name)
        response.raise_for_status()
        h1, title, description = parse_page(response.text)
        db.insert_url_check(
            conn,
            {
                'url_id': url_id,
                'status_code': response.status_code,
                'h1': h1,
                'title': title,
                'description': description
            }
        )
        db.commit(conn)
        flash(CHECK_URL_MESSAGES['success'], 'success')
    except RequestException:
        flash(CHECK_URL_MESSAGES['danger'], 'danger')
    db.close_connection(conn)
    return redirect(url_for('show_url', url_id=url_id), HTTPStatus.FOUND)


@app.errorhandler(Exception)
def internal_error(error):
    print(''.join(traceback.format_exception(*sys.exc_info())))
    status_code = getattr(error, "code", HTTPStatus.INTERNAL_SERVER_ERROR)
    print(status_code)
    messages = ' '.join([
        ERROR_MESSAGES[status_code],
        REDIRECTION_MESSAGE
    ])
    return render_template(
        'error.html',
        status_code=status_code,
        messages=messages
    ), HTTPStatus.INTERNAL_SERVER_ERROR, {
        "Refresh": f"{REDIRECT_DELAY_SECONDS}; url={url_for('index')}"
    }
