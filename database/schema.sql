SELECT
    'CREATE DATABASE knowledge_agent'
WHERE
    NOT EXISTS (
        SELECT
        FROM
            pg_database
        WHERE
            datname = 'knowledge_agent'
    )\gexec
create schema genai;

create schema genai_ops;

-- drop table genai.summaries;
CREATE TABLE IF NOT EXISTS genai.summaries (
    hash char(64) primary key,
    summary text
);

CREATE TABLE IF NOT EXISTS genai.process_tasks (
    hash char(64),
    url text,
    task_id text,
    task_name char(40),
    status char(20),
    primary key(hash, task_id)
);

CREATE TABLE IF NOT EXISTS genai_ops.process_task_metrics (
    task_id text primary key,
    -- null for root task
    parent_id text,
    -- metrics start
    result char(30),
    started_at timestamp,
    duration real,
    -- metrics end
    CONSTRAINT fk_parent FOREIGN KEY(parent_id) REFERENCES genai_ops.process_task_metrics(task_id)
);