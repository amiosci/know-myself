import dataclasses
import datetime
import enum
from psycopg2.extras import RealDictCursor
from types import TracebackType

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
class TaskRequest:
    task_name: str
    hash: str

    def __post_init__(self):
        self.task_name = self.task_name.strip()
        self.hash = self.hash.strip()


def get_task_request(task_id: str) -> TaskRequest | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(
                "SELECT t.hash, t.task_name "
                "from genai.process_tasks as t where t.task_id=%s",
                (task_id,),
            )
            row = curs.fetchone()
            if row is not None:
                return TaskRequest(**row)

            return None


def set_retry_child(original_task_id: str, retry_task_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "UPDATE genai.process_tasks SET retry_task_id=%s where task_id=%s",
                (retry_task_id, original_task_id),
            )


@dataclasses.dataclass
class ProcessingRegistration:
    hash: str
    url: str
    parent_id: str
    task_id: str
    retry_task_id: str
    task_name: str
    status: str
    status_reason: str
    updated_at: datetime.datetime = datetime.datetime.min
    has_summary: bool = False

    def __post_init__(self):
        self.hash = self.hash.strip()
        self.url = self.url.strip()
        self.status = self.status.strip()
        self.parent_id = self.parent_id.strip()

        if self.task_id:
            self.task_id = self.task_id.strip()

        if self.retry_task_id:
            self.retry_task_id = self.retry_task_id.strip()

        if self.task_name:
            self.task_name = self.task_name.strip()

        if self.status_reason:
            self.status_reason = self.status_reason.strip()


def get_processing_registrations() -> list[ProcessingRegistration]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(
                "SELECT t.hash, t.status_reason, t.updated_at, t.retry_task_id, t.task_id, "
                "t.status, t.parent_id, t.task_name, "
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


class ProcessTaskStatus(enum.Enum):
    SKIPPED = 0
    FAILED = 1
    COMPLETE = 2
    TIMEOUT = 3
    CANCELLED = 4

    def __str__(self):
        match self:
            case ProcessTaskStatus.SKIPPED:
                return "COMPLETED (SKIPPED)"
            case ProcessTaskStatus.FAILED:
                return "FAILED"
            case ProcessTaskStatus.COMPLETE:
                return "COMPLETE"
            case ProcessTaskStatus.TIMEOUT:
                return "TIMEOUT"
            case ProcessTaskStatus.CANCELLED:
                return "CANCELLED"

        raise ValueError(f"Unknown Process Status {self}")


_DEFAULT_MESSAGES = {
    ProcessTaskStatus.SKIPPED: "Task processing not required. Skipped.",
    ProcessTaskStatus.FAILED: "Task failed.",
    ProcessTaskStatus.COMPLETE: "Task processing successful.",
    ProcessTaskStatus.TIMEOUT: "Task did not complete in a timely manner.",
    ProcessTaskStatus.CANCELLED: "Task cancellation requested.",
}


@dataclasses.dataclass
class TaskResult:
    status: ProcessTaskStatus
    message: str | None = None

    def friendly_message(self) -> str:
        msg = self.message
        if msg is None:
            msg = _DEFAULT_MESSAGES[self.status]

        return msg


@dataclasses.dataclass
class ProcessTaskUpdater:
    hash: str
    task_name: str
    task_id: str

    def __enter__(self):
        return self

    def set_result(self, task_result: TaskResult):
        column_updaters = ["status=%s"]
        column_values = [str(task_result.status)]
        if task_result.message is not None:
            column_updaters.append("status_reason=%s")
            column_values.append(task_result.friendly_message())
        with get_connection() as conn:
            with conn.cursor() as curs:
                print(f"setting status {task_result.status}")
                curs.execute(
                    "UPDATE genai.process_tasks SET "
                    + ", ".join(column_updaters)
                    + " WHERE hash=%s AND task_id=%s",
                    (tuple(column_values) + (self.hash, self.task_id)),
                )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ):
        if exc_val is not None:
            self.set_result(
                TaskResult(
                    status=ProcessTaskStatus.FAILED,
                    message=str(exc_val),
                )
            )

        return True


def assign_processing_action(hash: str, task_name: str, task_id: str):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "UPDATE genai.process_tasks SET task_id=%s, status='STARTED' WHERE hash=%s AND task_name=%s",
                ((task_id, hash, task_name)),
            )

            return ProcessTaskUpdater(hash=hash, task_name=task_name, task_id=task_id)
