import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import wandb

# ---------- W&B -------------
wandb.init(
    project="fxbot-demo"
)  # プロジェクト名は任意  ✔公式Quickstart:contentReference[oaicite:1]{index=1}

# ---------- データ ----------
X, y = load_iris(
    return_X_y=True
)  # scikit‑learn Iris  ✔公式例:contentReference[oaicite:2]{index=2}
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------- 学習 ----------
with mlflow.start_run():  # MLflow run 開始
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # ---------- 評価 ----------
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)

    # ---------- ログ ----------
    mlflow.log_metric("accuracy", acc)
    mlflow.sklearn.log_model(clf, "model")  # モデル保存
    wandb.log(
        {"accuracy": acc}
    )  # W&B へメトリクス送信  ✔log API:contentReference[oaicite:3]{index=3}

    print(f"Accuracy logged to MLflow & W&B: {acc:.4f}")
