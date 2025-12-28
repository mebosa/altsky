import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tmp" / "skycrypt" / "src" / "constants" / "skins-animations.js"
OUT = ROOT / "frontend" / "src" / "routes" / "u" / "[name]" / "p" / "[profileId]" / "petSkins.json"

# Extracts PET_SKIN_* ids and their /head/<hash> textures from SkyCrypt constants.
# Also applies ITEM_ANIMATIONS overrides found in the same file.

PET_OBJ_RE = re.compile(
    r"\{\s*id:\s*\"(PET_SKIN_[^\"]+)\"[\s\S]*?texture:\s*\"(/head/[^\"]+)\"[\s\S]*?\}\s*,?",
    re.MULTILINE,
)

ANIM_OBJ_RE = re.compile(
    r"\{\s*id:\s*\"([^\"]+)\"[\s\S]*?texture:\s*\"(/head/[^\"]+)\"[\s\S]*?\}\s*,?",
    re.MULTILINE,
)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Source file not found: {SRC}")

    text = SRC.read_text(encoding="utf-8")

    skins: dict[str, str] = {}

    # Base SKINS list (includes pet skins)
    for skin_id, texture in PET_OBJ_RE.findall(text):
        key = skin_id.removeprefix("PET_SKIN_")
        skins[key] = texture.removeprefix("/head/")

    # Apply animation overrides (some pet skins are animated and override texture)
    for any_id, texture in ANIM_OBJ_RE.findall(text):
        if not any_id.startswith("PET_SKIN_"):
            continue
        key = any_id.removeprefix("PET_SKIN_")
        skins[key] = texture.removeprefix("/head/")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ordered = {k: skins[k] for k in sorted(skins.keys())}
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {len(ordered)} pet skins to: {OUT}")


if __name__ == "__main__":
    main()
