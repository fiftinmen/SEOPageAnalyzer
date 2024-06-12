from flask import (
    render_template,
    Flask,
    request,
    flash,
    redirect,
    url_for
)
import os
import validators
from requests import get
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
    data = db.get_url_data_by_name(conn, url)
    if url not in data:
        flash(ADD_URL_MESSAGES['success'], 'success')
        db.insert_url(conn, url)
        db.commit(conn)
    else:
        flash(ADD_URL_MESSAGES['warning'], 'warning')
    url_id = db.get_url_data_by_name(conn, url).id
    db.close_connection(conn)
    return redirect(url_for('show_url_data', url_id=url_id), 302)


@app.get('/urls')
def show_urls_list():
    conn = db.get_connection(DATABASE_URL)
    urls_list = db.get_urls_list(conn)
    db.close_connection(conn)
    return render_template(
        'urls.html',
        urls=urls_list,
    )


@app.get('/urls/<url_id>')
def show_url_data(url_id):
    conn = db.get_connection(DATABASE_URL)
    url_data = db.get_url_data_by_id(conn, url_id)
    checks = db.get_url_checks(conn, url_id)
    db.close_connection(conn)
    return render_template(
        'url.html',
        id=url_id,
        name=url_data.name,
        created_at=url_data.created_at.date(),
        checks=checks,
    )


@app.post('/urls/<url_id>/checks')
def check_url(url_id):
    conn = db.get_connection(DATABASE_URL)
    data = db.get_url_data_by_id(conn, url_id)
    try:
        url = data.name
        response = get(url)
        response.raise_for_status()
        h1, title, description = parse_page(response.text)
        db.insert_check_data(
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
    return redirect(url_for('show_url_data', url_id=url_id), 302)
