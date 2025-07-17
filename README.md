# 🎬 TUBECRAFT

AI-powered YouTube動画・Podcast自動生成システム

## 🎯 概要

TUBECRAFTは、AIを活用してYouTube動画とPodcastを完全自動で生成・投稿するオープンソースシステムです。コンテンツクリエイターの時間的制約を解決し、高品質なコンテンツの大量生産を可能にします。

### 主な機能

- ✨ **AI台本生成**: Ollama + Mistral 7Bによる自動台本作成
- 🗣️ **音声合成**: Piper TTSによる日本語音声生成
- 🎥 **動画生成**: FFmpeg + Python moviepyによる動画作成
- 📊 **コンテンツ管理**: PostgreSQL + n8nによる生成履歴管理
- 🐳 **完全Docker化**: すべてコンテナで動作

## 🚀 クイックスタート

### 前提条件

- Docker Desktop がインストール済み
- 8GB以上のメモリ推奨
- 10GB以上の空きディスク容量

### 1. リポジトリクローン

```bash
git clone https://github.com/yourusername/tubecraft.git
cd tubecraft
```

### 2. 初期セットアップ

```bash
# プロジェクト構造を初期化
bash scripts/init-project.sh

# システムセットアップ（初回のみ）
bash scripts/setup.sh
```

### 3. システム起動

```bash
# システム起動
bash scripts/start.sh
```

### 4. アクセス

- **n8n (ワークフロー)**: http://localhost:5678
  - ユーザー: `admin`
  - パスワード: `tubecraft2024`
- **Generator API**: http://localhost:8000
- **Ollama API**: http://localhost:11434

## 📁 プロジェクト構造

```
TUBECRAFT/
├── claude-knowledge/        # 仕様書・ドキュメント
├── docker/                 # Docker設定
│   ├── generator/           # ジェネレーターサービス
│   ├── manager/             # 管理サービス（Phase 2）
│   ├── shared/              # 共有設定
│   └── docker-compose.yml   # メインCompose設定
├── src/                    # ソースコード
│   ├── generator/           # コンテンツ生成サービス
│   ├── manager/             # 管理サービス
│   └── common/              # 共通ライブラリ
├── scripts/                # 実行スクリプト
├── config/                 # 設定ファイル
├── data/                   # データ保存
│   ├── audio/              # 生成音声ファイル
│   ├── video/              # 生成動画ファイル
│   └── metadata/           # メタデータ
└── tests/                  # テストコード
```

## 🔧 設定

### 環境変数

設定は `config/.env` ファイルで管理されます：

```bash
# データベース
POSTGRES_USER=tubecraft
POSTGRES_PASSWORD=tubecraft2024
POSTGRES_DB=tubecraft_db

# n8n
N8N_USER=admin
N8N_PASSWORD=tubecraft2024

# Ollama
OLLAMA_MODEL=mistral:7b

# 生成設定
VIDEO_QUALITY=high
AUDIO_SAMPLE_RATE=44100
MAX_CONCURRENT_JOBS=3
```

### カスタマイズ

1. **モデル変更**: `config/.env` の `OLLAMA_MODEL` を変更
2. **品質設定**: 動画・音声品質を調整
3. **並列処理**: `MAX_CONCURRENT_JOBS` で同時生成数を調整

## 🛠️ 開発・運用

### 便利なコマンド

```bash
# システム状態確認
bash scripts/status.sh

# ログ確認
bash scripts/logs.sh [service]

# システム停止
bash scripts/stop.sh

# 全体再起動
bash scripts/restart.sh
```

### API使用例

```bash
# エピソード作成
curl -X POST http://localhost:8000/episodes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Docker入門 - コンテナ技術の基礎", 
    "description": "初心者向けDocker解説",
    "duration_minutes": 15,
    "content_style": "educational"
  }'

# 生成状況確認
curl http://localhost:8000/episodes/{episode_id}
```

## 📊 システムアーキテクチャ

### Phase 1 (MVP)

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   n8n           │    │  Generator   │    │  PostgreSQL     │
│  (Workflow)     │◄──►│  (FastAPI)   │◄──►│  (Database)     │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────┐
│   Ollama        │    │  Piper TTS   │
│  (Mistral 7B)   │    │  (Japanese)  │
└─────────────────┘    └──────────────┘
```

### データフロー

1. **台本生成**: Ollama (Mistral 7B) → 構造化された台本
2. **音声生成**: Piper TTS → WAV/MP3音声ファイル
3. **動画生成**: FFmpeg + moviepy → MP4動画ファイル
4. **管理**: PostgreSQL → メタデータ・履歴管理

## 🔍 トラブルシューティング

### よくある問題

#### 1. ポート競合エラー
```bash
# 使用中のポート確認
lsof -i :5678
# docker-compose.ymlでポート変更
```

#### 2. メモリ不足
```bash
# Docker Desktop設定でメモリを8GB以上に増やす
# または docker-compose.yml でリソース制限調整
```

#### 3. Ollamaモデルダウンロード失敗
```bash
# 手動でモデルをプル
docker-compose exec ollama ollama pull mistral:7b
```

#### 4. 権限エラー
```bash
# データディレクトリの権限調整
chmod -R 755 data/
```

### ログ確認

```bash
# 全サービスのログ
bash scripts/logs.sh all

# 特定サービスのログ
bash scripts/logs.sh generator

# リアルタイムログ
cd docker && docker-compose logs -f
```

## 🚀 ロードマップ

### Phase 1 (Current) - MVP
- [x] 基本的なコンテンツ生成
- [x] Docker環境構築
- [x] n8nワークフロー基盤
- [ ] Web UI管理画面

### Phase 2 - 拡張機能
- [ ] YouTube API統合
- [ ] 自動投稿機能
- [ ] サムネイル生成
- [ ] 複数言語対応

### Phase 3 - エンタープライズ
- [ ] クラウドデプロイ
- [ ] API公開
- [ ] 有料プラン

## 🤝 コントリビューション

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### 開発環境セットアップ

```bash
# 開発用コンテナ起動
docker-compose -f docker-compose.dev.yml up -d

# テスト実行
bash scripts/test.sh

# リンター実行
bash scripts/lint.sh
```

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

## 🙏 謝辞

- [Ollama](https://ollama.ai/) - オープンソースLLMランタイム
- [Piper TTS](https://github.com/rhasspy/piper) - 高品質音声合成
- [n8n](https://n8n.io/) - ワークフロー自動化

## 📞 サポート

- 📧 Email: support@tubecraft.io
- 💬 Discord: [TUBECRAFT Community](https://discord.gg/tubecraft)
- 📚 Docs: [docs.tubecraft.io](https://docs.tubecraft.io)

---

**TUBECRAFT - Craft the future of content creation together! 🎬✨**