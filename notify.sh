#!/usr/bin/env bash
WEB="https://discord.com/api/webhooks/XXXXXXXX"
curl -s -H "Content-Type: application/json" -X POST \
     -d "{\"content\":\"$*\"}" "$WEB" >/dev/null
