import logging
import pathlib

import numpy as np
import tensorflow as tf
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.models import load_model

# --- 既存モデル互換チェック -------------------------
MODEL_FILE = pathlib.Path("model.keras")
try:
    if MODEL_FILE.exists():
        from tensorflow.keras.models import load_model

        load_model(MODEL_FILE, compile=False)
except Exception as e:
    logging.warning("⚠️ 既存モデルを削除しました: %s", e)
    MODEL_FILE.unlink(missing_ok=True)
# ---------------------------------------------------


def build_model():
    m = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(1,))])
    m.compile(optimizer="adam", loss=MeanSquaredError())
    return m


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path = pathlib.Path("model.keras")
    if path.exists():
        model = load_model(path, compile=False)  # compile は 1 回だけ
        logging.info("✅ 既存モデルを読み込みました")
    else:
        model = build_model()
        x = np.arange(100, dtype="float32").reshape(-1, 1)
        model.fit(x, x, epochs=1, verbose=0)
        model.save(path)
        logging.info("✅ 新規学習して model.keras を保存しました")
