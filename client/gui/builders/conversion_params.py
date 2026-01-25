"""
ConversionParams - Type-safe conversion parameter dataclass and builder.

Part of the Mediator-Shell refactoring. Provides:
- ConversionParams: Immutable dataclass for all conversion settings
- ConversionParamsBuilder: Fluent builder for constructing params from UI
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ConversionType(Enum):
    """Type of conversion to perform."""
    IMAGE = "image"
    VIDEO = "video"
    LOOP = "loop"  # GIF or WebM loop


class ResizeMode(Enum):
    """Resize mode options."""
    NONE = "No resize"
    BY_WIDTH = "By width (pixels)"
    BY_LONGER_EDGE = "By longer edge (pixels)"
    BY_RATIO = "By ratio (percent)"


class RotationAngle(Enum):
    """Rotation angle options."""
    NONE = "No rotation"
    CW_90 = "90° CW"
    CCW_90 = "90° CCW"
    ROTATE_180 = "180°"


@dataclass(frozen=True)
class ConversionParams:
    """
    Immutable dataclass containing all conversion parameters.
    
    This provides type safety and clear documentation of what
    parameters are available for each conversion type.
    """
    
    # Common fields
    conversion_type: ConversionType
    output_dir: str = ""
    suffix: str = "_converted"
    overwrite: bool = True
    
    # Output location
    output_same_folder: bool = False
    output_nested: bool = True
    nested_folder_name: str = "output"
    output_custom: bool = False
    
    # Resize settings
    resize_mode: ResizeMode = ResizeMode.NONE
    resize_value: int = 720
    multiple_resize: bool = False
    resize_variants: List[str] = field(default_factory=list)
    
    # Rotation
    rotation_angle: RotationAngle = RotationAngle.NONE
    
    # Quality (used differently by image/video/loop)
    quality: int = 40
    multiple_qualities: bool = False
    quality_variants: List[str] = field(default_factory=list)
    
    # Max size mode
    max_size_mb: Optional[float] = None
    auto_resize: bool = True
    
    # Image-specific
    image_format: Optional[str] = None  # WebP, JPG, PNG
    
    # Video-specific
    video_codec: Optional[str] = None  # MP4 (H.264), WebM (VP9), etc.
    enable_time_cutting: bool = False
    time_start: float = 0.0
    time_end: float = 1.0
    retime_enabled: bool = False
    retime_speed: float = 1.0
    
    # Loop-specific (GIF/WebM)
    loop_format: Optional[str] = None  # GIF or WebM
    gif_fps: int = 15
    gif_colors: int = 256
    gif_dither: int = 3
    gif_blur: bool = False
    gif_fps_variants: List[str] = field(default_factory=list)
    gif_colors_variants: List[str] = field(default_factory=list)
    gif_dither_variants: List[str] = field(default_factory=list)
    webm_quality: int = 30
    webm_quality_variants: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility with existing conversion engine."""
        result = {
            'type': self.conversion_type.value,
            'output_dir': self.output_dir,
            'suffix': self.suffix,
            'overwrite': self.overwrite,
            'output_same_folder': self.output_same_folder,
            'output_nested': self.output_nested,
            'nested_folder_name': self.nested_folder_name,
            'output_custom': self.output_custom,
            'rotation_angle': self.rotation_angle.value,
            'quality': self.quality,
            'multiple_qualities': self.multiple_qualities,
            'quality_variants': list(self.quality_variants),
        }
        
        # Resize
        if self.resize_mode != ResizeMode.NONE:
            result['video_size_mode'] = 'manual'
            result['resize_mode'] = self.resize_mode.value
            result['resize_value'] = self.resize_value
            result['multiple_resize'] = self.multiple_resize
            result['resize_variants'] = list(self.resize_variants)
        
        # Max size
        if self.max_size_mb is not None:
            result['video_max_size_mb'] = self.max_size_mb
            result['video_auto_resize'] = self.auto_resize
        
        # Type-specific
        if self.conversion_type == ConversionType.IMAGE:
            result['codec'] = self.image_format
            
        elif self.conversion_type == ConversionType.VIDEO:
            result['codec'] = self.video_codec
            result['enable_time_cutting'] = self.enable_time_cutting
            result['time_start'] = self.time_start
            result['time_end'] = self.time_end
            result['retime_enabled'] = self.retime_enabled
            result['retime_speed'] = self.retime_speed
            
        elif self.conversion_type == ConversionType.LOOP:
            result['loop_format'] = self.loop_format
            if self.loop_format == 'GIF':
                result['gif_fps'] = self.gif_fps
                result['gif_colors'] = self.gif_colors
                result['gif_dither'] = self.gif_dither
                result['gif_blur'] = self.gif_blur
                result['gif_fps_variants'] = list(self.gif_fps_variants)
                result['gif_colors_variants'] = list(self.gif_colors_variants)
                result['gif_dither_variants'] = list(self.gif_dither_variants)
            else:
                result['webm_quality'] = self.webm_quality
                result['webm_quality_variants'] = list(self.webm_quality_variants)
        
        return result


