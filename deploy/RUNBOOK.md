# Running the 5-model bake-off on your Azure VM

The cloud dev sandbox can't reach your Azure endpoint, your images, **or** the VM
(SSH is egress-blocked there). So run this on the VM, where all three are reachable.

## 0. Prerequisites on the VM
- Python 3.10+ and `git` installed.
- The **client images** present on the VM. Point `IMAGES_ROOT` at a directory whose
  children are **one entry per client**, either:
  - a folder `\<something\>-\<clientId\>/` (e.g. `009-6779/`) containing that client's JPEGs, **or**
  - a folder containing a single 5-page PDF, **or**
  - a bare `\<clientId\>.pdf`.
  Folder names are matched on the trailing id, so `009-6779` maps to client `6779`.
- Repo access. If the repo is private, either clone it once manually with your
  GitHub credentials, or pass `REPO_URL=git@github.com:sharpmindlabs/sparkleme_ai.git`
  with an SSH deploy key on the VM.

## 1. SSH in
```bash
ssh -i SparkleMeClaude.pem azureuser@98.70.59.140
```

## 2. One-command setup + smoke test
Validates VM→Azure reachability, the API format, image loading, and JSON parsing on
a single client before spending a full run:
```bash
curl -fsSL https://raw.githubusercontent.com/sharpmindlabs/sparkleme_ai/claude/product-dev-multi-agent-s2p7eq/deploy/run_on_vm.sh -o run_on_vm.sh
# (or: git clone the repo and use deploy/run_on_vm.sh)

AZURE_FOUNDRY_API_KEY='<your-key>' \
IMAGES_ROOT='/path/to/client/images' \
bash run_on_vm.sh
```
- If the smoke test **passes**, it prints the exact commands for the full run + UI.
- If it **fails**, copy the printed error and send it to me — that error tells me
  precisely what to adjust in the Azure adapter (base URL / api-version / auth header),
  since I couldn't validate the Foundry contract from the locked-down sandbox.

## 3. Full 4-model bake-off
(grok-4.3, gpt-5.6-sol, gpt-5.4, gpt-5.6-terra — Kimi-K2.6 is text-only, so it's not a
drape judge; add it only as a text adjudicator later.)
```bash
cd ~/sparkleme_ai/services/inference_engine && source .venv/bin/activate
AZURE_FOUNDRY_API_KEY='<your-key>' SPARKLEME_IMAGES_ROOT='/path/to/client/images' \
  python -m scripts.run_models
```
Writes `results/results_<model>.json` for each model and `results/comparison.json`
with a ranked accuracy table (vs Carol's 64% first-pass baseline).

## 4. Review in the UI
```bash
cd ~/sparkleme_ai/apps/web && npm install && npm run build
cp -r dist/* ../../services/inference_engine/app/static/
cd ~/sparkleme_ai/services/inference_engine && source .venv/bin/activate
AZURE_FOUNDRY_API_KEY='<your-key>' SPARKLEME_IMAGES_ROOT='/path/to/client/images' \
  SPARKLEME_AZURE_MODEL=gpt-5.6-sol uvicorn app.api:app --host 0.0.0.0 --port 8000
# open http://98.70.59.140:8000  (open port 8000 in the VM's NSG first)
```

## 5. Share results with me
Paste `results/comparison.json` (and any `results_<model>.json`) back into the chat and
I'll analyse accuracy, the boundary confusion, and which model wins — and tune the
consolidated prompt from the misses. (Or `git push` the `results/` files to the branch.)

## Security
Rotate the Azure key and this SSH key once we're done — both were shared over chat.
