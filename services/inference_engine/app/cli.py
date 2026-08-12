"""CLI: run a batch and print a summary. Usage: python -m app.cli [client_id ...]"""
from __future__ import annotations
import sys
from .batch import run_batch


def main(argv: list[str]) -> int:
    ids = argv or None
    def prog(i, n, cr):
        mark = {"exact": "OK ", "boundary": "~OK", "miss": "XX ", "error": "ERR",
                "no_ground_truth": "?  "}.get(cr.match_kind, "?  ")
        print(f"[{i}/{n}] {mark} client {cr.client_id}: pred={cr.predicted} "
              f"carol={cr.carol_primary} ({cr.match_kind})")
    s = run_batch(client_ids=ids, only_available=True, progress=prog)
    print("\n=== SUMMARY ===")
    print(f"provider={s.provider} model={s.model} scored={s.scored} "
          f"exact={s.exact} boundary={s.boundary} miss={s.misses} err={s.errors}")
    print(f"accuracy (exact+boundary) = {s.accuracy:.1%}   exact = {s.exact_accuracy:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
