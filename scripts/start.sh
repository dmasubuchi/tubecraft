#!/bin/bash
# TUBECRAFT Start Script

set -e

echo "🚀 TUBECRAFT を起動中..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/docker"

# Check if .env exists
if [ ! -f ../config/.env ]; then
    echo "❌ 環境設定ファイルが見つかりません。"
    echo "📋 先に 'bash scripts/setup.sh' を実行してください。"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' ../config/.env | xargs)

# Start all services
echo "🐳 Docker Compose でサービスを起動中..."
docker-compose --env-file ../config/.env up -d

# Wait for services to be ready
echo "⏳ サービスの起動を待機中..."
sleep 20

# Health check for each service
services=("postgres" "ollama" "n8n" "generator")
failed_services=()

for service in "${services[@]}"; do
    container_name="tubecraft-$service"
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        # Additional health checks
        case $service in
            "postgres")
                if docker-compose exec -T postgres pg_isready -U tubecraft -d tubecraft_db > /dev/null 2>&1; then
                    echo "✅ $service: 起動成功・ヘルスチェック OK"
                else
                    echo "⚠️  $service: 起動しましたが、ヘルスチェック失敗"
                    failed_services+=($service)
                fi
                ;;
            "ollama")
                if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                    echo "✅ $service: 起動成功・API応答 OK"
                else
                    echo "⚠️  $service: 起動しましたが、API応答なし"
                    failed_services+=($service)
                fi
                ;;
            "n8n")
                if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
                    echo "✅ $service: 起動成功・ヘルスチェック OK"
                else
                    echo "⚠️  $service: 起動しましたが、ヘルスチェック失敗"
                    failed_services+=($service)
                fi
                ;;
            "generator")
                if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                    echo "✅ $service: 起動成功・ヘルスチェック OK"
                else
                    echo "⚠️  $service: 起動しましたが、ヘルスチェック失敗"
                    failed_services+=($service)
                fi
                ;;
        esac
    else
        echo "❌ $service: 起動失敗"
        failed_services+=($service)
    fi
done

echo ""

if [ ${#failed_services[@]} -eq 0 ]; then
    echo "🎉 すべてのサービスが正常に起動しました！"
else
    echo "⚠️  一部のサービスに問題があります: ${failed_services[*]}"
    echo "📋 ログを確認してください: bash scripts/logs.sh"
fi

echo ""
echo "📋 アクセス情報:"
echo "┌─────────────────────────────────────────────┐"
echo "│ サービス    │ URL                         │"
echo "├─────────────────────────────────────────────┤"
echo "│ n8n         │ http://localhost:5678       │"
echo "│ Generator   │ http://localhost:8000       │"
echo "│ Ollama API  │ http://localhost:11434      │"
echo "└─────────────────────────────────────────────┘"
echo ""
echo "🔐 n8n ログイン情報:"
echo "ユーザー名: admin"
echo "パスワード: tubecraft2024"
echo ""
echo "🔧 便利なコマンド:"
echo "- bash scripts/status.sh    # ステータス確認"
echo "- bash scripts/logs.sh      # ログ確認"
echo "- bash scripts/stop.sh      # システム停止"