#!/usr/bin/env python3
"""Compress and resize images for the web (WordPress uploads).

Resizes down (never up) to a max width/height, converts to WebP/AVIF/JPEG or keeps
the original format, applies EXIF orientation, strips metadata, and prints a
savings report. Originals are never modified.

Usage:
  python optimize_images.py <file_or_dir> [more ...] -o out/ \
      [--max-width 1920] [--max-height 0] [--format webp|avif|jpeg|keep] [--quality 80]
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".bmp", ".tif", ".tiff"}
EXT = {"webp": ".webp", "avif": ".avif", "jpeg": ".jpg"}


def collect(paths):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*") if f.suffix.lower() in SUPPORTED)
        elif p.suffix.lower() in SUPPORTED:
            yield p


def target_format(src: Path, fmt: str) -> str:
    if fmt != "keep":
        return fmt
    s = src.suffix.lower()
    if s in (".jpg", ".jpeg"):
        return "jpeg"
    if s in (".png", ".gif", ".bmp", ".tif", ".tiff"):
        return "png"
    return s.lstrip(".")


def optimize(src: Path, dst_dir: Path, args, base: Path):
    with Image.open(src) as im:
        if getattr(im, "is_animated", False):
            return None, "skipped (animated: convert to MP4/WebM instead)"
        im = ImageOps.exif_transpose(im)
        orig_size = im.size

        max_w = args.max_width or im.width
        max_h = args.max_height or im.height
        if im.width > max_w or im.height > max_h:
            im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        fmt = target_format(src, args.format)
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        if fmt == "jpeg":
            if has_alpha:
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").getchannel("A"))
                im = bg
            else:
                im = im.convert("RGB")
        elif im.mode not in ("RGB", "RGBA", "L", "LA") and fmt != "png":
            im = im.convert("RGBA" if has_alpha else "RGB")

        ext = EXT.get(fmt, src.suffix.lower())
        rel = src.relative_to(base) if base in src.parents else Path(src.name)
        dst = (dst_dir / rel).with_suffix(ext)
        dst.parent.mkdir(parents=True, exist_ok=True)

        save = {}
        if fmt == "jpeg":
            save = dict(format="JPEG", quality=args.quality, optimize=True, progressive=True)
        elif fmt == "webp":
            save = dict(format="WEBP", quality=args.quality, method=6)
        elif fmt == "avif":
            save = dict(format="AVIF", quality=max(1, args.quality - 20))
        elif fmt == "png":
            save = dict(format="PNG", optimize=True)
        # EXIF/GPS is dropped (never passed to save); the ICC profile is kept for color accuracy
        icc = im.info.get("icc_profile")
        if icc and fmt in ("jpeg", "webp", "avif"):
            save["icc_profile"] = icc
        im.save(dst, **save)
        return dst, f"{orig_size[0]}x{orig_size[1]} -> {im.width}x{im.height}"


def human(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", required=True, help="output directory")
    ap.add_argument("--max-width", type=int, default=1920, help="0 = no limit")
    ap.add_argument("--max-height", type=int, default=0, help="0 = no limit")
    ap.add_argument("--format", choices=["webp", "avif", "jpeg", "keep"], default="webp")
    ap.add_argument("--quality", type=int, default=80, help="1-100 (AVIF uses quality-20)")
    args = ap.parse_args()

    out = Path(args.out)
    files = list(collect(args.inputs))
    if not files:
        sys.exit("No supported images found.")
    first = Path(args.inputs[0])
    base = first if first.is_dir() else first.parent

    total_in = total_out = 0
    print(f"{'file':40} {'dimensions':24} {'before':>8} {'after':>8} {'saved':>6}")
    for f in files:
        try:
            dst, info = optimize(f, out, args, base)
        except Exception as e:  # keep going on corrupt files
            print(f"{f.name[:40]:40} ERROR: {e}")
            continue
        before = f.stat().st_size
        if dst is None:
            print(f"{f.name[:40]:40} {info}")
            continue
        after = dst.stat().st_size
        total_in += before
        total_out += after
        pct = (1 - after / before) * 100 if before else 0
        print(f"{f.name[:40]:40} {info:24} {human(before):>8} {human(after):>8} {pct:5.0f}%")

    if total_in:
        print(f"\nTotal: {human(total_in)} -> {human(total_out)} "
              f"({(1 - total_out / total_in) * 100:.0f}% saved) | output: {out.resolve()}")


if __name__ == "__main__":
    main()
