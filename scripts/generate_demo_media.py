"""Generate stable public demo media for the GitHub README."""

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets"
WIDTH = 1280
HEIGHT = 720


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    options = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for name in options:
        path = Path(name)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def put(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    size: int,
    color: str,
    bold: bool = False,
) -> None:
    draw.text(xy, value, fill=color, font=font(size, bold))


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = "#ffffff") -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill)


def render_frame() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f6f8fb")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 92), fill="#10332b")
    put(draw, (44, 28), "tcia-cohort-forge", 34, "#ffffff", True)
    put(draw, (820, 34), "TCIA/NBIA cohort discovery workflow", 20, "#c5ded6")

    panel(draw, (44, 126, 446, 612))
    put(draw, (76, 156), "1. Discover", 25, "#194d42", True)
    commands = [
        "$ tcia-cohort-forge collections",
        "$ tcia-cohort-forge info LIDC-IDRI",
        "$ tcia-cohort-forge modalities LIDC-IDRI",
    ]
    y = 220
    for command in commands:
        draw.rounded_rectangle((76, y - 10, 414, y + 42), radius=10, fill="#eef6f2")
        put(draw, (92, y), command, 17, "#25433d")
        y += 76
    put(draw, (76, 514), "Public collections use the TCIA API.", 18, "#667085")

    panel(draw, (486, 126, 836, 612))
    put(draw, (518, 156), "2. Filter", 25, "#194d42", True)
    filters = [
        ("Collection", "LIDC-IDRI"),
        ("Modality", "CT"),
        ("Body part", "CHEST"),
        ("Series", "1,018"),
    ]
    y = 222
    for key, value in filters:
        put(draw, (522, y), key, 18, "#667085")
        put(draw, (670, y), value, 24, "#1d2939", True)
        y += 72
    draw.rounded_rectangle((520, 516, 800, 562), radius=10, fill="#dff3eb")
    put(draw, (544, 527), "Export manifest JSON", 18, "#116149", True)

    panel(draw, (876, 126, 1236, 612))
    put(draw, (908, 156), "3. Download", 25, "#194d42", True)
    folders = [
        "downloads/",
        "  LIDC-IDRI/",
        "    patient_id/",
        "      study_uid/",
        "        series_uid/",
    ]
    y = 228
    for index, folder in enumerate(folders):
        put(draw, (918, y), folder, 22, "#1d2939" if index == 0 else "#475467", index == 0)
        y += 52
    put(draw, (908, 514), "Restricted collections can use TCIA_AUTH_TOKEN.", 18, "#667085")

    put(
        draw,
        (44, 676),
        "Demo media is static and public-data oriented; it does not call the live API.",
        18,
        "#667085",
    )
    return image


def guided_frame(base: Image.Image, step: int) -> Image.Image:
    titles = (
        "1/3 Discover public collections and available metadata",
        "2/3 Filter a cohort before requesting any downloads",
        "3/3 Write a manifest and organize approved series downloads",
    )
    focus_boxes = ((44, 126, 446, 612), (486, 126, 836, 612), (876, 126, 1236, 612))
    dimmed = Image.blend(base, Image.new("RGB", base.size, "#0b1f1a"), 0.35)
    focus = focus_boxes[step]
    dimmed.paste(base.crop(focus), focus)
    draw = ImageDraw.Draw(dimmed)
    draw.rounded_rectangle(focus, radius=18, outline="#34d399", width=4)
    draw.rounded_rectangle((44, 98, 1236, 118), radius=8, fill="#e3f5ed")
    put(draw, (62, 99), titles[step], 16, "#116149", True)
    return dimmed


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    base = render_frame()
    frames = [guided_frame(base, step) for step in range(3)]
    frames[0].save(ASSET_DIR / "demo-poster.png")
    frames[0].save(
        ASSET_DIR / "demo.gif", save_all=True, append_images=frames[1:], duration=3000, loop=0
    )
    with imageio.get_writer(
        ASSET_DIR / "demo.mp4", fps=6, codec="libx264", quality=8, macro_block_size=None
    ) as writer:
        for frame in frames:
            for _ in range(18):
                writer.append_data(np.asarray(frame))


if __name__ == "__main__":
    main()
