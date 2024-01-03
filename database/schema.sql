create schema genai;
create schema genai_ops;
create schema kms;

CREATE TABLE IF NOT EXISTS kms.document_paths (
    hash char(64) primary key,
    loader_spec json,
    url text
);

CREATE TABLE IF NOT EXISTS genai.summaries (
    hash char(64) primary key,
    summary text
);

CREATE TABLE IF NOT EXISTS genai.process_tasks (
    hash char(64),
    parent_id text not null,
    -- nullable, set when started
    task_id text,
    task_name char(40),
    status char(20),
    primary key(hash, task_name)
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