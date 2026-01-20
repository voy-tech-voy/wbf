from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class PresetObject:
    """Data structure defining a single smart preset"""
    id: str
    title: str
    subtitle: str
    icon_name: str
    category: str  # "SOCIAL", "WEB", "UTILS"
    output_format: str
    params: Dict[str, str] = field(default_factory=dict)

class PresetRegistry:
    """Central registry for all smart overlay presets"""
    
    @staticmethod
    def get_all_presets() -> List[PresetObject]:
        """Return the master list of all available presets"""
        return [
            # --- SOCIAL MEDIA ---
            PresetObject(
                id="TIKTOK_HQ",
                title="TIKTOK",
                subtitle="1080x1920",
                icon_name="tiktok.svg",
                category="SOCIAL",
                output_format="mp4",
                params={"width": "1080", "height": "1920", "vcodec": "h264_nvenc", "bitrate": "15M"}
            ),
            PresetObject(
                id="INSTA_REEL",
                title="REEL",
                subtitle="1080x1920",
                icon_name="instagram.svg",
                category="SOCIAL",
                output_format="mp4",
                params={"width": "1080", "height": "1920", "vcodec": "h264_nvenc", "bitrate": "12M"}
            ),
            PresetObject(
                id="YOUTUBE_SHORTS",
                title="SHORTS",
                subtitle="1080x1920",
                icon_name="youtube.svg",
                category="SOCIAL",
                output_format="mp4",
                params={"width": "1080", "height": "1920", "vcodec": "h264_nvenc", "bitrate": "18M"}
            ),
            
            # --- WEB OPTIMIZATION ---
            PresetObject(
                id="WEB_WEBM",
                title="WEBM",
                subtitle="Optimized",
                icon_name="chrome.svg",
                category="WEB",
                output_format="webm",
                params={"vcodec": "libvpx-vp9", "crf": "30"}
            ),
            PresetObject(
                id="WEB_WEBP",
                title="WEBP",
                subtitle="Animation",
                icon_name="image.svg",
                category="WEB",
                output_format="webp",
                params={"qscale": "75", "loop": "0"}
            ),
            
            # --- UTILITIES ---
            PresetObject(
                id="GIF_HQ",
                title="GIF HQ",
                subtitle="Palette",
                icon_name="gif.svg",
                category="UTILS",
                output_format="gif",
                params={"palette_use": "true", "fps": "15"}
            ),
            PresetObject(
                id="AUDIO_ONLY",
                title="MP3",
                subtitle="Extract",
                icon_name="music.svg",
                category="UTILS",
                output_format="mp3",
                params={"acodec": "libmp3lame", "ab": "192k"}
            )
        ]

    @staticmethod
    def get_presets_by_category(category: str) -> List[PresetObject]:
        """Filter presets by category tag (case-insensitive)"""
        if category.upper() == "ALL":
            return PresetRegistry.get_all_presets()
        return [p for p in PresetRegistry.get_all_presets() if p.category.upper() == category.upper()]

    @staticmethod
    def get_preset_by_id(preset_id: str) -> Optional[PresetObject]:
        """Find a preset by its unique ID"""
        for p in PresetRegistry.get_all_presets():
            if p.id == preset_id:
                return p
        return None
