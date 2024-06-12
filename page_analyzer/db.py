import psycopg2
import psycopg2.extras


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


def get_url_data_by_name(conn, value):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM urls
            WHERE name = %s
            """,
            (value,)
        )
        return cursor.fetchone() if cursor.rowcount > 0 else ['']


def get_url_data_by_id(conn, value):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM urls
            WHERE id = %s
            """,
            (value,)
        )
        return cursor.fetchone() if cursor.rowcount > 0 else ['']


def insert_url(conn, url):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO urls (name, created_at)
            VALUES (%s, NOW())
            """, (url,))


def insert_check_data(conn, check_data):
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
            (check_data['url_id'],
             check_data['status_code'],
             check_data['h1'],
             check_data['title'],
             check_data['description'])
        )


def get_urls_list(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
        cursor.execute(
            """
            SELECT
                urls.id as url_id,
                urls.name as name,
                url_checks.status_code as status_code,
                url_checks.created_at as created_at
                FROM urls
            LEFT JOIN url_checks
            ON urls.id = url_checks.url_id
            """
        )
        if cursor.rowcount < 1:
            return
        checks = cursor.fetchall()
        url_ids = {check.url_id for check in checks}
        last_checks = []
        for url_id in url_ids:
            checks_by_url_id = [
                rec for rec in checks
                if rec.url_id == url_id
            ]
            last_checks_by_url_id = max(
                checks_by_url_id, key=lambda check: check.created_at
            )
            last_checks.append(last_checks_by_url_id)
        urls_list = [
            {
                'id': rec.url_id,
                'name': rec.name,
                'status_code': rec.status_code if rec.status_code
                is not None else '',
                'last_check_date': rec.created_at.date() if rec.created_at
                is not None else ''
            }
            for rec in last_checks
        ]
        return urls_list
