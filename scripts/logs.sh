#!/bin/bash
# TUBECRAFT Logs Script

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/docker"

SERVICE=${1:-""}
LINES=${2:-50}

if [ -z "$SERVICE" ]; then
    echo "📋 利用可能なサービス:"
    echo "  - n8n"
    echo "  - postgres"
    echo "  - ollama"
    echo "  - generator"
    echo "  - all (全サービス)"
    echo ""
    echo "使用方法: bash scripts/logs.sh [service] [lines]"
    echo "例: bash scripts/logs.sh n8n 100"
    echo ""
    echo "最新50行のログを表示します（全サービス）:"
    docker-compose logs --tail=$LINES -t
elif [ "$SERVICE" = "all" ]; then
    echo "📋 全サービスのログ（最新 $LINES 行）:"
    docker-compose logs --tail=$LINES -t
else
    # Validate service name
    case $SERVICE in
        "n8n"|"postgres"|"ollama"|"generator")
            echo "📋 $SERVICE のログ（最新 $LINES 行）:"
            docker-compose logs --tail=$LINES -t $SERVICE
            ;;
        *)
            echo "❌ 不正なサービス名: $SERVICE"
            echo "利用可能なサービス: n8n, postgres, ollama, generator, all"
            exit 1
            ;;
    esac
fi

echo ""
echo "💡 リアルタイムでログを確認するには:"
echo "   docker-compose logs -f $SERVICE"