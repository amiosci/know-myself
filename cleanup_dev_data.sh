#!/bin/bash


# clean up database
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "delete from kms.document_paths"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "drop table kms.document_paths"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "delete from genai.summaries"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "drop table genai.summaries"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "delete from genai.process_tasks"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "drop table genai.process_tasks"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "delete from genai_ops.process_task_metrics"
docker exec -it knowledge_agent_postgres psql -U knowledge_agent -c "drop table genai_ops.process_task_metrics"

# clean up redis
docker exec -it knowledge_agent_redis redis-cli flushall

# stop ollama
ps -aux | grep 'ollama serve' | grep -v grep | awk '{print $2}' | xargs -I @ sh -c 'sudo kill -9 @'

# remove document CACHE
rm -rf $HOME/kms

