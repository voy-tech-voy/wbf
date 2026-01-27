"""
Resize Parameter Normalization

Converts UI parameters to normalized format with pre-calculated dimensions.
This eliminates the need for multiple components to re-parse and re-calculate
the same values.
"""

from typing import Dict, List, Optional, Tuple
from client.core.dimension_utils import calculate_target_dimensions
from client.core.ffmpeg_utils import get_video_dimensions, get_image_dimensions


class ResizeConfig:
    """
    Normalized resize configuration with pre-calculated dimensions.
    
    Attributes:
        mode: Resize mode ("No resize", "By width (pixels)", etc.)
        spec: Resize specification string (e.g., "L720", "50%", "1280")
        dimensions: Pre-calculated (width, height) or None
        variants: List of variant configs
    """
    
    def __init__(self, mode: str, spec: Optional[str], dimensions: Optional[Tuple[int, int]]):
        self.mode = mode
        self.spec = spec
        self.dimensions = dimensions
    
    def __repr__(self):
        return f"ResizeConfig(mode={self.mode}, spec={self.spec}, dims={self.dimensions})"


def normalize_resize_params(params: Dict, file_path: str) -> Dict:
    """
    Normalize resize parameters from UI format to engine-ready format.
    
    This function:
    1. Extracts resize parameters from the raw params dict
    2. Calculates actual dimensions for the file
    3. Returns normalized parameters with pre-calculated dimensions
    
    Args:
        params: Raw parameters from UI (contains resize_mode, resize_value, etc.)
        file_path: Path to the media file being processed
        
    Returns:
        Dictionary with normalized resize parameters:
        {
            'resize_config': ResizeConfig,  # Single resize config
            'resize_variant_configs': [ResizeConfig, ...],  # List of variant configs
            'has_resize': bool,  # Whether any resize is active
            'has_variants': bool  # Whether multiple variants are active
        }
    """
    # Get original dimensions
    width, height = get_video_dimensions(file_path)
    if width == 0:
        # Try as image
        width, height = get_image_dimensions(file_path)
    
    # Extract UI parameters
    resize_mode = params.get('resize_mode', 'No resize')
    current_resize = params.get('current_resize')
    
    # Calculate single resize config
    single_config = None
    if current_resize and resize_mode != 'No resize':
        dims = calculate_target_dimensions(file_path, current_resize, width, height)
        single_config = ResizeConfig(resize_mode, current_resize, dims)
    
    # Calculate variant configs
    variant_configs = []
    has_variants = params.get('multiple_resize') or params.get('multiple_size_variants')
    
    if has_variants:
        # Get variant list (could be under different keys)
        variant_list = (
            params.get('resize_variants') or
            params.get('video_variants') or
            params.get('gif_resize_values') or
            []
        )
        
        for variant_spec in variant_list:
            if variant_spec:
                dims = calculate_target_dimensions(file_path, variant_spec, width, height)
                variant_configs.append(ResizeConfig(resize_mode, variant_spec, dims))
    
    return {
        'resize_config': single_config,
        'resize_variant_configs': variant_configs,
        'has_resize': single_config is not None,
        'has_variants': len(variant_configs) > 0,
        'original_dimensions': (width, height)
    }


def inject_normalized_resize(params: Dict, file_path: str) -> Dict:
    """
    Inject normalized resize parameters into the params dict.
    
    This modifies the params dict in-place to add normalized resize data
    while preserving all original parameters.
    
    Args:
        params: Raw parameters dict (modified in-place)
        file_path: Path to media file
        
    Returns:
        The same params dict with added '_resize_normalized' key
    """
    normalized = normalize_resize_params(params, file_path)
    params['_resize_normalized'] = normalized
    return params


def get_resize_suffix_parts(resize_config: Optional[ResizeConfig]) -> str:
    """
    Generate suffix part for a resize configuration.
    
    Args:
        resize_config: Normalized resize configuration
        
    Returns:
        Suffix string (e.g., "_1280x720" or "")
    """
    if not resize_config or not resize_config.dimensions:
        return ""
    
    width, height = resize_config.dimensions
    return f"_{width}x{height}"
