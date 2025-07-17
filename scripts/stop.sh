#!/bin/bash
# TUBECRAFT Stop Script

echo "🛑 TUBECRAFT を停止中..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/docker"

# Stop all services
docker-compose down

echo "✅ すべてのサービスが停止しました"
echo ""
echo "💡 データは保持されています。再起動するには:"
echo "   bash scripts/start.sh"
echo ""
echo "🗑️  データも含めて完全に削除するには:"
echo "   bash scripts/clean.sh"