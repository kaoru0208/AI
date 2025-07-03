############ dev ############
FROM python:3.11-slim AS dev
WORKDIR /app

# 依存関係 : macOS 専用 wheel を除外
COPY requirements.txt requirements-dev.txt ./
RUN grep -vE 'tensorflow-(macos|metal)' requirements-dev.txt > req-dev-linux.txt \
 && pip install --no-cache-dir -r requirements.txt -r req-dev-linux.txt

############ tests ##########
FROM dev AS test
COPY . .
RUN pytest -q            # ユニットテスト

############ runtime ########
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体を site‑packages へ
COPY --from=test /app /app

# モジュール形式で起動
CMD ["python", "-m", "fxbot.trade"]
