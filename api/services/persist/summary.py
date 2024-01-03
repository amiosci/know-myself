from services.persist.utils import get_connection


def get_summary(hash: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT summary from genai.summaries where hash = %s", (hash,))
            row = curs.fetchone()
            if row is not None:
                return str(row[0]).strip()

            return None


def has_summary(hash: str) -> bool:
    return get_summary(hash) is not None


def save_summary(hash: str, summary: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            # upsert summary
            curs.execute(
                "INSERT INTO genai.summaries (hash, summary) VALUES (%s, %s) "
                "ON CONFLICT(hash) DO UPDATE SET summary = EXCLUDED.summary",
                ((hash, summary)),
            )
