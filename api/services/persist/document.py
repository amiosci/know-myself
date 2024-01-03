import dataclasses
from psycopg2.extras import RealDictCursor
from psycopg2.errors import UniqueViolation # type: ignore

from services.persist.utils import get_connection


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
