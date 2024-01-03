import dataclasses
import datetime
import json
import os
import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2.extras import Json, DictCursor, RealDictCursor
from psycopg2.extensions import register_adapter

register_adapter(dict, Json)

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
                return str(row[0]).strip()

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


def get_hash_url(hash: str) -> str:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT url from kms.document_paths where hash = %s", (hash,))
            row = curs.fetchone()
            if row is not None:
                return str(row[0]).strip()

            raise ValueError(f"No process found for hash [{hash}]")


def register_document(
    hash: str, url: str, loader_spec: dict[str, str], handle_exists: bool
):
    with get_connection() as conn:
        with conn.cursor() as curs:
            try:
                curs.execute(
                    "INSERT INTO kms.document_paths (hash, url, loader_spec) VALUES (%s, %s, %s)",
                    ((hash, url, loader_spec)),
                )
            except UniqueViolation:
                if not handle_exists:
                    raise


def create_processing_action(hash: str, parent_task_id: str, task_name: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            # allow re-assignments for re-processing
            curs.execute(
                "INSERT INTO genai.process_tasks (hash, parent_id, task_name, status) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT(hash, task_name) DO UPDATE SET parent_id = EXCLUDED.parent_id",
                ((hash, parent_task_id, task_name, "PENDING")),
            )


@dataclasses.dataclass
class ProcessTaskUpdater:
    hash: str
    task_name: str
    task_id: str

    def __enter__(self):
        return self

    def set_status(self, status: str):
        with get_connection() as conn:
            with conn.cursor() as curs:
                print(f"setting status {status}")
                curs.execute(
                    "UPDATE genai.process_tasks SET status=%s WHERE hash=%s AND task_name=%s",
                    ((status, self.hash, self.task_id)),
                )

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, traceback):
        if exc_val is not None:
            self.set_status("FAILED")

        return True


def assign_processing_action(hash: str, task_name: str, task_id: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "UPDATE genai.process_tasks SET task_id=%s, status='STARTED' WHERE hash=%s AND task_name=%s",
                ((task_id, hash, task_name)),
            )

            return ProcessTaskUpdater(hash=hash, task_name=task_name, task_id=task_id)


@dataclasses.dataclass
class DocumentProcessingResult:
    hash: str
    url: str
    has_summary: bool

    def __post_init__(self):
        self.hash = self.hash.strip()
        self.url = self.url.strip()

def get_loaded_documents() -> list[DocumentProcessingResult]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(
                "SELECT t.hash, t.url, "
                "EXISTS(select 1 from genai.summaries where hash=t.hash) as has_summary "
                "from kms.document_paths as t",
            )
            return [DocumentProcessingResult(**row) for row in curs]


@dataclasses.dataclass
class ProcessingRegistration:
    hash: str
    url: str
    parent_id: str
    task_id: str
    task_name: str
    status: str
    has_summary: bool = False

    def __post_init__(self):
        self.hash = self.hash.strip()
        self.url = self.url.strip()
        self.status = self.status.strip()
        self.parent_id = self.parent_id.strip()

        if self.task_id:
            self.task_id = self.task_id.strip()

        if self.task_name:
            self.task_name = self.task_name.strip()


def get_processing_registrations() -> list[ProcessingRegistration]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(
                "SELECT t.hash, t.task_id, t.status, t.parent_id, t.task_name, "
                "EXISTS(select 1 from genai.summaries where hash=t.hash) as has_summary, "
                "(select url from kms.document_paths where hash=t.hash) as url "
                "from genai.process_tasks as t",
            )
            return [ProcessingRegistration(**row) for row in curs]


def has_loader_spec_registered(loader_spec: dict) -> bool:
    with get_connection() as conn:
        with conn.cursor() as curs:
            query = "SELECT 1 from kms.document_paths where "
            spec_components = [
                f"loader_spec->>'{key}'=%s" for key in loader_spec.keys()
            ]
            spec_components_query = " and ".join(spec_components)
            query += spec_components_query
            curs.execute(
                query,
                tuple(loader_spec.values()),
            )

            return curs.fetchone() is not None


def get_processing_registration(hash: str) -> ProcessingRegistration | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(
                "SELECT url, task_id, status, task_name from genai.process_tasks where hash = %s",
                (hash,),
            )
            row = curs.fetchone()
            if row is not None:
                return ProcessingRegistration(**row)

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
