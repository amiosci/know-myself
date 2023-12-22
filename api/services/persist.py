import dataclasses
import datetime
import os
import psycopg2

_HOME = os.environ["HOME"]
_PASSWD_FILE = f"{_HOME}/.dev_secrets/knowledge_worker_postgres_passwd"


def get_passwd_from_local() -> str:
    with open(_PASSWD_FILE, "r") as p:
        passwd = p.read().strip()
        return passwd


_POSTGRES_HOST = os.environ.get("DB_HOST", "127.0.0.1")
_POSTGRES_USER = os.environ.get("DB_USER", "knowledge_agent")
_POSTGRES_PASS = os.environ.get("DB_PASS", get_passwd_from_local())
_POSTGRES_PORT = os.environ.get("DB_PORT", 5432)

_POSTGRES_DB = "knowledge_agent"


def get_connection_string(
    db_name: str = _POSTGRES_DB,
    protocol: str = "postgresql",
) -> str:
    return f"{protocol}://{_POSTGRES_USER}:{_POSTGRES_PASS}@{_POSTGRES_HOST}/{db_name}"


def get_connection(**kwargs):
    return psycopg2.connect(
        database=kwargs.pop("database", _POSTGRES_DB),
        host=kwargs.pop("host", _POSTGRES_HOST),
        user=kwargs.pop("user", _POSTGRES_USER),
        password=kwargs.pop("password", _POSTGRES_PASS),
        port=kwargs.pop("port", _POSTGRES_PORT),
        **kwargs,
    )


def get_summary(hash: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT summary from genai.summaries where hash = %s", (hash,))
            row = curs.fetchone()
            if row is not None:
                return row[0]

            return None


@dataclasses.dataclass
class TaskMetric:
    result: str
    duration_seconds: float
    started_at: datetime.datetime


def report_task_metrics(task_id: str, parent_id: str | None, metrics: TaskMetric):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO genai_ops.process_task_metrics (task_id, parent_id, result, started_at, duration) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    (
                        task_id,
                        parent_id,
                        metrics.result,
                        metrics.started_at,
                        metrics.duration_seconds,
                    )
                ),
            )


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


def update_processing_action(hash: str, url: str, task_id: str, status: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO genai.process_tasks (hash, url, task_id, status) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT(hash, task_id) DO UPDATE SET status = EXCLUDED.status",
                ((hash, url, task_id, status)),
            )


def update_processing_action_state(hash: str, task_id: str, status: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "UPDATE genai.process_tasks set status=%s where hash=%s and task_id=%s",
                ((status, hash, task_id)),
            )


@dataclasses.dataclass
class ProcessingRegistration:
    hash: str
    url: str
    task_id: str
    status: str
    has_summary: bool = False


def get_processing_registrations() -> list[ProcessingRegistration]:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT t.hash, t.url, t.task_id, t.status, EXISTS(select 1 from genai.summaries where hash=t.hash) "
                "from genai.process_tasks as t",
            )
            return [
                ProcessingRegistration(
                    hash=str(row[0]),
                    url=str(row[1]),
                    task_id=str(row[2]),
                    status=str(row[3]),
                    has_summary=bool(row[4]),
                )
                for row in curs
            ]


def get_processing_registration(hash: str) -> ProcessingRegistration | None:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT url, task_id, status from genai.process_tasks where hash = %s",
                (hash,),
            )
            row = curs.fetchone()
            if row is not None:
                return ProcessingRegistration(
                    hash=hash,
                    url=str(row[0]),
                    task_id=str(row[1]),
                    status=str(row[2]),
                )

            return None


def get_task_result(id: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT result from genai_ops.process_task_metrics where task_id = %s",
                (id,),
            )
            row = curs.fetchone()
            if row is not None:
                return row[0].strip()

            return None
