"""Smoke-test ONE client against ONE Azure Foundry model, printing the RAW model
response and the parsed result. Run this first to validate VM->Azure reachability,
the adapter's API format, image loading, and JSON parsing before the full bake-off.

Usage:
  SPARKLEME_PROVIDER=azure_foundry SPARKLEME_AZURE_MODEL=gpt-5.6-sol \
  AZURE_FOUNDRY_API_KEY=... SPARKLEME_IMAGES_ROOT=/path/to/images \
  python -m scripts.smoke_azure <client_id>
"""
import sys, traceback
from app.config import get_settings
from app.providers.base import get_provider
from app.images import load_client_images, find_client_dir
from app.engine import load_prompt, parse_result


def main(client_id: str) -> int:
    s = get_settings()
    print(f"provider={s.provider} model={s.model_label()} images_root={s.images_root}")
    cdir = find_client_dir(s.images_root, client_id)
    print(f"client dir: {cdir}")
    images = load_client_images(s.images_root, client_id)
    print(f"loaded {len(images)} images "
          f"({', '.join(i['media_type'] for i in images) or 'none'})")
    if not images:
        print("!! no images found — check SPARKLEME_IMAGES_ROOT and client folder names")
        return 2
    try:
        provider = get_provider(s.provider)
    except Exception as e:
        print(f"!! provider init failed: {e}")
        traceback.print_exc()
        return 3
    prompt = load_prompt()
    try:
        raw = provider.complete(prompt, "Analyse this client's five drape images and return the JSON verdict.", images)
    except Exception as e:
        print(f"!! model call FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        print("\n>> Send me this error and I'll adjust the Azure adapter "
              "(base URL / api-version / auth header).")
        return 4
    print("\n=== RAW MODEL RESPONSE (first 3000 chars) ===")
    print(raw[:3000])
    print("\n=== PARSED ===")
    try:
        res = parse_result(raw)
        print(res.model_dump_json(indent=2))
    except Exception as e:
        print(f"!! parse failed: {e} — the model didn't return clean JSON; "
              f"we may need to tighten the prompt or add response_format.")
        return 5
    print("\nOK — smoke test passed. Run the full bake-off next.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m scripts.smoke_azure <client_id>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
