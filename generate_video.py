"""
generate_video.py
Orchestrator: pick the next unused script from the active niche's bank,
render it to a finished MP4 in output/, write its caption/hashtags as a
.txt next to it, and advance the rotation state so the next run picks a
fresh one. Designed to be called once per scheduled run (see
.github/workflows/daily-content.yml) with zero required arguments.

Usage:
    python scripts/generate_video.py
    python scripts/generate_video.py --niche ai-tools
    python scripts/generate_video.py --count 3   # batch-produce several at once
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_video import build_video  # noqa: E402

STATE_FILE = ROOT / "content" / ".rotation_state.json"


def load_niche_config(name: str | None):
    cfg = yaml.safe_load((ROOT / "config" / "niches.yaml").read_text())
    active = name or cfg["active"]
    if active not in cfg["packs"]:
        raise SystemExit(f"Unknown niche '{active}'. Options: {list(cfg['packs'])}")
    return active, cfg["packs"][active]


def load_bank(bank_file: str):
    path = ROOT / bank_file
    if not path.exists():
        raise SystemExit(
            f"Bank file {bank_file} not found yet. Only 'money-psychology' ships "
            f"with starter scripts — add your own scripts in the same JSON shape "
            f"to activate other niches."
        )
    return json.loads(path.read_text())


def next_index(niche: str, total: int) -> int:
    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
    idx = state.get(niche, 0) % total
    state[niche] = (idx + 1) % total
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return idx


def run_once(niche_name: str | None) -> Path:
    niche_key, niche = load_niche_config(niche_name)
    bank = load_bank(niche["bank_file"])
    scripts = bank["scripts"]
    idx = next_index(niche_key, len(scripts))
    script = scripts[idx]

    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{niche_key}_{script['id']}.mp4"

    build_video(
        script=script,
        colors=tuple(niche["colors"]),
        accent_color=niche["accent_color"],
        handle=niche["handle"],
        out_path=out_path,
        music_dir=ROOT / "assets" / "music",
    )

    caption = (
        f"{script['title']}\n\n"
        f"{bank.get('disclaimer', '')}\n\n"
        + " ".join(script["hashtags"])
    )
    (out_dir / f"{niche_key}_{script['id']}.txt").write_text(caption)

    print(f"[ok] built {out_path.name}  ({script['title']})")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", default=None, help="override active niche from config/niches.yaml")
    ap.add_argument("--count", type=int, default=1, help="how many videos to produce this run")
    args = ap.parse_args()

    for _ in range(args.count):
        run_once(args.niche)


if __name__ == "__main__":
    main()
