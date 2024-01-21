DO $do$
BEGIN
  IF EXISTS(
    SELECT
    FROM
      pg_database
    WHERE
      datname = 'knowledge_agent') THEN
  RAISE NOTICE 'Database already exists';
ELSE
  PERFORM
    dblink_exec('dbname=' || current_database(), 'CREATE DATABASE knowledge_agent');
END IF;
END
$do$;

CREATE SCHEMA genai;

CREATE SCHEMA genai_ops;

CREATE SCHEMA kms;

CREATE TABLE IF NOT EXISTS kms.document_paths(
  hash char(64) PRIMARY KEY,
  loader_spec jsonb NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}' ::jsonb,
  name text,
  url text
);

CREATE TABLE IF NOT EXISTS genai.summaries(
  hash char(64) PRIMARY KEY,
  summary text
);

CREATE TABLE IF NOT EXISTS genai.process_tasks(
  hash char(64),
  parent_id text NOT NULL,
  -- nullable, set when started
  task_id text,
  -- nullable, only set if reprocess request is emitted
  retry_task_id text,
  task_name char(40),
  status char(20),
  status_reason text,
  updated_at timestamp DEFAULT now(),
  PRIMARY KEY (hash, task_name)
);

CREATE OR REPLACE FUNCTION sync_updated_at()
  RETURNS TRIGGER
  AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER tr_sync_updated_at
  BEFORE UPDATE ON genai.process_tasks
  FOR EACH ROW
  EXECUTE PROCEDURE sync_updated_at();

CREATE TABLE IF NOT EXISTS genai_ops.process_task_metrics(
  metric_id bigserial PRIMARY KEY,
  task_id text,
  -- metrics start
  result char(30),
  started_at timestamp,
  duration real
);

