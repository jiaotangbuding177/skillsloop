# Preparation only: not built or validated on this host.
# Resolve and record the actual base digest, apt versions and image ID on build.
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-calc libreoffice-script-provider-python fonts-liberation \
    git bash coreutils ca-certificates
RUN python -m pip install --no-cache-dir \
    openai==2.36.0 openpyxl==3.1.5 diskcache==5.6.3 httpx==0.28.1 PyYAML==6.0.3 \
    requests==2.33.1 tqdm pandas numpy
RUN git config --system --add safe.directory /workspace/research/baselines/Trace2Skill
WORKDIR /workspace/research/experiments/20261006_trace2skill_native_baseline/private/runtime_preflight/runtime
ENV PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1

