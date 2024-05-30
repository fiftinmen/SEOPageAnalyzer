from flask import (
    render_template,
    Flask,
    request,
    flash,
    get_flashed_messages,
    redirect,
    # make_response
)
from bs4 import BeautifulSoup
from requests import (
    get,
    HTTPError
)
import psycopg2
import os
from dotenv import load_dotenv
from re import fullmatch

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
app = Flask(__name__)
app.secret_key = 'super secret key'
MESSAGES = {
    "success": "Страница успешно добавлена",
    "warning": "Страница уже существует",
    "danger": "Некорректный URL"
}


def is_valid_url(url):
    if not isinstance(url, str):
        return False
    if len(url) > 255:
        return False
    return fullmatch(
        'http[s]?:[/]{2}([A-za-z.0-9_])+[A-za-z/?=+%&0-9-]*', url
    ) is not None


def get_url_data_by_field(field, value):
    cursor.execute(f"""
        SELECT * FROM urls
        WHERE {field} = %s
        """, (value,))
    return cursor.fetchone() or ['']


def parse_page(page):
    soup = BeautifulSoup(page, 'html.parser')
    description = ''
    h1 = str(soup.h1.text)[:255] if soup.h1 else ''
    title = str(soup.title.text)[:255] if soup.title else ''
    for tag in soup.find_all("meta"):
        tag_name = tag.get('name', '').lower()
        if tag_name == 'description':
            description = tag.get('content', '')[:255]
            break
    return h1, title, description


def handle_url(url):
    if not is_valid_url(url):
        return MESSAGES['danger'], "danger"
    try:
        if url not in get_url_data_by_field('name', url):
            return MESSAGES['success'], "success"
    except TypeError as e:
        return ' '.join([url, *e.args]), "danger"
    return MESSAGES['warning'], "warning"


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'index.html',
        messages=messages)


@app.post('/urls')
def add_url():
    url = request.form.to_dict().get('url')
    message, result = handle_url(url)
    flash(message, result)
    if result == 'success':
        cursor.execute("""
        INSERT INTO urls (name, created_at)
        VALUES (%s, NOW())
        """, (url,))
        conn.commit()
    if result in {'success', 'warning'}:
        url_id = get_url_data_by_field('name', url)[0]
        return redirect(f'urls/{url_id}', 302)
    return redirect('/', 302)


def get_checks_data(url_id):
    cursor.execute(
        """
        SELECT
            id,
            status_code,
            h1,
            title,
            description,
            created_at FROM url_checks
        WHERE url_id = %s
        """,
        (int(url_id),)
    )
    if cursor:
        return cursor.fetchall()


@app.get('/urls')
def show_urls_list():
    messages = get_flashed_messages(with_categories=True)
    urls = None
    cursor.execute(
        """
        WITH url_last_checks(url_id, status_code, created_at) AS (
            SELECT
                url_checks.url_id as url_id,
                url_checks.status_code as status_code,
                url_checks.created_at as created_at
            FROM url_checks
            LEFT JOIN urls
                ON url_checks.url_id = urls.id
            ORDER BY url_checks.created_at DESC
            LIMIT 1
        )
        SELECT
            urls.id as id,
            urls.name as name,
            url_last_checks.status_code as status_code,
            url_last_checks.created_at as created_at
            FROM urls
        LEFT JOIN url_last_checks
        ON urls.id = url_last_checks.url_id
        """
    )
    if cursor:
        urls = [
            {
                'id': rec[0],
                'name': rec[1],
                'status_code': rec[2] or '',
                'last_check_date': rec[3].date() if rec[3] is not None else ''
            }
            for rec in cursor.fetchall()
        ]
    return render_template(
        'urls.html',
        messages=messages,
        urls=urls
    )


@app.get('/urls/<url_id>')
def show_url_data(url_id):
    url_data = get_url_data_by_field('id', url_id)
    checks = get_checks_data(url_id)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url.html',
        messages=messages,
        id=url_id,
        name=url_data[1],
        created_at=url_data[2].date(),
        checks=checks
    )


@app.post('/urls/<url_id>/checks')
def check_url(url_id):
    url = get_url_data_by_field('id', url_id)[1]
    try:
        response = get(url)
        response.raise_for_status()
        h1, title, description = parse_page(response.text)
        conn.rollback()
        cursor.execute("""
        INSERT INTO url_checks (
            url_id,
            status_code,
            h1,
            title,
            description,
            created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            url_id,
            response.status_code,
            h1,
            title,
            description))
        conn.commit()
    except HTTPError:
        flash('Произошла ошибка при проверке', 'danger')
    return redirect(f'/urls/{url_id}', 302)
