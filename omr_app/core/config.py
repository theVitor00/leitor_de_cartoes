"""
Centralized Configuration parameters for OMR image processing, geometry, and detection thresholds.
"""

from dataclasses import dataclass, field


@dataclass
class OMRConfig:
    """
    Centralized parameters for image normalization, corner marker detection,
    and bubble grid sampling.
    """
    # Perspective canvas dimensions (Normalized A4 Aspect Ratio)
    warp_width: int = 1000
    warp_height: int = 1414

    # Corner Crop Mark Detection parameters
    min_marker_area_ratio: float = 0.0001
    max_marker_area_ratio: float = 0.02
    marker_aspect_ratio_min: float = 0.7
    marker_aspect_ratio_max: float = 1.3
    gaussian_blur_kernel: tuple[int, int] = (5, 5)
    adaptive_thresh_block_size: int = 11
    adaptive_thresh_c: int = 2

    # QR Code Search Crop Region (Ratios relative to normalized canvas)
    qr_crop_height_ratio: float = 0.35
    qr_crop_width_start_ratio: float = 0.45

    # Default OMR Bubble Threshold sensitivity
    default_sensitivity_pct: float = 45.0


# Shared default configuration instance
DEFAULT_OMR_CONFIG = OMRConfig()
