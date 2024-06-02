import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for Flask application")


def execute(query, *args):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (*args,)
            )
            return cursor.fetchall() if cursor.description is not None else None


def get_checks_data(url_id):
    return execute(
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


def get_url_data_by_field(field, value):
    if data := execute(f"""
    SELECT * FROM urls
    WHERE {field} = %s
    """, value):
        return data[0]
    return ['']


def insert_url(url):
    execute("""
    INSERT INTO urls (name, created_at)
    VALUES (%s, NOW())
    """, url)


def insert_check(url_id, status_code, h1, title, description):
    execute(
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
        url_id,
        status_code,
        h1,
        title,
        description
    )


def get_urls_list():
    if result := execute(
        """
        WITH url_last_checks(url_id, created_at) AS (
            SELECT
                url_checks.url_id as url_id,
                MAX(url_checks.created_at) as created_at
            FROM url_checks
            LEFT JOIN urls
                ON url_checks.url_id = urls.id
            GROUP BY url_checks.url_id
        )
        SELECT
            urls.id as id,
            urls.name as name,
            url_checks.status_code as status_code,
            url_last_checks.created_at as created_at
            FROM urls
        LEFT JOIN url_last_checks
        ON urls.id = url_last_checks.url_id
        LEFT JOIN url_checks
        ON url_last_checks.url_id = url_checks.id
        """
    ):
        urls = [
            {
                'id': rec[0],
                'name': rec[1],
                'status_code': rec[2] or '',
                'last_check_date': rec[3].date() if rec[3]
                is not None else ''
            }
            for rec in result
        ]
        return urls
