"""
Visual content processor.

Responsibilities:
- Crop figure/table/diagram regions from the page image.
- Encode cropped images as base64 strings for submission to the VLM.
- Attach image references back to the LayoutRegion objects.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from app.services.ocr.schemas.homework import LayoutRegion, RegionType
from app.services.ocr.utils.image_utils import crop_region, ndarray_to_base64

logger = logging.getLogger(__name__)

# Region types that contain visual content worth sending to the VLM
VISUAL_TYPES = {
    RegionType.FIGURE,
    RegionType.TABLE,
    RegionType.DIAGRAM,
    RegionType.GRAPH,
}


class VisualProcessor:
    """
    Crops visual regions from the source image and prepares them for VLM input.
    """

    def __init__(self, save_dir: Optional[Path] = None):
        """
        Args:
            save_dir: If provided, cropped images are also saved to disk
                      at this path (useful for debugging / reproducibility).
        """
        self._save_dir = save_dir
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)

    def process_regions(
        self,
        img: np.ndarray,
        regions: list[LayoutRegion],
    ) -> list[LayoutRegion]:
        """
        For each visual region, crop the image and attach a base64 reference.

        Modifies regions in-place.  Returns the list.
        """
        for region in regions:
            if region.region_type not in VISUAL_TYPES:
                continue

            crop = crop_region(img, region.bbox, padding=8)
            if crop.size == 0:
                logger.warning("Empty crop for region %s — skipping", region.region_id)
                continue

            b64 = ndarray_to_base64(crop, fmt="PNG")
            region.image_reference = f"data:image/png;base64,{b64}"

            if self._save_dir:
                out_path = self._save_dir / f"{region.region_id}.png"
                import cv2
                cv2.imwrite(str(out_path), crop)
                logger.debug("Saved crop for %s → %s", region.region_id, out_path)

            logger.debug(
                "Encoded visual region %s (%s, %.0fx%.0f px)",
                region.region_id,
                region.region_type.value,
                region.bbox[2] - region.bbox[0],
                region.bbox[3] - region.bbox[1],
            )

        return regions

    def encode_full_page(self, img: np.ndarray) -> str:
        """
        Encode a full-page image as a base64 data URI for VLM consumption.
        """
        b64 = ndarray_to_base64(img, fmt="PNG")
        return f"data:image/png;base64,{b64}"
