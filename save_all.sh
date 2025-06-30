#!/bin/bash
BASE=/Users/taka/projects/fxbot
DEST=/Users/taka/Dropbox/fxbot_backup

# 必ず存在させるフォルダ
mkdir -p "$BASE/model" "$BASE/data" "$BASE/results"
mkdir -p "$DEST/model" "$DEST/data" "$DEST/results"

# 差分同期（--delete で不要ファイルを削除）
rsync -av --delete \
  "$BASE/model/"   "$DEST/model/"   \
  "$BASE/data/"    "$DEST/data/"    \
  "$BASE/results/" "$DEST/results/"

# ここには Git 行を置かない（使う場合は git init 後に自分で追記）

