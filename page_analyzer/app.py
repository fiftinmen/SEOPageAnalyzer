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
from page_analyzer.tools import parse_page, normalize_url, parse_error


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')

if app.config['DATABASE_URL'] is None:
    raise ValueError("No DATABASE_URL set for Flask application")

INCORRECT_URL_MESSAGE = "Некорректный URL", "danger"
URL_CHECK_SUCCESS = "Страница успешно проверена", "success"
URL_CHECK_FAIL = "Произошла ошибка при проверке", "danger"
REDIRECT_DELAY_SECONDS = 5


@app.route('/')
def index():
    return render_template(
        'index.html',
    )


@app.post('/urls')
def add_url():
    with db.get_connection(app.config['DATABASE_URL']) as conn:
        url = request.form.to_dict().get('url')
        url = normalize_url(url)
        if not validators.url(url):
            flash(*INCORRECT_URL_MESSAGE)
            return render_template(
                'index.html',
            ), 422
        flash(*db.insert_url(conn, url))
        db.commit(conn)
        url_id = db.get_url(conn, name=url).id
        return redirect(url_for('show_url', url_id=url_id), HTTPStatus.FOUND)


@app.get('/urls')
def show_urls():
    with db.get_connection(app.config['DATABASE_URL']) as conn:
        urls = db.get_urls(conn)
        return render_template(
            'urls.html',
            urls=urls,
        )


@app.get('/urls/<url_id>')
def show_url(url_id):
    with db.get_connection(app.config['DATABASE_URL']) as conn:
        url = db.get_url(conn, id=url_id)
        if url is None:
            abort(HTTPStatus.BAD_REQUEST, 'WRONG_URL_ID')

        checks = db.get_url_checks(conn, url_id)
        return render_template(
            'url.html',
            url=url,
            checks=checks,
        )


@app.post('/urls/<url_id>/checks')
def check_url(url_id):
    with db.get_connection(app.config['DATABASE_URL']) as conn:
        url = db.get_url(conn, id=url_id)
        if url is None:
            abort(HTTPStatus.BAD_REQUEST, 'WRONG_URL_ID')

        try:
            response = requests.get(url.name)
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
            message = URL_CHECK_SUCCESS
        except RequestException:
            message = URL_CHECK_FAIL
        flash(*message)
        return redirect(url_for('show_url', url_id=url_id), HTTPStatus.FOUND)


@app.errorhandler(Exception)
def handle_error(error):
    print(''.join(traceback.format_exception(*sys.exc_info())))
    status_code, messages = parse_error(error)
    return render_template(
        'error.html',
        status_code=status_code,
        messages=messages
    ), HTTPStatus.INTERNAL_SERVER_ERROR
