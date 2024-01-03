#!/bin/bash

export PGPASSWORD=`cat $HOME/.dev_secrets/knowledge_worker_postgres_passwd`

psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "delete from kms.document_paths"
psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "drop table kms.document_paths"

psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "delete from genai.summaries"
psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "drop table genai.summaries"

psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "delete from genai.process_tasks"
psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "drop table genai.process_tasks"

psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "delete from genai_ops.process_task_metrics"
psql -U knowledge_agent  -p 5432 -h 127.0.0.1 -c "drop table genai_ops.process_task_metrics"

docker exec -it cabc2e300cd4 redis-cli flushall

ps -aux | grep 'ollama serve' | grep -v grep | awk '{print $2}' | xargs -I @ sh -c 'sudo kill -9 @'

rm -rf $HOME/kms

