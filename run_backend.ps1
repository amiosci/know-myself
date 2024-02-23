function Start-Database {
    $passwordFile = "$HOME/.dev_secrets/knowledge_worker_postgres_passwd"
    if (-not (Test-Path $passwordFile)) {
        $randomPasswd = -join ((97..122) | Get-Random -Count 10 | ForEach-Object {[char]$_})
        New-Item -Path $passwordFile -ItemType File -Force
        Set-Content -Path $passwordFile -Value $randomPasswd -Force
    }

    docker run -itd `
        -e POSTGRES_USER=knowledge_agent `
        -e POSTGRES_PASSWORD_FILE=/postgres_passwd `
        -v "${passwordFile}:/postgres_passwd" `
        -v ~/data:/var/lib/postgresql/data `
        -p 5432:5432 `
        --name knowledge_agent_postgres `
        postgres
}

function Start-Redis {
    docker run -d `
        --name knowledge_agent_redis `
        -p 6379:6379 `
        -v ~/redis_data:/data `
        redis/redis-stack:latest
}

function Start-Neo4j {
    docker run -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/s3cr3t neo4j
}

Start-Database
Start-Redis
# Start-Neo4j

docker start knowledge_agent_postgres knowledge_agent_redis