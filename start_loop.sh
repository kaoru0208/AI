#!/usr/bin/env bash
source ~/.fxbot_env                 || exit 1
source ~/venv/fxbot311/bin/activate || exit 1

SESSION=fxloop
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"
tmux new-session -d -s "$SESSION"
tmux send-keys -t "$SESSION" \
  'while true; do python ~/projects/fxbot/trade_demo.py >> ~/fxbot.log 2>&1; sleep 60; done' C-m

echo "Started.  tail -f ~/fxbot.log | grep -E \"prob=|ORDER|CLOSE|SKIP\""
