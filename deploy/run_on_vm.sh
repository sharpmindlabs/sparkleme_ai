#!/usr/bin/env bash
# Turnkey setup + smoke test for the SparkleMe bake-off, run ON the Azure VM
# (where the Azure Foundry endpoint and the client images are reachable).
#
#   AZURE_FOUNDRY_API_KEY=...  IMAGES_ROOT=/path/to/client/images  bash run_on_vm.sh
#
# Optional overrides: BRANCH, REPO_URL, REPO_DIR, SMOKE_MODEL, SMOKE_CLIENT,
#                     AZURE_FOUNDRY_ENDPOINT
set -euo pipefail

: "${AZURE_FOUNDRY_API_KEY:?set AZURE_FOUNDRY_API_KEY}"
: "${IMAGES_ROOT:?set IMAGES_ROOT to the dir with per-client image folders or <id>.pdf files}"

BRANCH="${BRANCH:-claude/product-dev-multi-agent-s2p7eq}"
REPO_URL="${REPO_URL:-https://github.com/sharpmindlabs/sparkleme_ai.git}"
REPO_DIR="${REPO_DIR:-$HOME/sparkleme_ai}"
export AZURE_FOUNDRY_ENDPOINT="${AZURE_FOUNDRY_ENDPOINT:-https://sparkleme-resource.services.ai.azure.com/api/projects/sparkleme}"

echo ">>> repo: $REPO_DIR (branch $BRANCH)"
if [ ! -d "$REPO_DIR/.git" ]; then git clone "$REPO_URL" "$REPO_DIR"; fi
cd "$REPO_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

cd services/inference_engine
echo ">>> python venv + deps"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

export SPARKLEME_PROVIDER=azure_foundry
export SPARKLEME_IMAGES_ROOT="$IMAGES_ROOT"

# pick a client for the smoke test: SMOKE_CLIENT, else first entry under IMAGES_ROOT
if [ -n "${SMOKE_CLIENT:-}" ]; then
  CID="$SMOKE_CLIENT"
else
  CID="$(ls "$IMAGES_ROOT" | head -1 | sed 's/\.pdf$//' | sed 's/.*-//')"
fi
echo ">>> SMOKE TEST — client '$CID', model '${SMOKE_MODEL:-gpt-5.6-sol}'"
if SPARKLEME_AZURE_MODEL="${SMOKE_MODEL:-gpt-5.6-sol}" python -m scripts.smoke_azure "$CID"; then
  echo
  echo ">>> SMOKE OK. Run the full 4-model bake-off with:"
  echo "    cd $REPO_DIR/services/inference_engine && source .venv/bin/activate"
  echo "    AZURE_FOUNDRY_API_KEY=*** SPARKLEME_IMAGES_ROOT='$IMAGES_ROOT' python -m scripts.run_models"
  echo
  echo ">>> Then review in the UI (build once):"
  echo "    cd $REPO_DIR/apps/web && npm install && npm run build && cp -r dist/* ../../services/inference_engine/app/static/"
  echo "    cd $REPO_DIR/services/inference_engine && source .venv/bin/activate"
  echo "    AZURE_FOUNDRY_API_KEY=*** SPARKLEME_IMAGES_ROOT='$IMAGES_ROOT' uvicorn app.api:app --host 0.0.0.0 --port 8000"
  echo "    # open http://<vm-ip>:8000  (open port 8000 in the VM's NSG first)"
else
  echo ">>> SMOKE FAILED — copy the error output above and send it back; it tells us"
  echo "    exactly what to fix in the Azure adapter (base URL / api-version / auth)."
  exit 1
fi
