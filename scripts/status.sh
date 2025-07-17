#!/bin/bash
# TUBECRAFT Status Check Script

echo "📊 TUBECRAFT システムステータス"
echo "================================"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/docker"

# Check if services are running
echo ""
echo "🐳 Docker コンテナ状態:"
echo "------------------------"
docker-compose ps

echo ""
echo "🌐 ネットワーク接続テスト:"
echo "---------------------------"

# Test each service
services=(
    "PostgreSQL:localhost:5432"
    "n8n:localhost:5678/healthz"
    "Ollama:localhost:11434/api/tags"
    "Generator:localhost:8000/health"
)

for service_info in "${services[@]}"; do
    service_name=$(echo "$service_info" | cut -d: -f1)
    service_url=$(echo "$service_info" | cut -d: -f2-)
    
    if [[ "$service_url" == *"/health"* ]] || [[ "$service_url" == *"/api"* ]] || [[ "$service_url" == *"healthz"* ]]; then
        # HTTP check
        if curl -s -f "http://$service_url" > /dev/null 2>&1; then
            echo "✅ $service_name: 正常応答"
        else
            echo "❌ $service_name: 応答なし"
        fi
    else
        # TCP port check for PostgreSQL
        if nc -z localhost 5432 2>/dev/null; then
            echo "✅ $service_name: ポート接続可能"
        else
            echo "❌ $service_name: ポート接続不可"
        fi
    fi
done

echo ""
echo "💾 ストレージ使用量:"
echo "--------------------"
echo "Docker volumes:"
docker volume ls | grep tubecraft

echo ""
echo "Data directory size:"
if [ -d "$PROJECT_ROOT/data" ]; then
    du -sh "$PROJECT_ROOT/data"/* 2>/dev/null || echo "データディレクトリは空です"
else
    echo "データディレクトリが見つかりません"
fi

echo ""
echo "📈 システムリソース:"
echo "--------------------"
echo "Docker stats (5秒間):"
timeout 5s docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null || echo "実行中のコンテナがありません"

echo ""
echo "🔧 便利なコマンド:"
echo "------------------"
echo "bash scripts/logs.sh [service]  # ログ確認"
echo "bash scripts/restart.sh         # 再起動"
echo "bash scripts/backup.sh          # バックアップ"