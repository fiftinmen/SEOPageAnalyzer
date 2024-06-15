import psycopg2
import psycopg2.extras
from page_analyzer.tools import get_last_checks_for_urls


def commit(conn):
    conn.commit()


def get_connection(db_url):
    return psycopg2.connect(db_url)


def close_connection(conn):
    conn.close()


def execute(conn, query, *args):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            query,
            (*args,)
        )
        return cursor.fetchall() if cursor.rowcount > 0 else None


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
        cursor.execute(
            """
            SELECT id, url_id, status_code, created_at
            FROM url_checks
            """
        )
        checks = cursor.fetchall()
        return get_last_checks_for_urls(urls, checks)
