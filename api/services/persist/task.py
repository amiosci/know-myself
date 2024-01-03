import dataclasses
from psycopg2.extras import RealDictCursor

from services.persist.utils import get_connection


def create_processing_action(hash: str, parent_task_id: str, task_name: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            # allow re-assignments for re-processing
            curs.execute(
                "INSERT INTO genai.process_tasks (hash, parent_id, task_name, status) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT(hash, task_name) DO UPDATE SET parent_id = EXCLUDED.parent_id",
                ((hash, parent_task_id, task_name, "PENDING")),
            )


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