class ConversionParamsBuilder:
    """
    Fluent builder for constructing ConversionParams.
    
    Provides a type-safe way to build conversion parameters
    with validation and sensible defaults.
    
    Usage:
        params = (ConversionParamsBuilder()
            .set_type(ConversionType.IMAGE)
            .set_format("WebP")
            .set_quality(80)
            .build())
    """
    
    def __init__(self):
        self._params = {}
    
    def set_type(self, conversion_type: ConversionType) -> 'ConversionParamsBuilder':
        """Set the conversion type (image, video, loop)."""
        self._params['conversion_type'] = conversion_type
        return self
    
    def set_output_dir(self, path: str) -> 'ConversionParamsBuilder':
        """Set the output directory."""
        self._params['output_dir'] = path
        return self
    
    def set_suffix(self, suffix: str) -> 'ConversionParamsBuilder':
        """Set the output filename suffix."""
        self._params['suffix'] = suffix
        return self
    
    def set_overwrite(self, overwrite: bool) -> 'ConversionParamsBuilder':
        """Set whether to overwrite existing files."""
        self._params['overwrite'] = overwrite
        return self
    
    def set_output_options(self, same_folder: bool = False, nested: bool = True,
                          nested_name: str = "output", custom: bool = False) -> 'ConversionParamsBuilder':
        """Set output location options."""
        self._params['output_same_folder'] = same_folder
        self._params['output_nested'] = nested
        self._params['nested_folder_name'] = nested_name
        self._params['output_custom'] = custom
        return self
    
    def set_resize(self, mode: ResizeMode, value: int = 720,
                  multiple: bool = False, variants: List[str] = None) -> 'ConversionParamsBuilder':
        """Set resize options."""
        self._params['resize_mode'] = mode
        self._params['resize_value'] = value
        self._params['multiple_resize'] = multiple
        self._params['resize_variants'] = variants or []
        return self
    
    def set_rotation(self, angle: RotationAngle) -> 'ConversionParamsBuilder':
        """Set rotation angle."""
        self._params['rotation_angle'] = angle
        return self
    
    def set_quality(self, quality: int, multiple: bool = False,
                   variants: List[str] = None) -> 'ConversionParamsBuilder':
        """Set quality settings."""
        self._params['quality'] = quality
        self._params['multiple_qualities'] = multiple
        self._params['quality_variants'] = variants or []
        return self
    
    def set_max_size(self, max_mb: float, auto_resize: bool = True) -> 'ConversionParamsBuilder':
        """Set max file size targeting."""
        self._params['max_size_mb'] = max_mb
        self._params['auto_resize'] = auto_resize
        return self
    
    # Image-specific
    def set_image_format(self, format_name: str) -> 'ConversionParamsBuilder':
        """Set image output format (WebP, JPG, PNG)."""
        self._params['image_format'] = format_name
        return self
    
    # Video-specific
    def set_video_codec(self, codec: str) -> 'ConversionParamsBuilder':
        """Set video codec (MP4 (H.264), WebM (VP9), etc.)."""
        self._params['video_codec'] = codec
        return self
    
    def set_time_cutting(self, enabled: bool, start: float = 0.0, 
                        end: float = 1.0) -> 'ConversionParamsBuilder':
        """Set time cutting options."""
        self._params['enable_time_cutting'] = enabled
        self._params['time_start'] = start
        self._params['time_end'] = end
        return self
    
    def set_retime(self, enabled: bool, speed: float = 1.0) -> 'ConversionParamsBuilder':
        """Set retiming (speed change) options."""
        self._params['retime_enabled'] = enabled
        self._params['retime_speed'] = speed
        return self
    
    # Loop-specific
    def set_loop_format(self, format_name: str) -> 'ConversionParamsBuilder':
        """Set loop format (GIF or WebM)."""
        self._params['loop_format'] = format_name
        return self
    
    def set_gif_options(self, fps: int = 15, colors: int = 256, 
                       dither: int = 3, blur: bool = False) -> 'ConversionParamsBuilder':
        """Set GIF-specific options."""
        self._params['gif_fps'] = fps
        self._params['gif_colors'] = colors
        self._params['gif_dither'] = dither
        self._params['gif_blur'] = blur
        return self
    
    def set_gif_variants(self, fps: List[str] = None, colors: List[str] = None,
                        dither: List[str] = None) -> 'ConversionParamsBuilder':
        """Set GIF variant options."""
        self._params['gif_fps_variants'] = fps or []
        self._params['gif_colors_variants'] = colors or []
        self._params['gif_dither_variants'] = dither or []
        return self
    
    def set_webm_quality(self, quality: int = 30, 
                        variants: List[str] = None) -> 'ConversionParamsBuilder':
        """Set WebM loop quality options."""
        self._params['webm_quality'] = quality
        self._params['webm_quality_variants'] = variants or []
        return self
    
    def from_dict(self, params: dict) -> 'ConversionParamsBuilder':
        """
        Populate builder from a dictionary (legacy format).
        
        This allows gradual migration from dict-based params.
        """
        # Map type
        type_map = {'image': ConversionType.IMAGE, 'video': ConversionType.VIDEO, 'loop': ConversionType.LOOP}
        if 'type' in params:
            self._params['conversion_type'] = type_map.get(params['type'], ConversionType.IMAGE)
        
        # Direct mappings
        direct_fields = ['output_dir', 'suffix', 'overwrite', 'output_same_folder',
                        'output_nested', 'nested_folder_name', 'output_custom',
                        'quality', 'multiple_qualities', 'quality_variants',
                        'resize_value', 'multiple_resize', 'resize_variants',
                        'max_size_mb', 'auto_resize', 'image_format', 'video_codec',
                        'enable_time_cutting', 'time_start', 'time_end',
                        'retime_enabled', 'retime_speed', 'loop_format',
                        'gif_fps', 'gif_colors', 'gif_dither', 'gif_blur',
                        'gif_fps_variants', 'gif_colors_variants', 'gif_dither_variants',
                        'webm_quality', 'webm_quality_variants']
        
        for f in direct_fields:
            if f in params:
                self._params[f] = params[f]
        
        # Map rotation
        rotation_map = {
            'No rotation': RotationAngle.NONE,
            '90° CW': RotationAngle.CW_90,
            '90° CCW': RotationAngle.CCW_90,
            '180°': RotationAngle.ROTATE_180,
        }
        if 'rotation_angle' in params:
            self._params['rotation_angle'] = rotation_map.get(params['rotation_angle'], RotationAngle.NONE)
        
        # Map resize mode
        resize_map = {
            'No resize': ResizeMode.NONE,
            'By width (pixels)': ResizeMode.BY_WIDTH,
            'By longer edge (pixels)': ResizeMode.BY_LONGER_EDGE,
            'By ratio (percent)': ResizeMode.BY_RATIO,
        }
        if 'resize_mode' in params:
            self._params['resize_mode'] = resize_map.get(params['resize_mode'], ResizeMode.NONE)
        
        return self
    
    def build(self) -> ConversionParams:
        """
        Build the ConversionParams object.
        
        Raises:
            ValueError: If required fields are missing
        """
        if 'conversion_type' not in self._params:
            raise ValueError("conversion_type is required")
        
        return ConversionParams(**self._params)
    
    def build_dict(self) -> dict:
        """Build and return as dictionary for backward compatibility."""
        return self.build().to_dict()
