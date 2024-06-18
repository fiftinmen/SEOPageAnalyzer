import psycopg2
import psycopg2.extras
from psycopg2.errors import UniqueViolation
from collections import namedtuple

UrlLastCheck = namedtuple('UrlLastCheck',
                          ['id', 'name', 'status_code', 'created_at'])
URL_INSERT_SUCCEEDED = 201
URL_ALREADY_EXIST = 501


def commit(conn):
    conn.commit()


def get_connection(db_url):
    return psycopg2.connect(db_url)


def close_connection(conn):
    conn.close()


def get_url_checks(conn, url_id):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
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
        return cursor.fetchall()


def get_url(conn, **kwargs):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        column, value = next(iter(kwargs.items()))
        cursor.execute(f"SELECT * FROM urls WHERE {column} = %s",
                       (value,))
        return cursor.fetchone()


def insert_url(conn, url):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO urls (name, created_at)
                VALUES (%s, NOW())
                RETURNING id
                """, (url,))
            return URL_INSERT_SUCCEEDED, cursor.fetchone()
        except UniqueViolation:
            conn.rollback()
            return URL_ALREADY_EXIST, get_url(conn, name=url)


def insert_url_check(conn, url_check):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO url_checks (
                url_id,
                status_code,
                h1,
                title,
                description,
                created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
            """,
            (url_check['url_id'],
             url_check['status_code'],
             url_check['h1'],
             url_check['title'],
             url_check['description'])
        )


def get_urls(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute('SELECT id, name FROM urls')
        urls = cursor.fetchall()
        if not urls:
            return

        cursor.execute(
            """
            SELECT DISTINCT id, url_id, status_code, created_at
            FROM url_checks
            ORDER BY created_at DESC
            """
        )
        checks = cursor.fetchall()
        if not checks:
            return urls
        checks_dict = {check.url_id: check for check in checks}
        urls_dict = {url.id: url.name for url in urls}
        urls_last_checks = []
        for url_id, url_name in urls_dict.items():
            url_last_check = UrlLastCheck(
                id=url_id,
                name=url_name,
                created_at=getattr(checks_dict.get(url_id, {}),
                                   'created_at', None),
                status_code=getattr(checks_dict.get(url_id, {}),
                                    'status_code', ''),
            )
            urls_last_checks.append(url_last_check)
        return urls_last_checks
