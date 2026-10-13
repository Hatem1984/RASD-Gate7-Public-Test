"""Reject near-empty screenshots before they can be accepted as article evidence."""
from pathlib import Path
from PIL import Image, ImageStat

def assess_image(path: str | Path) -> dict:
    """Compute basic visual-content metrics; conservative quality gate, not OCR."""
    with Image.open(path) as original:
        image = original.convert("L").resize((240, 180))
        stats = ImageStat.Stat(image)
        luminance_stddev = round(float(stats.stddev[0]), 2)
        values = list(image.getdata())
        dark_fraction = round(sum(v < 180 for v in values) / len(values), 4)
        accepted = luminance_stddev >= 12.0 and dark_fraction >= 0.01
        return {
            "accepted": accepted,
            "luminance_stddev": luminance_stddev,
            "dark_pixel_fraction": dark_fraction,
            "reason": "ok" if accepted else "low_visual_content_or_blank",
        }
