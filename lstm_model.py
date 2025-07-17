import os

import tensorflow as tf


def _file(pair):
    return f"lstm_{pair}.h5"


def train(series, pair, epochs=3):
    x = (series - series.mean()) / series.std()
    ds = tf.keras.preprocessing.timeseries_dataset_from_array(
        x[:-1, None], x[1:], sequence_length=20, batch_size=32
    )
    m = tf.keras.Sequential([tf.keras.layers.LSTM(32), tf.keras.layers.Dense(1)])
    m.compile("adam", "mse")
    m.fit(ds, epochs=epochs, verbose=0)
    m.save(_file(pair))


def predict(series, pair):
    if not os.path.exists(_file(pair)):
        return 0
    m = tf.keras.models.load_model(_file(pair))
    x = series[-20:].values.reshape(1, 20, 1)
    return float(m(x, training=False)[0, 0])
