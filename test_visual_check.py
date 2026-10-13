"""Synthetic visual gate checks; zero network, zero Gmail, no private data."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from visual_check import assess_image


class ScreenshotQualityTests(unittest.TestCase):
    def test_nearly_blank_page_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "blank.png"
            page = Image.new("RGB", (1200, 900), (244, 245, 249))
            ImageDraw.Draw(page).rectangle((10, 10, 1190, 12), fill=(160, 180, 210))
            page.save(file)
            result = assess_image(file)
            self.assertFalse(result["accepted"])

    def test_article_like_page_is_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "article.png"
            page = Image.new("RGB", (1200, 900), "white")
            draw = ImageDraw.Draw(page)
            draw.rectangle((0, 0, 1200, 170), fill=(29, 42, 63))
            for y in range(260, 730, 55):
                draw.rectangle((180, y, 1020, y+17), fill=(48, 48, 48))
            page.save(file)
            result = assess_image(file)
            self.assertTrue(result["accepted"])


if __name__ == "__main__":
    unittest.main()
