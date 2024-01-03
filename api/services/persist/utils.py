import json
import os
import psycopg2
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter

dumps_lambda = lambda x: json.dumps(x, ensure_ascii=False)

# register_adapter(dict, lambda x: Json(x, dumps=dumps_lambda))
register_adapter(dict, Json)
register_adapter(list, Json)

_HOME = os.environ["HOME"]
_PASSWD_FILE = f"{_HOME}/.dev_secrets/knowledge_worker_postgres_passwd"


def _get_passwd_from_local() -> str:
    with open(_PASSWD_FILE, "r") as p:
        passwd = p.read().strip()
        return passwd


_POSTGRES_HOST = os.environ.get("DB_HOST", "127.0.0.1")
_POSTGRES_USER = os.environ.get("DB_USER", "knowledge_agent")
_POSTGRES_PASS = os.environ.get("DB_PASS", _get_passwd_from_local())
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
