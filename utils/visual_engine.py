import os
import time
from PIL import Image, ImageChops, ImageDraw

class VisualEngine:
    @staticmethod
    def compare_screenshots(image_path_1, image_path_2, threshold=0.05, mask_regions=None):
        """
        Compares two screenshots with a configurable threshold and region masking.
        mask_regions: list of tuples (x1, y1, x2, y2) to ignore.
        """
        if not os.path.exists(image_path_1) or not os.path.exists(image_path_2):
            return False, "One of the images is missing."

        img1 = Image.open(image_path_1).convert('RGB')
        img2 = Image.open(image_path_2).convert('RGB')

        if img1.size != img2.size:
            return False, f"Size mismatch: {img1.size} vs {img2.size}"

        # Apply masking to ignore dynamic areas (like clocks or ads)
        if mask_regions:
            draw1 = ImageDraw.Draw(img1)
            draw2 = ImageDraw.Draw(img2)
            for region in mask_regions:
                # Black out the ignored regions in both images
                draw1.rectangle(region, fill=(0, 0, 0))
                draw2.rectangle(region, fill=(0, 0, 0))

        # Calculate absolute difference
        diff = ImageChops.difference(img1, img2)
        
        # Calculate percentage of different pixels
        # Get data from histogram
        h = diff.histogram()
        # Sum up all pixel differences that aren't black (0,0,0)
        sq = 0
        for i in range(1, 256):
            sq += h[i]
            
        diff_percent = sq / (img1.size[0] * img1.size[1] * 3)
        
        if diff_percent <= threshold:
            return True, f"Match! Diff: {round(diff_percent*100, 2)}%"
        else:
            diff_path = image_path_2.replace(".png", "_diff.png")
            diff.save(diff_path)
            return False, f"Mismatch! Diff: {round(diff_percent*100, 2)}%. See {diff_path}"

if __name__ == "__main__":
    # Simple test logic
    pass
