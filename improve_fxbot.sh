#!/usr/bin/env bash
set -euo pipefail
echo "▶️  fxbot 開発環境セットアップ開始"

[ -d ".venv" ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel >/dev/null
pip install -U ruff pylint mypy black isort pytest pytest-cov coverage \
             bandit pip-audit memory_profiler psutil pre-commit >/dev/null
pip freeze > requirements.txt

if [ ! -f LICENSE ]; then
cat > LICENSE <<'EOF_LICENSE'
MIT License

Copyright (c) $(date +'%Y') taka
EOF_LICENSE
fi

if [ ! -s README.md ]; then
cat > README.md <<'EOF_README'
# fxbot – AI 自動売買システム

## 概要
fxbot は OANDA REST API で完全自動 FX トレードを行う Python ボットです。  
LSTM / 強化学習モデル、Optuna による最適化、Docker デプロイに対応します。

## セットアップ
\`\`\`bash
git clone <your-repo-url>
cd fxbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\`\`\`

## ライセンス
MIT License（詳細は LICENSE を参照）
EOF_README
fi

echo "🎉  improve_fxbot.sh の処理が完了しました"
