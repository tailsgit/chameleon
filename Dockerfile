FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# System libs some renderer backends (e.g. skia) need at runtime, plus git
# (build-time only) so pip can install cr-renderer straight from its repo.
# Harmless to include even if your engine doesn't end up using them.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libegl1 \
    libglib2.0-0 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# If you add dependencies for your own resize() approach, add them to
# requirements.txt above — everything needed must install at BUILD time.
# Stage-one scoring runs with --network none, so nothing at runtime can
# reach out to the internet (no pip installs, no API calls, no model
# downloads at run time — pull those in during the build instead).

COPY chameleon_design_schema_v0.9.json .
COPY brand_kit/ ./brand_kit/
COPY renderer/ ./renderer/
COPY engine/ ./engine/
# the layout critic's feature encoder and the search's geometry helpers (no training code, no PyTorch)
COPY critic/__init__.py critic/features.py critic/damage.py ./critic/
# Optional trained critic, fetched at BUILD time (run time is offline): docker build --build-arg
# CRITIC_URL=https://huggingface.co/<user>/<repo>/resolve/main/critic.onnx . It is used only with
# CHAMELEON_CRITIC=1; without it the engine is unchanged. See HANDOFF.md.
ARG CRITIC_URL=""
RUN if [ -n "$CRITIC_URL" ]; then python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], 'engine/data/critic.onnx')" "$CRITIC_URL"; fi
# the engine ranks candidates with the same checker and scorer we benchmark with
COPY eval/*.py ./eval/

# input/ and output/ are mounted as volumes at run time (see README) —
# not baked into the image.
RUN mkdir -p /app/input /app/output

ENTRYPOINT ["python", "-m", "engine.main"]
