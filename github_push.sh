#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate      # 仮想環境を必ず有効化
git add .
git commit -m "chore: first push with hooks" || echo "⚠️  既にコミット済み"
git branch -M main
echo "Remote URL? 例: https://github.com/<USER>/<REPO>.git"
read -r URL
git remote add origin "$URL" 2>/dev/null || git remote set-url origin "$URL"
git push --set-upstream origin main      # -u と同じ：今後は git push だけで OK
