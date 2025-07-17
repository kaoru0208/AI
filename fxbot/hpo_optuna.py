import mlflow
import optuna
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

X, y = load_iris(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)


def objective(trial):
    n_est = trial.suggest_int("n_estimators", 50, 200)
    depth = trial.suggest_int("max_depth", 2, 8)
    with mlflow.start_run(nested=True):
        clf = RandomForestClassifier(
            n_estimators=n_est, max_depth=depth, random_state=42
        )
        clf.fit(Xtr, ytr)
        acc = accuracy_score(yte, clf.predict(Xte))
        mlflow.log_params({"n_estimators": n_est, "max_depth": depth})
        mlflow.log_metric("accuracy", acc)
        return acc


study = optuna.create_study(direction="maximize")
with mlflow.start_run(run_name="OptunaRandomForest"):
    study.optimize(objective, n_trials=20, show_progress_bar=False)
    print("🔎 Best accuracy:", study.best_value, "| params:", study.best_params)
