#!/usr/bin/env python3
"""Generate lightweight card thumbnails for every post cover.

For each post in _posts/ with a `cover:` (or an inferred first image) this writes

  assets/thumbs/<slug>.webp        static poster, 800 px wide  (shown immediately)
  assets/thumbs/<slug>.anim.webp   animated preview, 560 px wide (GIF covers only;
                                   loaded lazily and played on hover / when in view)

and records them in the post's front matter as `thumb:` and `thumb_anim:`.

Run it after adding a post or changing a cover:

  python3 scripts/make_thumbs.py            # only missing / outdated thumbs
  python3 scripts/make_thumbs.py --force    # rebuild everything
"""
from __future__ import annotations

import argparse
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
OUT = ROOT / "assets" / "thumbs"

POSTER_W = 800
ANIM_W = 560
ANIM_MAX_FRAMES = 90
ANIM_BUDGET = 1_600_000  # bytes; quality steps down until the preview fits

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def slug_of(path: Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)


def cover_of(fm: str, body: str) -> str | None:
    m = re.search(r'^cover:\s*"?([^"\n]+)"?\s*$', fm, re.M)
    src = m.group(1).strip() if m else None
    if not src:
        m = re.search(r'<img[^>]*data-(?:cover|thumb)[^>]*src="([^"]+)"', body) or re.search(
            r'<img[^>]*src="([^"]+)"', body
        )
        src = m.group(1) if m else None
    if not src or src.startswith("http"):
        return None
    return src.split("?")[0].lstrip("/")


def resize(im: Image.Image, width: int) -> Image.Image:
    if im.width <= width:
        return im
    h = round(im.height * width / im.width)
    return im.resize((width, h), Image.LANCZOS)


def build(job: tuple[str, str, bool]) -> tuple[str, str | None, str | None, str]:
    slug, src, force = job
    src_path = ROOT / src
    poster = OUT / f"{slug}.webp"
    anim = OUT / f"{slug}.anim.webp"
    if not src_path.exists():
        return slug, None, None, f"missing source {src}"
    stale = lambda p: force or not p.exists() or p.stat().st_mtime < src_path.stat().st_mtime

    im = Image.open(src_path)
    n = getattr(im, "n_frames", 1)
    msg = []

    if stale(poster):
        if n > 1:
            im.seek(min(n - 1, n // 4))  # a frame past any title card
        frame = im.convert("RGB")
        resize(frame, POSTER_W).save(poster, "WEBP", quality=80, method=6)
        msg.append(f"poster {poster.stat().st_size // 1024}KB")

    anim_rel = None
    if n > 1:
        if stale(anim):
            frames, durations = [], []
            step = max(1, -(-n // ANIM_MAX_FRAMES))  # ceil(n / max)
            im.seek(0)
            for i, fr in enumerate(ImageSequence.Iterator(im)):
                d = fr.info.get("duration", 80) or 80
                if i % step == 0:
                    frames.append(resize(fr.convert("RGB"), ANIM_W))
                    durations.append(d)
                else:
                    durations[-1] += d
            for q in (60, 48, 38, 30):
                frames[0].save(anim, "WEBP", save_all=True, append_images=frames[1:],
                               duration=durations, loop=0, quality=q, method=4)
                if anim.stat().st_size <= ANIM_BUDGET:
                    break
            msg.append(f"anim {len(frames)}f {anim.stat().st_size // 1024}KB")
        anim_rel = f"/assets/thumbs/{anim.name}"
    elif anim.exists():
        anim.unlink()

    return slug, f"/assets/thumbs/{poster.name}", anim_rel, ", ".join(msg) or "up to date"


def set_field(fm: str, key: str, value: str | None) -> str:
    line_re = re.compile(rf"^{key}:.*$\n?", re.M)
    fm = line_re.sub("", fm)
    if value:
        fm = fm.rstrip("\n") + f'\n{key}: "{value}"'
    return fm


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="rebuild all thumbnails")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    posts = {}
    jobs = []
    for p in sorted(POSTS.glob("*.*")):
        text = p.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            continue
        src = cover_of(m.group(1), text[m.end():])
        if not src:
            print(f"- {p.name}: no local cover, skipped")
            continue
        slug = slug_of(p)
        posts[slug] = (p, text, m)
        jobs.append((slug, src, args.force))

    with ProcessPoolExecutor() as ex:
        for slug, poster, anim, msg in ex.map(build, jobs):
            print(f"- {slug}: {msg}")
            if not poster:
                continue
            p, text, m = posts[slug]
            fm = set_field(set_field(m.group(1), "thumb", poster), "thumb_anim", anim)
            new = f"---\n{fm}\n---\n" + text[m.end():]
            if new != text:
                p.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
