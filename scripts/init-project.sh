#!/bin/bash
# TUBECRAFT Project Initialization Script

set -e

echo "🚀 TUBECRAFT プロジェクト初期化開始..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Create directories
echo "📁 ディレクトリ構造を作成中..."

directories=(
    "docker/generator"
    "docker/manager"
    "docker/shared"
    "src/generator"
    "src/manager"
    "src/common"
    "scripts"
    "config"
    "data/audio"
    "data/video"
    "data/metadata"
    "tests/unit"
    "tests/integration"
    "docs"
    ".github/workflows"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo "  ✅ Created: $dir"
done

# Create .gitkeep files for empty directories
touch data/audio/.gitkeep
touch data/video/.gitkeep
touch data/metadata/.gitkeep
touch tests/unit/.gitkeep
touch tests/integration/.gitkeep

echo "✅ プロジェクト構造の初期化が完了しました！"
echo ""
echo "📝 次のステップ:"
echo "1. cd $PROJECT_ROOT"
echo "2. bash scripts/setup.sh"
echo "3. bash scripts/start.sh"