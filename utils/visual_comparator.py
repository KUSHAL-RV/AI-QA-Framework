import os
from PIL import Image, ImageChops, ImageDraw
import logging

logger = logging.getLogger(__name__)

class VisualComparator:
    """
    Handles screenshot comparison and diff generation for visual testing.
    """
    
    BASE_DIR = "screenshots"
    BASELINE_DIR = os.path.join(BASE_DIR, "baseline")
    LATEST_DIR = os.path.join(BASE_DIR, "latest")
    DIFF_DIR = os.path.join(BASE_DIR, "diff")

    @classmethod
    def compare(cls, test_name: str, threshold: float = 0.01) -> bool:
        """
        Compares the latest screenshot with the baseline.
        Returns True if they match within the threshold.
        """
        baseline_path = os.path.join(cls.BASELINE_DIR, f"{test_name}.png")
        latest_path = os.path.join(cls.LATEST_DIR, f"{test_name}.png")
        diff_path = os.path.join(cls.DIFF_DIR, f"{test_name}_diff.png")

        if not os.path.exists(baseline_path):
            logger.info(f"No baseline found for {test_name}. Saving current as baseline.")
            os.makedirs(cls.BASELINE_DIR, exist_ok=True)
            Image.open(latest_path).save(baseline_path)
            return True

        img1 = Image.open(baseline_path).convert("RGB")
        img2 = Image.open(latest_path).convert("RGB")

        if img1.size != img2.size:
            logger.warning(f"Size mismatch for {test_name}: {img1.size} vs {img2.size}. Resizing to match baseline.")
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        diff = ImageChops.difference(img1, img2)
        
        # Calculate percentage of difference
        bbox = diff.getbbox()
        if not bbox:
            return True # Perfect match

        # Create a visual diff highlighting changes
        diff_img = Image.new("RGBA", img1.size)
        diff_img.paste(img1, (0, 0))
        
        # Highlight changed areas in red
        overlay = Image.new("RGBA", img1.size, (255, 0, 0, 80))
        mask = diff.convert("L").point(lambda x: 255 if x > 10 else 0)
        diff_img.paste(overlay, (0, 0), mask)
        
        os.makedirs(cls.DIFF_DIR, exist_ok=True)
        diff_img.save(diff_path)

        # Calculate deviation
        stat = diff.getdata()
        # Increase sensitivity threshold for CI to ignore minor color shifts/noise
        pixel_threshold = 50 if os.getenv("CI") else 30
        diff_pixels = sum(1 for p in stat if sum(p) > pixel_threshold)
        total_pixels = img1.size[0] * img1.size[1]
        deviation = diff_pixels / total_pixels

        logger.info(f"Visual deviation for {test_name}: {deviation:.4%}")
        return deviation <= threshold
