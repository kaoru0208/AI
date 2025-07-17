#!/usr/bin/env bash
OUT=~/Desktop/fxbot_pkg_$(date +%Y%m%d_%H%M)
mkdir -p "$OUT"; echo "▶ OUT = $OUT"

A_PATHS="fxbot strategy.py"
B_PATHS="order_api.py data_feed.py market_order.py"
C_PATH="models"
D_PATH="sample_data"
E_PATHS="tests .github/workflows"
F_PATHS="README.md docs requirements.txt Dockerfile pyproject.toml"

EXCLUDE="*.git* *.DS_Store *.fxenv* *.venv* .mypy_cache/* __pycache__/*"

zip_safe () {
  local dst=$1; shift; local paths="$*"; local miss=0
  for p in $paths; do [[ -e $p ]] || { echo "⚠ $p が無い"; miss=1; }; done
  [[ $miss -eq 0 ]] && zip -r -y -q -s 100m "$dst" $paths -x $EXCLUDE \
                    || echo "⏩ Skip $(basename "$dst")"
}

zip_safe "$OUT/core_logic.zip"   $A_PATHS
zip_safe "$OUT/api_layer.zip"    $B_PATHS
zip_safe "$OUT/models_phase1.zip" $C_PATH
[[ -d $D_PATH ]] && tar -czf "$OUT/sample_data.tar.gz" $D_PATH || echo "⏩ Skip sample_data"
zip_safe "$OUT/tests_and_ci.zip" $E_PATHS
zip_safe "$OUT/docs_env.zip"     $F_PATHS

echo "✅ Done!"
ls -lh "$OUT"
