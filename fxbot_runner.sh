#!/usr/bin/env bash
set -eu                                # エラー時に即終了

# ① Mac をスリープさせない（バックグラウンド）
caffeinate -dimsu &                    # display / idle / system / user :contentReference[oaicite:0]{index=0}

# ② venv 内の Python を絶対パスで呼び出す
/Users/taka/projects/fxbot/.venv/bin/python \
    /Users/taka/projects/fxbot/backtest.py \
    >> /Users/taka/projects/fxbot/fxbot.log 2>&1

# ③ ハートビート行（フェーズ0の完了判定用）
echo "DONE $(date '+%Y-%m-%d %H:%M:%S')" >> /Users/taka/projects/fxbot/fxbot.log

