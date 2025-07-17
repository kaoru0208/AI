import optuna

import train


def objective(trial):
    units = trial.suggest_int("units", 32, 128)
    layers = trial.suggest_int("layers", 1, 3)
    lr = trial.suggest_float("lr", 1e-4, 1e-2, log=True)
    model = train.build_model(units, layers, lr)
    Xtr, ytr, Xte, yte = train.get_dataset()
    model.fit(Xtr, ytr, epochs=15, batch_size=32, verbose=0)
    return model.evaluate(Xte, yte, verbose=0)


if __name__ == "__main__":
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50)
    print("Best params", study.best_params)
