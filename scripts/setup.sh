#!/bin/bash
# TUBECRAFT Setup Script

set -e

echo "🔧 TUBECRAFT セットアップ開始..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker が起動していません。Docker Desktop を起動してください。"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f config/.env ]; then
    echo "📄 環境変数ファイルを作成中..."
    cp config/.env.example config/.env
    echo "✅ .env ファイルを作成しました（config/.env）"
    echo "⚠️  本番環境では必ずパスワードを変更してください"
else
    echo "✅ .env ファイルが既に存在します"
fi

# Create Docker network if it doesn't exist
echo "🌐 Docker ネットワークを作成中..."
docker network create tubecraft-network 2>/dev/null || echo "✅ ネットワーク 'tubecraft-network' は既に存在します"

# Pull required Docker images
echo "📥 Docker イメージをプル中..."
cd docker
docker-compose pull

# Build custom images
echo "🔨 カスタム Docker イメージをビルド中..."
docker-compose build --no-cache generator

# Start PostgreSQL first to ensure it's ready
echo "🗄️  PostgreSQL を起動中..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ PostgreSQL の起動を待機中..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U tubecraft -d tubecraft_db > /dev/null 2>&1; then
        echo "✅ PostgreSQL が起動しました"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL の起動に失敗しました"
        docker-compose logs postgres
        exit 1
    fi
    sleep 2
done

# Start Ollama and pull the model
echo "🤖 Ollama を起動中..."
docker-compose up -d ollama

echo "⏳ Ollama の起動を待機中..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama が起動しました"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Ollama の起動に失敗しました"
        docker-compose logs ollama
        exit 1
    fi
    sleep 3
done

# Pull Mistral 7B model
echo "📥 Mistral 7B モデルをダウンロード中（初回は時間がかかります）..."
if docker-compose exec -T ollama ollama list | grep -q "mistral:7b"; then
    echo "✅ Mistral 7B は既にダウンロード済みです"
else
    docker-compose exec -T ollama ollama pull mistral:7b
    echo "✅ Mistral 7B モデルのダウンロードが完了しました"
fi

echo ""
echo "✅ セットアップが完了しました！"
echo ""
echo "📋 次のステップ:"
echo "1. bash scripts/start.sh でシステムを起動"
echo "2. http://localhost:5678 で n8n にアクセス"
echo "3. ユーザー: admin, パスワード: tubecraft2024"
echo ""
echo "🔧 便利なコマンド:"
echo "- bash scripts/start.sh     # システム起動"
echo "- bash scripts/stop.sh      # システム停止"
echo "- bash scripts/status.sh    # ステータス確認"
echo "- bash scripts/logs.sh      # ログ確認"