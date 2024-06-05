import psycopg2
from psycopg2.extensions import STATUS_BEGIN


def get_connection(db_url):
    conn = psycopg2.connect(db_url)
    return conn


def close_connection(conn):
    conn.close()


def execute(conn, query, *args):
    if conn.status == STATUS_BEGIN:
        conn.rollback()
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            (*args,)
        )
        return cursor.fetchall() if cursor.description is not None else None


def get_checks_data(conn, url_id):
    return execute(
        conn,
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
        int(url_id)
    )


def get_url_data_by_name(conn, value):
    if data := execute(conn, """
    SELECT * FROM urls
    WHERE name = %s
    """, value):
        return data[0]
    return ['']


def get_url_data_by_id(conn, value):
    if data := execute(conn, """
    SELECT * FROM urls
    WHERE id = %s
    """, value):
        return data[0]
    return ['']


def insert_url(conn, url):
    execute(conn, """
    INSERT INTO urls (name, created_at)
    VALUES (%s, NOW())
    """, url)
    conn.commit()


def insert_check_data(conn, check_data):
    execute(
        conn,
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
        check_data['url_id'],
        check_data['status_code'],
        check_data['h1'],
        check_data['title'],
        check_data['description']
    )
    conn.commit()


def get_urls_list(conn):
    if result := execute(
        conn,
        """
        WITH url_last_checks(id, url_id, status_code, created_at) AS (
            SELECT id, url_id, status_code, created_at FROM (
            SELECT
                id,
                url_id,
                status_code,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY url_id
                    ORDER BY created_at DESC
                ) as r_n
            FROM url_checks) t
            WHERE t.r_n = 1
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
    ):
        urls = [
            {
                'id': rec[0],
                'name': rec[1],
                'status_code': rec[2] if rec[2]
                is not None else '',
                'last_check_date': rec[3].date() if rec[3]
                is not None else ''
            }
            for rec in result
        ]
        return urls
