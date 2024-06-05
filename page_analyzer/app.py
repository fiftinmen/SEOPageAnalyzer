from flask import (
    render_template,
    Flask,
    request,
    flash,
    get_flashed_messages,
    redirect,
    url_for
)
import atexit
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
conn = db.get_connection(DATABASE_URL)


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
        messages=get_flashed_messages(with_categories=True))


@app.post('/urls')
def add_url():
    url = request.form.to_dict().get('url')
    url = normalize_url(url)
    if not validators.url(url):
        flash(ADD_URL_MESSAGES['danger'], "danger")
    else:
        data = db.get_url_data_by_name(conn, url)
        if url not in data:
            flash(ADD_URL_MESSAGES['success'], 'success')
            db.insert_url(conn, url)
        else:
            flash(ADD_URL_MESSAGES['warning'], 'warning')
        url_id = db.get_url_data_by_name(conn, url)[0]
        return redirect(url_for('show_url_data', url_id=url_id), 302)
    return render_template(
        'index.html',
    ), 422


@app.get('/urls')
def show_urls_list():
    return render_template(
        'urls.html',
        urls=db.get_urls_list(conn),
    )


@app.get('/urls/<url_id>')
def show_url_data(url_id):
    url_data = db.get_url_data_by_id(conn, url_id)
    print(url_data)
    return render_template(
        'url.html',
        id=url_id,
        name=url_data[1],
        created_at=url_data[2].date(),
        checks=db.get_checks_data(conn, url_id)
    )


@app.post('/urls/<url_id>/checks')
def check_url(url_id):
    data = db.get_url_data_by_id(conn, url_id)
    try:
        url = data[1]
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
        flash(CHECK_URL_MESSAGES['success'], 'success')
    except RequestException:
        flash(CHECK_URL_MESSAGES['danger'], 'danger')
    return redirect(url_for('show_url_data', url_id=url_id), 302)
