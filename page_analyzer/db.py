import psycopg2
import psycopg2.extras
from collections import namedtuple

UrlLastCheck = namedtuple('UrlLastCheck',
                          ['id', 'name', 'status_code', 'created_at'])


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


def get_url_by_name(conn, value):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM urls
            WHERE name = %s
            """,
            (value,)
        )
        return cursor.fetchone()


def get_url_by_id(conn, value):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM urls
            WHERE id = %s
            """,
            (value,)
        )
        return cursor.fetchone()


def insert_url(conn, url):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO urls (name, created_at)
            VALUES (%s, NOW())
            """, (url,))


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

        urls_last_checks = []
        for url in urls:
            last_check = None
            for check in checks:
                if check.url_id == url.id:
                    last_check = check
                    checks.remove(last_check)
            url_last_check = UrlLastCheck(
                id=url.id,
                name=url.name,
                created_at=getattr(last_check, 'created_at', None),
                status_code=getattr(last_check, 'status_code', ''),
            )
            urls_last_checks.append(url_last_check)
        return urls_last_checks
