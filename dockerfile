FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv sync

COPY . .

ENV PYTHONPATH=/app
ENV GGML_BACKEND=cpu
ENV NLTK_DATA=/usr/local/share/nltk_data

RUN python - <<'PY'
import io
import os
import urllib.request
import zipfile

base = "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages"
packages = {
    "corpora": ["wordnet", "stopwords"],
    "tokenizers": ["punkt_tab"],
}

dest = os.environ.get("NLTK_DATA", "/usr/local/share/nltk_data")
os.makedirs(dest, exist_ok=True)

for group, names in packages.items():
    out_dir = os.path.join(dest, group)
    os.makedirs(out_dir, exist_ok=True)
    for name in names:
        url = f"{base}/{group}/{name}.zip"
        with urllib.request.urlopen(url) as response:
            data = response.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(out_dir)
PY

CMD ["python", "main.py"]