"""
Core conversion engine for graphics files
Integrates FFmpeg operations with bundled tools
"""


import os
import sys
import subprocess
import hashlib
import json
import time
from client.version import APP_NAME

# Set the FFmpeg executable path BEFORE importing ffmpeg
bundled_tools_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools')

# Default cache path (lazy init). We keep PATH untouched until tools are explicitly initialized.
_USER_BIN_CACHE = ""

def _ensure_bundled_tools_unpacked() -> str:
    """Ensure bundled tools are available as distinct files.

    For onefile PyInstaller builds, PyInstaller extracts bundled files into sys._MEIPASS.
    This helper copies them into a persistent cache directory (per-user) so we have stable file paths
    and avoid re-extraction overhead. Returns the path to the cache directory.
    """
    # Choose platform-specific cache dir
    try:
        if os.name == 'nt':
            cache_root = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA') or os.path.expanduser('~')
        else:
            cache_root = os.getenv('XDG_CACHE_HOME') or os.path.expanduser('~/.cache')
        app_cache_dir = os.path.join(cache_root, APP_NAME, 'bin')
        os.makedirs(app_cache_dir, exist_ok=True)

        # If running frozen, copy from sys._MEIPASS/bundled_tools into cache
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            src_tools = os.path.join(sys._MEIPASS, 'tools')

            def _sha256_of_file(path: str) -> str:
                h = hashlib.sha256()
                with open(path, 'rb') as fh:
                    for chunk in iter(lambda: fh.read(8192), b''):
                        h.update(chunk)
                return h.hexdigest()

            def _read_checksums_from_dir(d: str) -> dict:
                # look for JSON or .sha256 files
                possible_names = ['checksums.json', 'bundled_tools_checksums.json', 'checksums.sha256']
                for fname in possible_names:
                    fpath = os.path.join(d, fname)
                    if os.path.exists(fpath):
                        try:
                            if fname.endswith('.json'):
                                with open(fpath, 'r', encoding='utf-8') as fh:
                                    data = json.load(fh)
                                    if isinstance(data, dict):
                                        return {k: str(v) for k, v in data.items()}
                            else:
                                checks = {}
                                with open(fpath, 'r', encoding='utf-8') as fh:
                                    for line in fh:
                                        parts = line.strip().split()
                                        if len(parts) >= 2:
                                            h = parts[0]
                                            name = parts[-1]
                                            checks[name] = h
                                return checks
                        except Exception:
                            pass
                return {}

            expected_checksums = _read_checksums_from_dir(src_tools) if os.path.isdir(src_tools) else {}

            if os.path.isdir(src_tools):
                for name in os.listdir(src_tools):
                    src = os.path.join(src_tools, name)
                    dst = os.path.join(app_cache_dir, name)
                    try:
                        # Only copy if not present or sizes differ
                        if (not os.path.exists(dst)) or (os.path.getsize(src) != os.path.getsize(dst)):
                            # write to temporary then move to be atomic
                            tmp = dst + '.tmp'
                            with open(src, 'rb') as sf, open(tmp, 'wb') as df:
                                df.write(sf.read())
                            try:
                                os.replace(tmp, dst)
                            except Exception:
                                # fallback
                                try:
                                    os.remove(tmp)
                                except Exception:
                                    pass
                                import shutil
                                shutil.copy2(src, dst)
                            # ensure executable on unix
                            if os.name != 'nt':
                                try:
                                    os.chmod(dst, 0o755)
                                except Exception:
                                    pass

                            # verify checksum if expected available
                            try:
                                expected = expected_checksums.get(name)
                                if expected:
                                    actual = _sha256_of_file(dst)
                                    if actual.lower() != expected.lower():
                                        # Attempt second copy and re-verify
                                        try:
                                            os.remove(dst)
                                        except Exception:
                                            pass
                                        tmp2 = dst + '.tmp2'
                                        with open(src, 'rb') as sf, open(tmp2, 'wb') as df:
                                            df.write(sf.read())
                                        try:
                                            os.replace(tmp2, dst)
                                        except Exception:
                                            try:
                                                os.remove(tmp2)
                                            except Exception:
                                                pass
                                        if os.name != 'nt':
                                            try:
                                                os.chmod(dst, 0o755)
                                            except Exception:
                                                pass
                                        try:
                                            actual2 = _sha256_of_file(dst)
                                            if actual2.lower() != expected.lower():
                                                # checksum mismatch; remove broken file
                                                try:
                                                    os.remove(dst)
                                                except Exception:
                                                    pass
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                    except Exception:
                        # ignore single-file copy errors (we'll fallback to sys._MEIPASS path)
                        pass

        # If a checksums.json was not already created in the cache, generate one (frozen runs)
        try:
            src_tools = os.path.join(sys._MEIPASS, 'tools') if (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')) else None
            checks_dst = os.path.join(app_cache_dir, 'checksums.json')
            if src_tools and os.path.isdir(src_tools) and not os.path.exists(checks_dst):
                checks = {}
                for name in os.listdir(src_tools):
                    # skip checksum files themselves
                    if name.lower().endswith(('.json', '.sha256')):
                        continue
                    p_in_cache = os.path.join(app_cache_dir, name)
                    s = None
                    try:
                        if os.path.exists(p_in_cache):
                            s = hashlib.sha256(open(p_in_cache, 'rb').read()).hexdigest()
                        else:
                            srcp = os.path.join(src_tools, name)
                            if os.path.exists(srcp):
                                s = hashlib.sha256(open(srcp, 'rb').read()).hexdigest()
                    except Exception:
                        s = None
                    if s:
                        checks[name] = s
                if checks:
                    try:
                        with open(checks_dst, 'w', encoding='utf-8') as fh:
                            json.dump(checks, fh)
                    except Exception:
                        pass
        except Exception:
            pass

        return app_cache_dir
    except Exception:
        # Fallback to temp dir
        return tempfile.gettempdir()

# Lazy initialization of bundled tools (used by onefile builds). Call once after login.
_BUNDLED_TOOLS_INITIALIZED = False

def init_bundled_tools() -> str:
    """Initialize bundled tools (unpack and set PATH/FFMPEG envs). Safe to call multiple times."""
    global _USER_BIN_CACHE, _BUNDLED_TOOLS_INITIALIZED
    if _BUNDLED_TOOLS_INITIALIZED and _USER_BIN_CACHE:
        return _USER_BIN_CACHE

    _USER_BIN_CACHE = _ensure_bundled_tools_unpacked()

    # For frozen onefile builds, add the persistent user cache to PATH so subprocesses can find binaries
    if getattr(sys, 'frozen', False) and os.path.isdir(_USER_BIN_CACHE):
        os.environ['PATH'] = _USER_BIN_CACHE + os.pathsep + os.environ.get('PATH', '')
    elif not getattr(sys, 'frozen', False):
        # Dev runs: keep bundled_tools on PATH for convenience
        os.environ['PATH'] = bundled_tools_dir + os.pathsep + os.environ.get('PATH', '')

    # Set FFMPEG_BINARY environment variable to point to correct ffmpeg binary when available
    ffmpeg_candidate = None
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        ffmpeg_candidate = os.path.join(sys._MEIPASS, 'tools', 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_candidate):
            ffmpeg_candidate = os.path.join(_USER_BIN_CACHE, 'ffmpeg.exe')
    else:
        ffmpeg_candidate = os.path.join(bundled_tools_dir, 'ffmpeg.exe')

    if ffmpeg_candidate and os.path.exists(ffmpeg_candidate):
        os.environ['FFMPEG_BINARY'] = ffmpeg_candidate

    # Set ffprobe as well (used by ffmpeg.probe())
    ffprobe_candidate = None
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        ffprobe_candidate = os.path.join(sys._MEIPASS, 'tools', 'ffprobe.exe')
        if not os.path.exists(ffprobe_candidate):
            ffprobe_candidate = os.path.join(_USER_BIN_CACHE, 'ffprobe.exe')
    else:
        ffprobe_candidate = os.path.join(bundled_tools_dir, 'ffprobe.exe')

    if ffprobe_candidate and os.path.exists(ffprobe_candidate):
        os.environ['FFPROBE_BINARY'] = ffprobe_candidate

    _BUNDLED_TOOLS_INITIALIZED = True
    return _USER_BIN_CACHE

import ffmpeg
from pathlib import Path
from typing import List, Dict, Optional, Callable
from PyQt6.QtCore import QThread, pyqtSignal
import tempfile

# Hide subprocess consoles on Windows without altering ffmpeg-python signatures
if os.name == 'nt':
    _orig_popen = subprocess.Popen

    def _popen_no_console(*args, **kwargs):
        """Wrap subprocess.Popen to suppress console windows on Windows"""
        creationflags = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
        kwargs['creationflags'] = creationflags

        startupinfo = kwargs.get('startupinfo')
        if startupinfo is None:
            startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs['startupinfo'] = startupinfo

        return _orig_popen(*args, **kwargs)

    subprocess.Popen = _popen_no_console

def ensure_output_directory_exists(output_path: str) -> bool:
    """
    Ensure the output directory exists, creating it if necessary
    Returns True if directory exists/was created, False on error
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            mkdir(output_dir)
        return True
    except Exception as e:
        print(f"Failed to create output directory for {output_path}: {e}")
        return False


def mkdir(path: str) -> None:
    """
    Recursively create directories using os.mkdir() for each missing level
    """
    if not path or os.path.exists(path):
        return

    # Create parent directories first
    parent = os.path.dirname(path)
    if parent and parent != path:  # Avoid infinite recursion
        mkdir(parent)

    # Create this directory level
    try:
        os.mkdir(path)
    except FileExistsError:
        # Directory already exists, which is fine
        pass

def get_bundled_tool_path(tool_name: str) -> str:
    """
    Get path to bundled tool executable
    Falls back to system PATH if bundled version not found
    """
    """
    Locate a bundled tool executable, preferring a persistent per-user cache for onefile builds.

    Order of resolution:
    1. Persistent user cache (created by _ensure_bundled_tools_unpacked) when available
    2. PyInstaller extraction dir sys._MEIPASS (when frozen)
    3. Project bundled_tools folder (development)
    4. Fallback to tool name (system PATH)
    """
    # On Windows the bundled files are .exe; on *nix they are assumed to be the tool name as-is
    tool_filename = f"{tool_name}.exe" if os.name == 'nt' else tool_name

    # Ensure tools are initialized before resolving paths
    init_bundled_tools()

    candidates = []

    # 1) persistent user cache
    try:
        if _USER_BIN_CACHE:
            candidates.append(os.path.join(_USER_BIN_CACHE, tool_filename))
    except Exception:
        pass

    # 2) PyInstaller extracted bundled_tools
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, 'tools', tool_filename))

    # 3) repo bundled_tools for development
    candidates.append(os.path.join(bundled_tools_dir, tool_filename))

    for path in candidates:
        if os.path.exists(path):
            # Ensure executable permission on non-Windows
            try:
                if os.name != 'nt':
                    st = os.stat(path)
                    # Grant owner execute bit if not present
                    if not (st.st_mode & 0o100):
                        os.chmod(path, st.st_mode | 0o100)
            except Exception:
                pass
            return path

    # Fallback: return the bare tool name so system PATH resolution can be used
    return tool_name

def get_subprocess_kwargs():
    """
    Get subprocess kwargs to hide console windows on Windows
    """
    kwargs = {'capture_output': True, 'text': True}
    
    if os.name == 'nt':  # Windows
        # Hide console window
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    return kwargs

def map_ui_quality_to_crf(ui_quality: int, codec: str = 'generic') -> int:
    """
    Map UI quality value (0-100) to CRF value.
    Higher UI quality = Lower CRF (Better).
    
    Ranges:
    - x264/x265: 0-51 (0 is lossless, 51 is worst)
    - VP9/AV1: 0-63 (0 is lossless, 63 is worst)
    """
    # Determine max CRF based on codec
    if 'libx264' in codec or 'libx265' in codec:
        max_crf = 51
    elif 'vp9' in codec or 'av1' in codec or 'libvpx' in codec or 'libaom' in codec:
        max_crf = 63
    else:
        max_crf = 51 # Default safe limit

    # Invert: UI 100 -> CRF 0, UI 0 -> max_crf
    # Ensure ui_quality is clamped 0-100
    ui_quality = max(0, min(100, int(ui_quality)))
    return int((100 - ui_quality) * (max_crf / 100.0))

def get_image_dimensions(file_path: str) -> tuple:
    """
    Get image dimensions using FFmpeg probe, accounting for EXIF rotation
    Returns (width, height) after applying rotation, or (0, 0) if unable to determine
    """
    try:
        probe = ffmpeg.probe(file_path)
        # Try video stream first (for images, they're treated as single-frame videos)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            
            # Check for EXIF rotation (side_data_list or tags.rotate)
            rotation = 0
            
            # Method 1: Check side_data_list for displaymatrix rotation
            if 'side_data_list' in video_stream:
                for side_data in video_stream['side_data_list']:
                    if side_data.get('side_data_type') == 'Display Matrix':
                        rotation = side_data.get('rotation', 0)
                        break
            
            # Method 2: Check tags.rotate
            if rotation == 0 and 'tags' in video_stream:
                rotation = int(video_stream['tags'].get('rotate', 0))
            
            # Swap dimensions if rotation is 90 or 270 degrees
            if abs(rotation) == 90 or abs(rotation) == 270:
                return (height, width)  # Swap for portrait orientation
            
            return (width, height)
    except Exception:
        pass
    return (0, 0)

def get_video_dimensions(file_path: str) -> tuple:
    """
    Get video dimensions using FFmpeg
    Returns (width, height) or (0, 0) if unable to determine
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            return (width, height)
    except Exception:
        pass
    return (0, 0)

def get_video_duration(file_path: str) -> float:
    """
    Get video duration in seconds using FFmpeg probe
    Returns duration in seconds or 0.0 if unable to determine
    """
    try:
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception:
        return 0.0

def has_audio_stream(file_path: str) -> bool:
    """
    Check if video file has an audio stream using FFmpeg probe
    Returns True if audio stream exists, False otherwise
    """
    try:
        probe = ffmpeg.probe(file_path)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        return audio_stream is not None
    except Exception:
        return False

def validate_resize_dimensions(original_width: int, original_height: int, target_width: int) -> int:
    """
    Validate and adjust resize dimensions to prevent upscaling beyond original size
    Returns the validated width (clamped to original if too large)
    """
    if target_width > original_width:
        return original_width
    return target_width


def clamp_resize_width(original_width: int, target_width: int) -> int:
    """Clamp target width to original width if larger; return target_width when unknown."""
    if original_width and target_width > original_width:
        return original_width
    return target_width


def calculate_longer_edge_resize(original_width: int, original_height: int, target_longer_edge: int) -> tuple:
    """
    Calculate new dimensions based on longer edge resize (no upscaling).
    Returns (new_width, new_height) or (original_width, original_height) if no resize needed.
    
    Rules:
    - Identify the longer edge
    - Scale so longer edge becomes target_longer_edge
    - If longer edge is already smaller than target, don't resize
    - Maintain aspect ratio
    """
    if not original_width or not original_height:
        return (original_width, original_height)
    
    longer_edge = max(original_width, original_height)
    
    # Don't upscale if longer edge is already smaller than target
    if longer_edge < target_longer_edge:
        return (original_width, original_height)
    
    # Calculate scale factor based on longer edge
    scale_factor = target_longer_edge / longer_edge
    
    # Calculate new dimensions maintaining aspect ratio
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    # Ensure even dimensions (required for some codecs)
    new_width = new_width if new_width % 2 == 0 else new_width - 1
    new_height = new_height if new_height % 2 == 0 else new_height - 1
    
    return (new_width, new_height)


def _resolve_output_dir(params: Dict, input_path: Path) -> Path:
    """Resolve output directory honoring custom path or nested option."""
    output_dir_param = params.get('output_dir', '').strip()
    use_nested_output = params.get('use_nested_output', False)
    nested_output_name = params.get('nested_output_name') or 'output'

    if output_dir_param:
        return Path(output_dir_param)
    if use_nested_output:
        return input_path.parent / nested_output_name
    return input_path.parent

class ConversionEngine(QThread):
    """Main conversion engine running in separate thread"""
    
    progress_updated = pyqtSignal(int)  # Progress percentage
    status_updated = pyqtSignal(str)    # Status message
    file_completed = pyqtSignal(str, str)  # (source, output) file paths
    conversion_finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, files: List[str], params: Dict):
        super().__init__()
        self.files = files
        self.params = params
        self.should_stop = False
        self.current_process = None

    def run_ffmpeg_with_cancellation(self, stream_spec, **kwargs):
        """Run FFmpeg with cancellation support"""
        # Force quiet mode unless debug is needed
        if 'quiet' not in kwargs:
            kwargs['quiet'] = True
            
        try:
            # Use run_async to get a handle to the process
            self.current_process = ffmpeg.run_async(stream_spec, **kwargs)
            
            stdout_data = None
            stderr_data = None
            
            # Use communicate with timeout to prevent pipe deadlocks while allowing cancellation
            while True:
                try:
                    # Wait for process to finish or timeout
                    # This reads pipes to prevent deadlock
                    stdout, stderr = self.current_process.communicate(timeout=0.5)
                    if stdout: stdout_data = stdout
                    if stderr: stderr_data = stderr
                    break
                except subprocess.TimeoutExpired:
                    # Process still running
                    if self.should_stop:
                        self.status_updated.emit("Stopping FFmpeg process...")
                        self.current_process.kill()
                        return False
                    # Continue loop
                
            # Check exit code
            if self.current_process.returncode != 0:
                # If we killed it, it's not an error
                if self.should_stop:
                    return False
                    
                error_msg = f"FFmpeg process exited with code {self.current_process.returncode}"
                if stderr_data:
                    error_msg += f"\nStderr: {stderr_data.decode('utf-8', errors='replace')}"
                raise Exception(error_msg)
                
            return True
        except Exception as e:
            if self.should_stop:
                return False
            raise e
        finally:
            self.current_process = None
        
    def run(self):
        """Main conversion thread execution"""
        print(f"Starting conversion with {len(self.files)} files")
        print(f"Conversion parameters: {self.params}")
        try:
            total_files = len(self.files)
            successful_conversions = 0
            
            # Calculate total operations for progress tracking
            total_operations = 0
            for file_path in self.files:
                file_ext = Path(file_path).suffix.lower()
                conversion_type = self.params.get('type', 'image')
                
                if conversion_type == 'image' and self.params.get('multiple_qualities', False):
                    quality_variants = self.params.get('quality_variants', [])
                    total_operations += len(quality_variants) if quality_variants else 1
                else:
                    total_operations += 1
            
            current_operation = 0
            
            for i, file_path in enumerate(self.files):
                if self.should_stop:
                    break
                    
                self.status_updated.emit(f"Processing: {os.path.basename(file_path)}")
                print(f"Processing file {i+1}/{total_files}: {file_path}")
                
                result = self.convert_file(file_path)
                
                if result is None:
                    # Skipped file
                    print(f"Skipped file: {file_path}")
                    # Don't increment successful_conversions
                elif result:
                    successful_conversions += 1
                    print(f"Successfully converted: {file_path}")
                else:
                    print(f"Failed to convert: {file_path}")
                    
                # Update progress based on operations completed
                file_ext = Path(file_path).suffix.lower()
                conversion_type = self.params.get('type', 'image')
                
                if conversion_type == 'image' and self.params.get('multiple_qualities', False):
                    quality_variants = self.params.get('quality_variants', [])
                    current_operation += len(quality_variants) if quality_variants else 1
                else:
                    current_operation += 1
                    
                progress = int(current_operation * 100 / total_operations)
                self.progress_updated.emit(progress)
                
            # Finish
            if self.should_stop:
                print("Conversion cancelled by user")
                self.conversion_finished.emit(False, "Conversion cancelled by user")
            else:
                # Calculate actual processed count (excluding skipped)
                # We don't have a separate counter for skipped, but successful_conversions tracks successes.
                # If we want to report "X/Y files processed successfully" where Y is only relevant files:
                # But the user asked: "If you converted 2 video files and skipped 5 photos, dont tell in teh popup converted 7 files, but say converted 2 files"
                # So we should just report successful_conversions.
                
                message = f"Conversion completed: {successful_conversions} files processed successfully"
                print(message)
                self.conversion_finished.emit(True, message)
                
        except Exception as e:
            error_msg = f"Error during conversion: {str(e)}"
            print(error_msg)
            self.conversion_finished.emit(False, error_msg)
            
    def convert_file(self, file_path: str) -> bool:
        """Convert a single file based on parameters"""
        try:
            file_ext = Path(file_path).suffix.lower()
            conversion_type = self.params.get('type', 'image')
            
            # Define valid extensions
            image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp', '.gif'}
            video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
            
            # Filter files based on conversion type
            if conversion_type == 'image':
                if file_ext not in image_exts:
                    self.status_updated.emit(f"Skipping non-image file: {os.path.basename(file_path)}")
                    return None  # Return None to indicate skipped
                return self.convert_image(file_path)
                
            elif conversion_type == 'video':
                if file_ext not in video_exts:
                    self.status_updated.emit(f"Skipping non-video file: {os.path.basename(file_path)}")
                    return None  # Return None to indicate skipped
                    
                video_variants = self.params.get('video_variants', [])
                quality_variants = self.params.get('quality_variants', [])
                
                # Check if we need multiple variants (either size or quality)
                has_multiple_variants = (video_variants and len(video_variants) > 1) or (quality_variants and len(quality_variants) > 1)
                
                if has_multiple_variants:
                    print(f"Creating multiple video variants for {file_path}")
                    return self._convert_video_multiple_variants(file_path)
                else:
                    # If single variant, set width/scale from video_variants[0] if available
                    if video_variants and len(video_variants) == 1:
                        v = video_variants[0]
                        if isinstance(v, str) and v.endswith('%'):
                            self.params['scale'] = True
                            self.params['width'] = v
                        else:
                            try:
                                self.params['width'] = int(v)
                                self.params['scale'] = True
                            except Exception:
                                self.params['width'] = 1920
                                self.params['scale'] = True
                    return self.convert_video(file_path)
            elif conversion_type == 'gif':
                if file_ext not in video_exts:
                    self.status_updated.emit(f"Skipping non-video file for GIF conversion: {os.path.basename(file_path)}")
                    return None  # Return None to indicate skipped
                    
                if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']:
                    return self.video_to_gif(file_path)
                else:
                    return self.optimize_gif(file_path)
            else:
                self.status_updated.emit(f"Unknown conversion type: {conversion_type}")
                return False
                
        except Exception as e:
            self.status_updated.emit(f"Error converting {os.path.basename(file_path)}: {str(e)}")
            return False
            
    def convert_image(self, file_path: str) -> bool:
        """Convert image using FFmpeg"""
        try:
            format_ext = self.params.get('format', 'jpg').lower()
            
            # Handle resize parameter if present but current_resize is not set
            if 'resize' in self.params and 'current_resize' not in self.params:
                self.params['current_resize'] = str(self.params['resize'])
            
            # Check if multiple qualities or resize variants are requested
            has_multiple_qualities = self.params.get('multiple_qualities', False) and self.params.get('quality_variants')
            has_resize_variants = self.params.get('resize_variants', [])
            
            if has_multiple_qualities or (has_resize_variants and len(has_resize_variants) > 1):
                return self._convert_image_multiple_variants(file_path, format_ext)
            else:
                # Single conversion
                output_path = self.get_output_path(file_path, format_ext)
                return self._convert_single_image(file_path, output_path, format_ext)
                
        except Exception as e:
            self.status_updated.emit(f"Image conversion error: {str(e)}")
            return False
            
    def _convert_image_multiple_variants(self, file_path: str, format_ext: str) -> bool:
        """Convert image with multiple quality and/or resize variants"""
        quality_variants = self.params.get('quality_variants')
        if quality_variants is None:
            quality_variants = [self.params.get('quality', 75)]
        
        resize_variants = self.params.get('resize_variants')
        if resize_variants is None:
            resize_variants = [None]
        
        successful_conversions = 0
        total_variants = len(quality_variants) * len(resize_variants)
        
        for quality in quality_variants:
            if self.should_stop:
                break
            for resize in resize_variants:
                if self.should_stop:
                    break
                try:
                    # Create output path with quality and/or resize suffix
                    output_path = self.get_output_path_with_variants(file_path, format_ext, quality, resize)
                    
                    # Temporarily set the parameters for this conversion
                    original_quality = self.params.get('quality')
                    original_resize = self.params.get('current_resize')
                    self.params['quality'] = quality
                    self.params['current_resize'] = resize
                    
                    # Convert with these parameters
                    success = self._convert_single_image(file_path, output_path, format_ext)
                    
                    if success:
                        successful_conversions += 1
                        variant_desc = f"Quality {quality}%"
                        if resize:
                            variant_desc += f", Resize {resize}"
                        self.status_updated.emit(f"✓ {variant_desc} completed")
                    else:
                        variant_desc = f"Quality {quality}%"
                        if resize:
                            variant_desc += f", Resize {resize}"
                        self.status_updated.emit(f"✗ {variant_desc} failed")
                    
                    # Restore original parameters
                    self.params['quality'] = original_quality
                    self.params['current_resize'] = original_resize
                    
                except Exception as e:
                    self.status_updated.emit(f"Variant conversion error: {str(e)}")
        
        if self.should_stop:
            self.status_updated.emit(f"Image variants conversion stopped by user")
        
        return successful_conversions > 0
        
    def _convert_single_image(self, file_path: str, output_path: str, format_ext: str) -> bool:
        """Convert a single image with current settings using FFmpeg"""
        return self._convert_image_ffmpeg(file_path, output_path)
            
    def _convert_image_ffmpeg(self, file_path: str, output_path: str) -> bool:
        """Convert image using FFmpeg"""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        input_stream = ffmpeg.input(file_path)
        
        # Apply filters
        stream = input_stream
        
        # Handle resize based on current_resize parameter
        current_resize = self.params.get('current_resize')
        if current_resize:
            if current_resize.endswith('%'):
                # Percentage resize
                percent = float(current_resize[:-1]) / 100
                orig_w, orig_h = get_image_dimensions(file_path)
                if orig_w > 0:
                    target_w = int(orig_w * percent)
                    target_w = clamp_resize_width(orig_w, target_w)
                    target_h = int((target_w * orig_h) / orig_w) if orig_h else -1
                    stream = ffmpeg.filter(stream, 'scale', target_w, target_h)
                else:
                    stream = ffmpeg.filter(stream, 'scale', f'iw*{percent}', f'ih*{percent}')
            elif current_resize.startswith('L'):
                # Longer edge resize (no upscaling)
                target_longer_edge = int(current_resize[1:])
                orig_w, orig_h = get_image_dimensions(file_path)
                longer_edge = max(orig_w, orig_h)
                # Don't upscale if longer edge is already smaller than target
                if longer_edge >= target_longer_edge:
                    if orig_w > orig_h:
                        # Width is longer: scale by width
                        stream = ffmpeg.filter(stream, 'scale', target_longer_edge, -1)
                    else:
                        # Height is longer: calculate width to maintain aspect ratio
                        ratio = target_longer_edge / orig_h
                        new_w = int(orig_w * ratio)
                        # Ensure even dimensions for codec compatibility
                        new_w = new_w if new_w % 2 == 0 else new_w - 1
                        stream = ffmpeg.filter(stream, 'scale', new_w, target_longer_edge)
            else:
                # Pixel resize (width-based, maintain aspect ratio)
                width = int(current_resize)
                orig_w, orig_h = get_image_dimensions(file_path)
                width = clamp_resize_width(orig_w, width)
                stream = ffmpeg.filter(stream, 'scale', width, -1)
        elif self.params.get('resize', False):
            # Legacy resize mode - use width only, maintain aspect ratio
            width = self.params.get('width', 1920)
            orig_w, orig_h = get_image_dimensions(file_path)
            width = clamp_resize_width(orig_w, int(width)) if width is not None else width
            stream = ffmpeg.filter(stream, 'scale', width, -1)
            
        # Handle rotation (skip rotation when using longer edge resize unless explicitly toggled)
        rotation_angle = self.params.get('rotation_angle')
        # Skip rotation for longer edge mode UNLESS rotation is explicitly set to a real rotation value
        skip_rotation_for_longer_edge = (
            current_resize and 
            current_resize.startswith('L') and 
            (not rotation_angle or rotation_angle == "No rotation")
        )
        if rotation_angle and rotation_angle != "No rotation" and not skip_rotation_for_longer_edge:
            if rotation_angle == "90° clockwise":
                stream = ffmpeg.filter(stream, 'transpose', 1)  # 90 degrees clockwise
            elif rotation_angle == "180°":
                stream = ffmpeg.filter(stream, 'transpose', 2)  # 180 degrees
                stream = ffmpeg.filter(stream, 'transpose', 2)  # Apply twice for 180
            elif rotation_angle == "270° clockwise":
                stream = ffmpeg.filter(stream, 'transpose', 2)  # 270 degrees clockwise (or 90 counter-clockwise)
            
        # Output with quality settings
        output_args = {}
        format_type = self.params.get('format', 'jpg').lower()
        
        if format_type in ['jpg', 'jpeg']:
            quality = self.params.get('quality', 85)
            # FFmpeg q:v scale is 1-31 (lower is better), convert from 1-100 scale
            output_args['q:v'] = max(1, min(31, int((100 - quality) * 31 / 100)))
        elif format_type == 'png':
            quality = self.params.get('quality', 85)
            output_args['compression_level'] = min(9, max(0, (100 - quality) // 10))
        elif format_type == 'webp':
            quality = self.params.get('quality', 85)
            output_args['quality'] = quality
            
        output = ffmpeg.output(stream, output_path, **output_args)
        
        if self.params.get('overwrite', False):
            output = ffmpeg.overwrite_output(output)
            
        # Run with error capture
        try:
            # Use run_ffmpeg_with_cancellation instead of direct run
            self.run_ffmpeg_with_cancellation(output, overwrite_output=self.params.get('overwrite', False))
        except Exception as e:
            error_msg = str(e)
            raise Exception(f"FFmpeg conversion failed: {error_msg}")
            
        self.file_completed.emit(file_path, output_path)
        return True
        

            
    def convert_video(self, file_path: str) -> bool:
        """Convert video using FFmpeg"""
        try:
            # Determine output format based on codec
            format_map = {
                'H.264 (MP4)': 'mp4',
                'H.265 (MP4)': 'mp4', 
                'WebM (VP9, faster)': 'webm',
                'WebM (AV1, slower)': 'webm',
                'AV1 (MP4)': 'mp4'
            }
            
            selected_codec = self.params.get('codec', 'H.264 (MP4)')
            output_format = format_map.get(selected_codec, 'mp4')
            
            # Debug: Print the command being executed
            self.status_updated.emit(f"DEBUG: Video conversion - Codec: {selected_codec}, Output format: {output_format}")
            
            output_path = self.get_output_path(file_path, output_format)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Handle time cutting - apply to input for better performance and compatibility
            input_args = {}
            enable_time_cutting = self.params.get('enable_time_cutting', False)
            if enable_time_cutting:
                time_start = self.params.get('time_start')
                time_end = self.params.get('time_end')
                if time_start is not None and time_end is not None and time_start < time_end:
                    # Get video duration to convert normalized time to actual time
                    video_duration = get_video_duration(file_path)
                    if video_duration > 0:
                        start_time = time_start * video_duration
                        end_time = time_end * video_duration
                        self.status_updated.emit(f"DEBUG: Applying time cutting - start: {start_time:.2f}s, end: {end_time:.2f}s (duration: {video_duration:.2f}s)")
                        input_args['ss'] = start_time
                        input_args['to'] = end_time
                    else:
                        self.status_updated.emit("DEBUG: Could not determine video duration for time cutting")
            
            input_stream = ffmpeg.input(file_path, **input_args)
            video_stream = input_stream.video
            
            # Check if video has audio stream before creating reference
            has_audio = has_audio_stream(file_path)
            audio_stream = input_stream.audio if has_audio else None

            # Apply retime (speed change) after cutting and before other filters
            retime_enabled = self.params.get('retime_enabled') or self.params.get('enable_retime')
            retime_speed = self.params.get('retime_speed', 1.0)
            if retime_enabled and retime_speed and retime_speed != 1.0:
                try:
                    speed = float(retime_speed)
                    speed = max(0.1, min(3.0, speed))
                    self.status_updated.emit(f"DEBUG: Applying retime at {speed:.2f}x (setpts/atempo)")
                    video_stream = video_stream.filter('setpts', f'PTS/{speed}')
                    if audio_stream is not None:
                        try:
                            if speed <= 2.0:
                                audio_stream = audio_stream.filter('atempo', speed)
                            else:
                                # Chain atempo to stay within valid range per filter
                                audio_stream = audio_stream.filter('atempo', 2.0).filter('atempo', speed / 2.0)
                        except Exception as audio_err:
                            self.status_updated.emit(f"DEBUG: Skipping audio retime due to error: {audio_err}")
                            audio_stream = None
                    else:
                        self.status_updated.emit("DEBUG: No audio stream detected for retime")
                except Exception as e:
                    self.status_updated.emit(f"DEBUG: Skipping retime due to error: {e}")
            else:
                video_stream = video_stream
            
            # Video encoding options
            codec_map = {
                'H.264 (MP4)': 'libx264',
                'H.265 (MP4)': 'libx265', 
                'WebM (VP9, faster)': 'libvpx-vp9',
                'WebM (AV1, slower)': 'libaom-av1',
                'AV1 (MP4)': 'libaom-av1'
            }
            
            codec = codec_map.get(selected_codec, 'libx264')
            
            # Debug: Print FFmpeg codec being used
            self.status_updated.emit(f"DEBUG: FFmpeg codec: {codec}")
            
            output_args = {'vcodec': codec}
            
            # Get quality parameter
            quality = self.params.get('quality')
            
            # For WebM/VP9/AV1, we need to handle audio codec and format-specific parameters
            if selected_codec in ['WebM (VP9, faster)', 'WebM (AV1, slower)']:
                # WebM uses VP9/AV1 video codec and Opus audio codec
                output_args['acodec'] = 'libopus'  # Use Opus audio codec for WebM
                output_args['f'] = 'webm'          # WebM container format
                
                # Apply CRF quality for VP9/WebM single video conversion
                if quality is not None:
                    crf_value = map_ui_quality_to_crf(quality, codec)
                    output_args['crf'] = crf_value
                    self.status_updated.emit(f"DEBUG: WebM CRF set to {crf_value} (quality: {quality})")
                
                # Optimize AV1 speed
                if codec == 'libaom-av1':
                    output_args['cpu-used'] = 4
                    self.status_updated.emit("DEBUG: Applied AV1 speed optimization (cpu-used=4)")
            else:
                # For MP4 codecs, ensure MP4 format
                output_args['f'] = 'mp4'
                
                # Optimize AV1 speed for MP4 container too
                if codec == 'libaom-av1':
                    output_args['cpu-used'] = 4
                    self.status_updated.emit("DEBUG: Applied AV1 speed optimization (cpu-used=4)")
                
                # Apply CRF quality for MP4 codecs if quality is specified
                if quality is not None:
                    crf_value = map_ui_quality_to_crf(quality, codec)
                    output_args['crf'] = crf_value
                    self.status_updated.emit(f"DEBUG: MP4 CRF set to {crf_value} (quality: {quality})")
                
            # Frame rate (always use original as per user request)
            # fps = self.params.get('fps', 'Keep Original')
            # if fps != 'Keep Original':
            #     output_args['r'] = fps
                
            # Scaling
            if self.params.get('scale', False):
                width = self.params.get('width', None)
                if width is not None:
                    self.status_updated.emit(f"DEBUG: Applying video scaling - width: {width}")
                    if isinstance(width, str) and width.endswith('%'):
                        percent = float(width[:-1]) / 100.0
                        original_width, original_height = get_video_dimensions(file_path)
                        target_w = int(original_width * percent) if original_width else None
                        if target_w:
                            target_w = clamp_resize_width(original_width, target_w)
                            target_h = int((target_w * original_height) / original_width) if original_height else -1
                            video_stream = ffmpeg.filter(video_stream, 'scale', target_w, target_h)
                        else:
                            scale_w = f'trunc(iw*{percent}/2)*2'
                            scale_h = f'trunc(ih*{percent}/2)*2'
                            video_stream = ffmpeg.filter(video_stream, 'scale', scale_w, scale_h)
                        self.status_updated.emit(f"DEBUG: Applied percentage scaling: {percent*100}%")
                    else:
                        new_width = int(width)
                        original_width, _ = get_video_dimensions(file_path)
                        new_width = clamp_resize_width(original_width, new_width)
                        video_stream = ffmpeg.filter(video_stream, 'scale', new_width, -1)
                        self.status_updated.emit(f"DEBUG: Applied width scaling: {new_width}px")
                else:
                    self.status_updated.emit("DEBUG: Scale enabled but no width parameter found")
                
            # Handle rotation (skip rotation when using longer edge resize unless explicitly toggled)
            current_resize = self.params.get('current_resize')
            rotation_angle = self.params.get('rotation_angle')
            # Skip rotation for longer edge mode UNLESS rotation is explicitly set to a real rotation value
            skip_rotation_for_longer_edge = (
                current_resize and 
                current_resize.startswith('L') and 
                (not rotation_angle or rotation_angle == "No rotation")
            )
            if rotation_angle and rotation_angle != "No rotation" and not skip_rotation_for_longer_edge:
                if rotation_angle == "90° clockwise":
                    video_stream = ffmpeg.filter(video_stream, 'transpose', 1)  # 90 degrees clockwise
                elif rotation_angle == "180°":
                    video_stream = ffmpeg.filter(video_stream, 'transpose', 2)  # 180 degrees
                    video_stream = ffmpeg.filter(video_stream, 'transpose', 2)  # Apply twice for 180
                elif rotation_angle == "270° clockwise":
                    video_stream = ffmpeg.filter(video_stream, 'transpose', 2)  # 270 degrees clockwise
            
            if audio_stream is not None:
                output = ffmpeg.output(video_stream, audio_stream, output_path, **output_args)
            else:
                output = ffmpeg.output(video_stream, output_path, **output_args)
            
            if self.params.get('overwrite', False):
                output = ffmpeg.overwrite_output(output)
                
            # Check for cancellation before starting
            if self.should_stop:
                return False
                
            # Use run_ffmpeg_with_cancellation
            self.run_ffmpeg_with_cancellation(output)
            
            self.file_completed.emit(file_path, output_path)
            return True
            
        except Exception as e:
            error_msg = f"FFmpeg error: {str(e)}"
            if hasattr(e, 'stderr') and e.stderr:
                stderr_output = e.stderr.decode('utf-8', errors='ignore')
                error_msg += f" (stderr: {stderr_output})"
            self.status_updated.emit(error_msg)
            return False
        except Exception as e:
            self.status_updated.emit(f"Video conversion error: {e}")
            return False
            
    def video_to_gif(self, file_path: str) -> bool:
        """Convert video to GIF using FFmpeg"""
        try:
            self.status_updated.emit(f"Converting video to GIF: {os.path.basename(file_path)}")
            
            # Check if GIF variants are requested
            gif_variants = self.params.get('gif_variants', {})
            gif_resize_values = self.params.get('gif_resize_values', [])
            self.status_updated.emit(f"DEBUG: Video-to-GIF variants check - gif_variants: {gif_variants}, gif_resize_values: {gif_resize_values}")
            
            # Check if any variant list has actual values (not empty lists)
            has_variants = False
            if gif_variants:
                for key, value_list in gif_variants.items():
                    if value_list and len(value_list) > 0:
                        has_variants = True
                        break
            
            # Also check for resize variants
            if not has_variants and gif_resize_values and len(gif_resize_values) > 1:
                has_variants = True
                self.status_updated.emit("DEBUG: Multiple resize variants detected")
            
            if has_variants:
                self.status_updated.emit("Using GIF multiple variants conversion for video")
                return self._convert_video_to_gif_multiple_variants(file_path)
            else:
                # Single video-to-GIF conversion
                self.status_updated.emit("Using single video-to-GIF conversion")
                return self._convert_single_video_to_gif(file_path)
            
        except Exception as e:
            self.status_updated.emit(f"Video to GIF conversion error: {e}")
            return False
    
    def _convert_video_to_gif_ffmpeg_only(self, file_path: str, output_path: str) -> bool:
        """Convert video to GIF using advanced FFmpeg filters (palettegen/paletteuse)"""
        self.status_updated.emit(f"Converting to GIF using FFmpeg engine: {os.path.basename(file_path)}")
        
        try:
            # Input args
            input_args = {}
            
            # Time cutting
            enable_time_cutting = self.params.get('enable_time_cutting', False)
            if enable_time_cutting:
                time_start = self.params.get('time_start')
                time_end = self.params.get('time_end')
                if time_start is not None and time_end is not None and time_start < time_end:
                    video_duration = get_video_duration(file_path)
                    if video_duration > 0:
                        start_time = time_start * video_duration
                        end_time = time_end * video_duration
                        self.status_updated.emit(f"DEBUG: Applying time cutting - start: {start_time:.2f}s, end: {end_time:.2f}s")
                        input_args['ss'] = start_time
                        input_args['to'] = end_time
            
            input_stream = ffmpeg.input(file_path, **input_args)
            
            # Retime
            retime_enabled = self.params.get('retime_enabled') or self.params.get('enable_retime')
            retime_speed = self.params.get('retime_speed', 1.0)
            if retime_enabled and retime_speed and retime_speed != 1.0:
                try:
                    speed = float(retime_speed)
                    speed = max(0.1, min(3.0, speed))
                    self.status_updated.emit(f"DEBUG: Applying retime at {speed:.2f}x")
                    input_stream = ffmpeg.filter(input_stream, 'setpts', f'PTS/{speed}')
                except Exception:
                    pass
            
            # FPS
            fps = self.params.get('ffmpeg_fps', 15)
            input_stream = ffmpeg.filter(input_stream, 'fps', fps=fps)
            
            # Resize
            original_width, original_height = get_video_dimensions(file_path)
            resize_mode = self.params.get('gif_resize_mode', 'No resize')
            resize_values = self.params.get('gif_resize_values', [])
            
            # Check if resize_values contains "L" prefix (longer edge format)
            has_longer_edge_prefix = resize_values and isinstance(resize_values[0], str) and resize_values[0].startswith('L')
            
            if (resize_mode != 'No resize' or has_longer_edge_prefix) and resize_values:
                resize_value = resize_values[0]
                # Check for "L" prefix first (longer edge format)
                if isinstance(resize_value, str) and resize_value.startswith('L'):
                    # Handle "L" prefix format for longer edge
                    target_longer_edge = int(resize_value[1:])
                    longer_edge = max(original_width, original_height)
                    # Don't upscale if longer edge is already smaller than target
                    if longer_edge >= target_longer_edge:
                        if original_width > original_height:
                            # Width is longer: scale by width
                            input_stream = ffmpeg.filter(input_stream, 'scale', str(target_longer_edge), '-2')
                        else:
                            # Height is longer: calculate width to maintain aspect ratio
                            ratio = target_longer_edge / original_height
                            new_w = int(original_width * ratio)
                            # Ensure even dimensions
                            new_w = new_w if new_w % 2 == 0 else new_w - 1
                            input_stream = ffmpeg.filter(input_stream, 'scale', str(new_w), str(target_longer_edge))
                elif resize_mode == 'By ratio (percent)':
                    if resize_value.endswith('%'):
                        percent = float(resize_value[:-1]) / 100.0
                        new_width = int(original_width * percent)
                        new_width = clamp_resize_width(original_width, new_width)
                        input_stream = ffmpeg.filter(input_stream, 'scale', str(new_width), '-2')
                elif resize_mode == 'By width (pixels)':
                    new_width = int(resize_value)
                    new_width = clamp_resize_width(original_width, new_width)
                    input_stream = ffmpeg.filter(input_stream, 'scale', str(new_width), '-2')
                elif resize_mode == 'By longer edge (pixels)':
                    # Handle mode name format for longer edge
                    # Check if resize_value has 'L' prefix and strip it
                    if isinstance(resize_value, str) and resize_value.startswith('L'):
                        target_longer_edge = int(resize_value[1:])
                    else:
                        target_longer_edge = int(resize_value)
                    longer_edge = max(original_width, original_height)
                    # Don't upscale if longer edge is already smaller than target
                    if longer_edge >= target_longer_edge:
                        if original_width > original_height:
                            # Width is longer: scale by width
                            input_stream = ffmpeg.filter(input_stream, 'scale', str(target_longer_edge), '-2')
                        else:
                            # Height is longer: calculate width to maintain aspect ratio
                            ratio = target_longer_edge / original_height
                            new_w = int(original_width * ratio)
                            # Ensure even dimensions
                            new_w = new_w if new_w % 2 == 0 else new_w - 1
                            input_stream = ffmpeg.filter(input_stream, 'scale', str(new_w), str(target_longer_edge))
            
            # Rotation (skip rotation when using longer edge resize unless explicitly toggled)
            rotation_angle = self.params.get('rotation')
            # Skip rotation for longer edge mode UNLESS rotation is explicitly set to a real rotation value
            skip_rotation_for_longer_edge = (
                resize_mode == 'By longer edge (pixels)' and 
                (not rotation_angle or rotation_angle == "No rotation")
            )
            if rotation_angle and rotation_angle != "No rotation" and not skip_rotation_for_longer_edge and rotation_angle == "90° clockwise":
                input_stream = ffmpeg.filter(input_stream, 'transpose', 1)
            elif rotation_angle and rotation_angle != "No rotation" and not skip_rotation_for_longer_edge and rotation_angle == "180°":
                input_stream = ffmpeg.filter(input_stream, 'transpose', 2)
                input_stream = ffmpeg.filter(input_stream, 'transpose', 2)
            elif rotation_angle and rotation_angle != "No rotation" and not skip_rotation_for_longer_edge and rotation_angle == "270° clockwise":
                input_stream = ffmpeg.filter(input_stream, 'transpose', 2)
                
            # Blur
            if self.params.get('ffmpeg_blur', False):
                # Use smartblur for subtle effect
                input_stream = ffmpeg.filter(input_stream, 'smartblur', lr='1.0', ls='-0.5', lt='-3.0')
            
            # Split stream for palette generation
            split = input_stream.split()
            
            # Palette generation
            colors = self.params.get('ffmpeg_colors', 256)
            palette = split[0].filter('palettegen', max_colors=colors)
            
            # Palette use
            dither = self.params.get('ffmpeg_dither', 'sierra2_4a')
            paletteuse_args = {}
            
            if dither.startswith('bayer:bayer_scale='):
                try:
                    # Extract scale value (e.g. "bayer:bayer_scale=2" -> 2)
                    scale = int(dither.split('=')[1])
                    paletteuse_args['dither'] = 'bayer'
                    paletteuse_args['bayer_scale'] = scale
                except:
                    paletteuse_args['dither'] = dither
            else:
                paletteuse_args['dither'] = dither
                
            final = ffmpeg.filter([split[1], palette], 'paletteuse', **paletteuse_args)
            
            # Output
            out = ffmpeg.output(final, output_path)
            if self.params.get('overwrite', False):
                out = ffmpeg.overwrite_output(out)
                
            self.run_ffmpeg_with_cancellation(out, overwrite_output=True)
            
            self.status_updated.emit(f"Successfully converted to GIF: {os.path.basename(output_path)}")
            self.file_completed.emit(file_path, output_path)
            return True
            
        except Exception as e:
            error_msg = f"FFmpeg error: {str(e)}"
            self.status_updated.emit(error_msg)
            return False
        except Exception as e:
            self.status_updated.emit(f"Error in FFmpeg GIF conversion: {str(e)}")
            return False

    def _convert_single_video_to_gif(self, file_path: str) -> bool:
        """Convert single video to GIF using FFmpeg"""
        # Set current_resize if gif_resize_values is provided
        gif_resize_values = self.params.get('gif_resize_values', [])
        if gif_resize_values and len(gif_resize_values) > 0:
            self.params['current_resize'] = gif_resize_values[0]
        
        output_path = self.get_output_path(file_path, 'gif')
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Always use FFmpeg-only mode
        return self._convert_video_to_gif_ffmpeg_only(file_path, output_path)

    
    def _convert_video_to_gif_multiple_variants(self, file_path: str) -> bool:
        """Convert video to GIF with multiple variants using FFmpeg"""
        try:
            gif_variants = self.params.get('gif_variants', {})
            gif_resize_values = self.params.get('gif_resize_values', [])
            
            # Get variant lists or default single values
            resize_variants = gif_resize_values if gif_resize_values else [None]
            fps_variants = gif_variants.get('fps', [None])
            colors_variants = gif_variants.get('colors', [None])
            dither_variants = gif_variants.get('dither', [None])
            
            # Filter out None values to ensure at least one iteration if lists are empty
            if not resize_variants: resize_variants = [None]
            if not fps_variants: fps_variants = [None]
            if not colors_variants: colors_variants = [None]
            if not dither_variants: dither_variants = [None]

            successful_conversions = 0
            total_combinations = len(resize_variants) * len(fps_variants) * len(colors_variants) * len(dither_variants)
            current_combination = 0
            
            self.status_updated.emit(f"Starting {total_combinations} video-to-GIF variant combinations")
            
            # Store original params to restore later
            original_params = self.params.copy()
            
            for resize in resize_variants:
                if self.should_stop: break
                for fps in fps_variants:
                    if self.should_stop: break
                    for colors in colors_variants:
                        if self.should_stop: break
                        for dither in dither_variants:
                            if self.should_stop: break
                            
                            current_combination += 1
                            
                            # Update params for this variant
                            if resize:
                                self.params['gif_resize_values'] = [resize]
                                if str(resize).endswith('%'):
                                    self.params['gif_resize_mode'] = 'By ratio (percent)'
                                else:
                                    self.params['gif_resize_mode'] = 'By width (pixels)'
                            
                            if fps:
                                self.params['ffmpeg_fps'] = int(fps)
                            
                            if colors:
                                self.params['ffmpeg_colors'] = int(colors)
                                
                            if dither:
                                self.params['ffmpeg_dither'] = dither
                                
                            # Generate output path
                            output_path = self.get_output_path(file_path, 'gif')
                            
                            variant_desc = f"resize={resize}, fps={fps}, colors={colors}, dither={dither}"
                            self.status_updated.emit(f"Processing variant {current_combination}/{total_combinations}: {variant_desc}")
                            
                            success = self._convert_video_to_gif_ffmpeg_only(file_path, output_path)
                            
                            if success:
                                successful_conversions += 1
                            
                            # Restore params for next iteration
                            self.params = original_params.copy()
            
            if self.should_stop:
                self.status_updated.emit(f"Video-to-GIF variants stopped by user: {successful_conversions}/{current_combination} completed")
            else:
                self.status_updated.emit(f"Video-to-GIF variants completed: {successful_conversions}/{total_combinations} successful")
            
            return successful_conversions > 0
            
        except Exception as e:
            self.status_updated.emit(f"Error in video-to-GIF multiple variants conversion: {str(e)}")
            return False
    
    def _convert_video_to_temp_gif(self, file_path: str, resize_variant: str = None, fps_variant: str = None) -> str:
        """Convert video to temporary GIF for variant processing"""
        try:
            temp_gif = tempfile.NamedTemporaryFile(suffix='.gif', delete=False).name
            
            # Ensure temp directory exists (should always exist, but safety check)
            os.makedirs(os.path.dirname(temp_gif), exist_ok=True)
            
            # Handle time cutting for GIF
            input_args = {}
            enable_time_cutting = self.params.get('enable_time_cutting', False)
            if enable_time_cutting:
                time_start = self.params.get('time_start')
                time_end = self.params.get('time_end')
                if time_start is not None and time_end is not None and time_start < time_end:
                    # Get video duration to convert normalized time to actual time
                    video_duration = get_video_duration(file_path)
                    if video_duration > 0:
                        start_time = time_start * video_duration
                        end_time = time_end * video_duration
                        self.status_updated.emit(f"DEBUG: Applying time cutting to temp GIF - start: {start_time:.2f}s, end: {end_time:.2f}s")
                        input_args['ss'] = start_time
                        input_args['to'] = end_time
                
            input_stream = ffmpeg.input(file_path, **input_args)

            # Apply retime (speed change) after cutting
            retime_enabled = self.params.get('retime_enabled') or self.params.get('enable_retime')
            retime_speed = self.params.get('retime_speed', 1.0)
            if retime_enabled and retime_speed and retime_speed != 1.0:
                try:
                    speed = float(retime_speed)
                    speed = max(0.1, min(3.0, speed))
                    self.status_updated.emit(f"DEBUG: Applying temp GIF retime at {speed:.2f}x (setpts)")
                    input_stream = ffmpeg.filter(input_stream, 'setpts', f'PTS/{speed}')
                except Exception as e:
                    self.status_updated.emit(f"DEBUG: Skipping temp GIF retime due to error: {e}")
            
            # Apply FPS from variant or default
            if fps_variant:
                fps = int(fps_variant)
            else:
                gif_fps = self.params.get('gif_fps', '15')
                fps = int(gif_fps) if gif_fps.isdigit() else 15
            
            # Apply size scaling if specified
            if resize_variant:
                if resize_variant.endswith('%'):
                    percent = float(resize_variant[:-1]) / 100
                    original_width, original_height = get_video_dimensions(file_path)
                    target_w = int(original_width * percent) if original_width else None
                    if target_w:
                        target_w = clamp_resize_width(original_width, target_w)
                        target_h = int((target_w * original_height) / original_width) if original_height else -2
                        input_stream = ffmpeg.filter(input_stream, 'scale', str(target_w), str(target_h))
                    else:
                        input_stream = ffmpeg.filter(input_stream, 'scale', f"trunc(iw*{percent}/2)*2", f"trunc(ih*{percent}/2)*2")
                elif resize_variant.startswith('L'):
                    # Longer edge resize (no upscaling)
                    target_longer_edge = int(resize_variant[1:])
                    original_width, original_height = get_video_dimensions(file_path)
                    longer_edge = max(original_width, original_height)
                    # Don't upscale if longer edge is already smaller than target
                    if longer_edge >= target_longer_edge:
                        if original_width > original_height:
                            # Width is longer: scale by width
                            input_stream = ffmpeg.filter(input_stream, 'scale', str(target_longer_edge), '-2')
                        else:
                            # Height is longer: calculate width to maintain aspect ratio
                            ratio = target_longer_edge / original_height
                            new_w = int(original_width * ratio)
                            # Ensure even dimensions
                            new_w = new_w if new_w % 2 == 0 else new_w - 1
                            input_stream = ffmpeg.filter(input_stream, 'scale', str(new_w), str(target_longer_edge))
                else:
                    width = int(resize_variant)
                    original_width, _ = get_video_dimensions(file_path)
                    width = clamp_resize_width(original_width, width)
                    input_stream = ffmpeg.filter(input_stream, 'scale', str(width), '-2')
            else:
                # Apply default scale from UI
                scale_option = self.params.get('gif_scale', 'Keep Original')
                if scale_option == '50%':
                    input_stream = ffmpeg.filter(input_stream, 'scale', 'iw/2', 'ih/2')
                elif scale_option == '25%':
                    input_stream = ffmpeg.filter(input_stream, 'scale', 'iw/4', 'ih/4')
            
            # Create GIF
            output = ffmpeg.output(input_stream, temp_gif, r=fps)
            # Check for cancellation
            if self.should_stop:
                return None
                
            # Use quiet mode to minimize console output
            ffmpeg.run(output, quiet=True, overwrite_output=True)
            
            return temp_gif
            
        except Exception as e:
            self.status_updated.emit(f"Error creating temp GIF: {e}")
            return None
            
    def optimize_gif(self, file_path: str) -> bool:
        """Optimize existing GIF using FFmpeg with variant support"""
        try:
            # Check if GIF variants are requested
            gif_variants = self.params.get('gif_variants', {})
            gif_resize_values = self.params.get('gif_resize_values', [])
            self.status_updated.emit(f"DEBUG: GIF variants check - gif_variants: {gif_variants}, gif_resize_values: {gif_resize_values}")
            
            # Check if any variant list has actual values (not empty lists)
            has_variants = False
            if gif_variants:
                for key, value_list in gif_variants.items():
                    if value_list and len(value_list) > 0:
                        has_variants = True
                        break
            
            # Also check for resize variants
            if not has_variants and gif_resize_values and len(gif_resize_values) > 1:
                has_variants = True
                self.status_updated.emit("DEBUG: Multiple resize variants detected for GIF optimization")
            
            self.status_updated.emit(f"DEBUG: Has valid variants: {has_variants}")
            
            if has_variants:
                self.status_updated.emit("Using GIF multiple variants conversion")
                return self._convert_gif_multiple_variants(file_path, 'gif')
            else:
                # Single GIF optimization
                self.status_updated.emit("Using single GIF optimization")
                output_path = self.get_output_path(file_path, 'gif')
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                return self._convert_video_to_gif_ffmpeg_only(file_path, output_path)
            
        except Exception as e:
            self.status_updated.emit(f"GIF optimization error: {e}")
            return False
            

            
    def get_output_path(self, input_path: str, new_extension: str) -> str:
        """Generate output file path"""
        path = Path(input_path)
        
        # Determine output directory (supports nested output)
        output_dir = _resolve_output_dir(self.params, path)
            
        # Generate new filename
        suffix = self.params.get('suffix', '_converted')
        
        # Check if multivariant is enabled - if so, don't append single parameter suffixes
        conversion_type = self.params.get('type', 'image')
        is_multivariant = self._is_multivariant_enabled(conversion_type)
        
        if not is_multivariant or conversion_type == 'gif':
            # Append parameter suffixes for single exports (and GIF variants)
            param_suffixes = self._build_parameter_suffixes(conversion_type, input_path)
            if param_suffixes:
                suffix = f"{suffix}_{'_'.join(param_suffixes)}"
        
        new_name = f"{path.stem}{suffix}.{new_extension}"
        
        output_path = output_dir / new_name
        
        # Handle file conflicts
        if not self.params.get('overwrite', False):
            counter = 1
            while output_path.exists():
                new_name = f"{path.stem}{suffix}_{counter}.{new_extension}"
                output_path = output_dir / new_name
                counter += 1
                
        return str(output_path)
        
    def _is_multivariant_enabled(self, conversion_type: str) -> bool:
        """Check if multivariant conversion is enabled for the given type"""
        if conversion_type == 'image':
            has_multiple_qualities = self.params.get('multiple_qualities', False) and self.params.get('quality_variants')
            has_resize_variants = self.params.get('resize_variants', [])
            return has_multiple_qualities or (has_resize_variants and len(has_resize_variants) > 1)
        elif conversion_type == 'video':
            video_variants = self.params.get('video_variants', [])
            return video_variants and len(video_variants) > 1
        elif conversion_type == 'gif':
            gif_variants = self.params.get('gif_variants', {})
            gif_resize_values = self.params.get('gif_resize_values', [])
            # Check if any variant list has actual values
            has_variants = False
            if gif_variants:
                for key, value_list in gif_variants.items():
                    if value_list and len(value_list) > 0:
                        has_variants = True
                        break
            return has_variants or (gif_resize_values and len(gif_resize_values) > 1)
        return False
        
    def _build_parameter_suffixes(self, conversion_type: str, input_path: str = None) -> list:
        """Build list of parameter suffixes for single exports"""
        suffixes = []
        
        if conversion_type == 'image':
            # Quality
            quality = self.params.get('quality')
            if quality is not None:
                suffixes.append(f"q{quality}")

            # Rotation
            rotation_angle = self.params.get('rotation_angle')
            if rotation_angle and rotation_angle != "No rotation":
                rotation_degrees = {
                    "90° clockwise": "90",
                    "180°": "180",
                    "270° clockwise": "270"
                }.get(rotation_angle, rotation_angle)
                suffixes.append(f"rot{rotation_degrees}")
            
            # Resize
            current_resize = self.params.get('current_resize')
            if current_resize:
                if current_resize.endswith('%'):
                    # Calculate actual output dimensions for percent resize
                    if input_path:
                        original_width, original_height = get_image_dimensions(input_path)
                        if original_width > 0 and original_height > 0:
                            percent = float(current_resize[:-1]) / 100
                            output_width = int(original_width * percent)
                            output_height = int(original_height * percent)
                            suffixes.append(f"size{output_width}x{output_height}")
                        else:
                            # Fallback to percent notation if dimensions can't be determined
                            suffixes.append(f"size{current_resize[:-1]}pc")
                    else:
                        # Fallback to percent notation if no input path
                        suffixes.append(f"size{current_resize[:-1]}pc")
                elif current_resize.startswith('L'):
                    # Longer edge resize (no upscaling) - MUST MATCH conversion logic
                    if input_path:
                        target_longer_edge = int(current_resize[1:])
                        orig_w, orig_h = get_image_dimensions(input_path)
                        if orig_w > 0 and orig_h > 0:
                            longer_edge = max(orig_w, orig_h)
                            # Don't upscale if longer edge is already smaller than target
                            if longer_edge >= target_longer_edge:
                                if orig_w > orig_h:
                                    # Width is longer: scale by width (matches conversion line 811)
                                    new_w = target_longer_edge
                                    new_w = new_w if new_w % 2 == 0 else new_w - 1
                                    # Calculate height maintaining aspect ratio (FFmpeg does this with -1)
                                    new_h = int((new_w * orig_h) / orig_w)
                                    new_h = new_h if new_h % 2 == 0 else new_h - 1
                                else:
                                    # Height is longer: calculate width (matches conversion line 814-816)
                                    ratio = target_longer_edge / orig_h
                                    new_w = int(orig_w * ratio)
                                    new_w = new_w if new_w % 2 == 0 else new_w - 1
                                    new_h = target_longer_edge
                                    new_h = new_h if new_h % 2 == 0 else new_h - 1
                                print(f"DEBUG SUFFIX: Portrait image - orig={orig_w}x{orig_h}, target={target_longer_edge}, calculated={new_w}x{new_h}")
                                suffixes.append(f"size{new_w}x{new_h}")
                            else:
                                # No resize needed (no upscaling)
                                suffixes.append(f"size{orig_w}x{orig_h}")
                        else:
                            # Fallback to longer edge notation if dimensions can't be determined
                            suffixes.append(f"sizeLonger{current_resize[1:]}")
                    else:
                        # Fallback to longer edge notation if no input path
                        suffixes.append(f"sizeLonger{current_resize[1:]}")
                else:
                    # Calculate actual output dimensions for pixel width resize (maintain aspect ratio)
                    if input_path:
                        original_width, original_height = get_image_dimensions(input_path)
                        if original_width > 0 and original_height > 0:
                            target_width = int(current_resize)
                            # Calculate height maintaining aspect ratio
                            output_height = int((target_width * original_height) / original_width)
                            suffixes.append(f"size{target_width}x{output_height}")
                        else:
                            # Fallback to width notation if dimensions can't be determined
                            suffixes.append(f"size{current_resize}")
                    else:
                        # Fallback to width notation if no input path
                        suffixes.append(f"size{current_resize}")
                    
        elif conversion_type == 'video':
            # Codec suffix for WebM to distinguish VP9 vs AV1
            codec = self.params.get('codec', '')
            if 'VP9' in codec:
                suffixes.append("vp9")
            elif 'AV1' in codec and 'WebM' in codec:
                suffixes.append("av1")

            # Quality suffix for single video exports
            quality = self.params.get('quality')
            if quality is not None:
                suffixes.append(f"quality{quality}")
                
            # Rotation
            rotation_angle = self.params.get('rotation_angle')
            if rotation_angle and rotation_angle != "No rotation":
                # Map rotation angles to degrees for suffix
                rotation_degrees = {
                    "90° clockwise": "90",
                    "180°": "180", 
                    "270° clockwise": "270"
                }.get(rotation_angle, rotation_angle)
                suffixes.append(f"rot{rotation_degrees}")
            
            # Time cutting
            enable_time_cutting = self.params.get('enable_time_cutting', False)
            if enable_time_cutting:
                time_start = self.params.get('time_start')
                time_end = self.params.get('time_end')
                if time_start is not None and time_end is not None and time_start < time_end:
                    start_pct = int(time_start * 100)
                    end_pct = int(time_end * 100)
                    suffixes.append(f"time{start_pct}-{end_pct}")
            
            # Retime (speed change)
            retime_enabled = self.params.get('retime_enabled') or self.params.get('enable_retime')
            retime_speed = self.params.get('retime_speed', 1.0)
            if retime_enabled and retime_speed and retime_speed != 1.0:
                speed = float(retime_speed)
                # Format speed: whole numbers as integer (2.0 -> x2speed), decimals keep dot (2.5 -> x2.5speed)
                if speed == int(speed):
                    speed_str = str(int(speed))
                else:
                    speed_str = str(speed)
                suffixes.append(f"x{speed_str}speed")
                
            # FPS (commented out - using original framerate)
            # fps = self.params.get('fps', 'Keep Original')
            # if fps != 'Keep Original':
            #     suffixes.append(f"fps{fps}")
                
            # Scale/Width
            if self.params.get('scale', False):
                width = self.params.get('width')
                if width:
                    if isinstance(width, str) and width.endswith('%'):
                        # Calculate actual output dimensions for percent resize
                        if input_path:
                            original_width, original_height = get_video_dimensions(input_path)
                            if original_width > 0 and original_height > 0:
                                percent = float(width[:-1]) / 100
                                output_width = int(original_width * percent)
                                output_height = int(original_height * percent)
                                suffixes.append(f"size{output_width}x{output_height}")
                            else:
                                # Fallback to percent notation if dimensions can't be determined
                                percent_val = width[:-1].replace('.', '_')
                                suffixes.append(f"size{percent_val}p")
                        else:
                            # Fallback to percent notation if no input path
                            percent_val = width[:-1].replace('.', '_')
                            suffixes.append(f"size{percent_val}p")
                    else:
                        # Calculate actual output dimensions for pixel width resize (maintain aspect ratio)
                        if input_path:
                            original_width, original_height = get_video_dimensions(input_path)
                            if original_width > 0 and original_height > 0:
                                target_width = int(width)
                                # Calculate height maintaining aspect ratio
                                output_height = int((target_width * original_height) / original_width)
                                suffixes.append(f"size{target_width}x{output_height}")
                            else:
                                # Fallback to width notation if dimensions can't be determined
                                suffixes.append(f"size{width}w")
                        else:
                            # Fallback to width notation if no input path
                            suffixes.append(f"size{width}w")
                        
        elif conversion_type == 'gif':
            # FFmpeg mode (Standard now)
            fps = self.params.get('ffmpeg_fps')
            if fps:
                suffixes.append(f"fps{fps}")
            
            colors = self.params.get('ffmpeg_colors')
            if colors:
                suffixes.append(f"colors{colors}")
            
            dither = self.params.get('ffmpeg_dither')
            if dither:
                # Map dither settings to quality suffixes
                dither_map = {
                    "none": "quality0Lowest",
                    "bayer:bayer_scale=5": "quality1Low",
                    "bayer:bayer_scale=4": "quality2Medium",
                    "bayer:bayer_scale=3": "quality3High",
                    "bayer:bayer_scale=1": "quality4Higher",
                    "floyd_steinberg": "quality5Best"
                }
                
                # Check exact match first
                if dither in dither_map:
                    suffixes.append(dither_map[dither])
                # Handle bayer with scale fallback
                elif 'bayer_scale=' in dither:
                    try:
                        # Extract scale value (e.g. from "bayer:bayer_scale=2")
                        scale = dither.split('bayer_scale=')[1].split(':')[0]
                        suffixes.append(f"bayer{scale}")
                    except:
                        suffixes.append("bayer")
                else:
                    # Simplify dither name for suffix (e.g. bayer:scale=1 -> bayer)
                    dither_short = dither.split(':')[0]
                    suffixes.append(f"{dither_short}")

            # Rotation
            gif_rotation = self.params.get('rotation')
            if gif_rotation and gif_rotation != "No rotation":
                rotation_degrees = {
                    "90° clockwise": "90",
                    "180°": "180",
                    "270° clockwise": "270"
                }.get(gif_rotation, gif_rotation)
                suffixes.append(f"rot{rotation_degrees}")
            
            # Time cutting
            enable_time_cutting = self.params.get('enable_time_cutting', False)
            if enable_time_cutting:
                time_start = self.params.get('time_start')
                time_end = self.params.get('time_end')
                if time_start is not None and time_end is not None and time_start < time_end:
                    start_pct = int(time_start * 100)
                    end_pct = int(time_end * 100)
                    suffixes.append(f"time{start_pct}-{end_pct}")
            
            # Retime (speed change)
            retime_enabled = self.params.get('retime_enabled') or self.params.get('enable_retime')
            retime_speed = self.params.get('retime_speed', 1.0)
            if retime_enabled and retime_speed and retime_speed != 1.0:
                speed = float(retime_speed)
                # Format speed: whole numbers as integer (2.0 -> x2speed), decimals keep dot (2.5 -> x2.5speed)
                if speed == int(speed):
                    speed_str = str(int(speed))
                else:
                    speed_str = str(speed)
                suffixes.append(f"x{speed_str}speed")
                
            # Resize (first value from resize values)
            gif_resize_values = self.params.get('gif_resize_values', [])
            if gif_resize_values:
                resize_value = gif_resize_values[0]
                if resize_value.endswith('%'):
                    # Calculate actual output dimensions for percent resize
                    if input_path:
                        # For GIFs, try to get dimensions (could be video or existing GIF)
                        if input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            original_width, original_height = get_video_dimensions(input_path)
                        else:
                            original_width, original_height = get_image_dimensions(input_path)
                        
                        if original_width > 0 and original_height > 0:
                            percent = float(resize_value[:-1]) / 100
                            output_width = int(original_width * percent)
                            output_height = int(original_height * percent)
                            suffixes.append(f"size{output_width}x{output_height}")
                        else:
                            # Fallback to percent notation if dimensions can't be determined
                            suffixes.append(f"size{resize_value[:-1]}pc")
                    else:
                        # Fallback to percent notation if no input path
                        suffixes.append(f"size{resize_value[:-1]}pc")
                elif resize_value.startswith('L'):
                    # Longer edge resize - same logic as images
                    if input_path:
                        # For GIFs from video, get video dimensions
                        if input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            orig_w, orig_h = get_video_dimensions(input_path)
                        else:
                            orig_w, orig_h = get_image_dimensions(input_path)
                        
                        if orig_w > 0 and orig_h > 0:
                            target_longer_edge = int(resize_value[1:])
                            longer_edge = max(orig_w, orig_h)
                            # Don't upscale if longer edge is already smaller than target
                            if longer_edge >= target_longer_edge:
                                if orig_w > orig_h:
                                    # Width is longer
                                    new_w = target_longer_edge
                                    new_w = new_w if new_w % 2 == 0 else new_w - 1
                                    new_h = int((new_w * orig_h) / orig_w)
                                    new_h = new_h if new_h % 2 == 0 else new_h - 1
                                else:
                                    # Height is longer
                                    ratio = target_longer_edge / orig_h
                                    new_w = int(orig_w * ratio)
                                    new_w = new_w if new_w % 2 == 0 else new_w - 1
                                    new_h = target_longer_edge
                                    new_h = new_h if new_h % 2 == 0 else new_h - 1
                                suffixes.append(f"size{new_w}x{new_h}")
                            else:
                                # No resize needed (no upscaling)
                                suffixes.append(f"size{orig_w}x{orig_h}")
                        else:
                            # Fallback to longer edge notation if dimensions can't be determined
                            suffixes.append(f"sizeLonger{resize_value[1:]}")
                    else:
                        # Fallback to longer edge notation if no input path
                        suffixes.append(f"sizeLonger{resize_value[1:]}")
                else:
                    # Calculate actual output dimensions for pixel width resize (maintain aspect ratio)
                    if input_path:
                        # For GIFs, try to get dimensions (could be video or existing GIF)
                        if input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            original_width, original_height = get_video_dimensions(input_path)
                        else:
                            original_width, original_height = get_image_dimensions(input_path)
                        
                        if original_width > 0 and original_height > 0:
                            target_width = int(resize_value)
                            # Calculate height maintaining aspect ratio
                            output_height = int((target_width * original_height) / original_width)
                            suffixes.append(f"size{target_width}x{output_height}")
                        else:
                            # Fallback to width notation if dimensions can't be determined
                            suffixes.append(f"size{resize_value}px")
                    else:
                        # Fallback to width notation if no input path
                        suffixes.append(f"size{resize_value}px")
        
        return suffixes
        
    def get_output_path_with_quality(self, input_path: str, new_extension: str, quality: int) -> str:
        """Generate output file path with quality suffix"""
        path = Path(input_path)
        
        # Determine output directory (supports nested output)
        output_dir = _resolve_output_dir(self.params, path)
            
        # Generate new filename with quality suffix
        base_suffix = self.params.get('suffix', '_converted')
        quality_suffix = f"{base_suffix}_quality{quality}"
        new_name = f"{path.stem}{quality_suffix}.{new_extension}"
        
        output_path = output_dir / new_name
        
        # Handle file conflicts
        if not self.params.get('overwrite', False):
            counter = 1
            while output_path.exists():
                new_name = f"{path.stem}{quality_suffix}_{counter}.{new_extension}"
                output_path = output_dir / new_name
                counter += 1
                
        return str(output_path)
    
    def get_output_path_with_variants(self, input_path: str, new_extension: str, quality: int = None, resize: str = None) -> str:
        """Generate output file path with quality and/or resize suffix"""
        path = Path(input_path)
        
        # Determine output directory (supports nested output)
        output_dir = _resolve_output_dir(self.params, path)
            
        # Generate new filename with variant suffixes
        base_suffix = self.params.get('suffix', '_converted')
        suffixes = []
        
        if quality is not None:
            suffixes.append(f"q{quality}")
        
        if resize is not None:
            if resize.endswith('%'):
                # Calculate actual output dimensions for percent resize
                original_width, original_height = get_image_dimensions(input_path)
                if original_width > 0 and original_height > 0:
                    percent = float(resize[:-1]) / 100
                    output_width = clamp_resize_width(original_width, int(original_width * percent))
                    output_height = int((output_width * original_height) / original_width)
                    suffixes.append(f"size{output_width}x{output_height}")
                else:
                    # Fallback to percent notation if dimensions can't be determined
                    suffixes.append(f"size{resize[:-1]}pc")
            elif resize.startswith('L'):
                # Longer edge resize (no upscaling) - MUST MATCH conversion logic
                target_longer_edge = int(resize[1:])
                orig_w, orig_h = get_image_dimensions(input_path)
                if orig_w > 0 and orig_h > 0:
                    longer_edge = max(orig_w, orig_h)
                    # Don't upscale if longer edge is already smaller than target
                    if longer_edge >= target_longer_edge:
                        if orig_w > orig_h:
                            # Width is longer: scale by width (matches conversion line 811)
                            new_w = target_longer_edge
                            new_w = new_w if new_w % 2 == 0 else new_w - 1
                            # Calculate height maintaining aspect ratio (FFmpeg does this with -1)
                            new_h = int((new_w * orig_h) / orig_w)
                            new_h = new_h if new_h % 2 == 0 else new_h - 1
                        else:
                            # Height is longer: calculate width (matches conversion line 814-816)
                            ratio = target_longer_edge / orig_h
                            new_w = int(orig_w * ratio)
                            new_w = new_w if new_w % 2 == 0 else new_w - 1
                            new_h = target_longer_edge
                            new_h = new_h if new_h % 2 == 0 else new_h - 1
                        suffixes.append(f"size{new_w}x{new_h}")
                    else:
                        # No resize needed (no upscaling)
                        suffixes.append(f"size{orig_w}x{orig_h}")
                else:
                    # Fallback to longer edge notation if dimensions can't be determined
                    suffixes.append(f"sizeLonger{resize[1:]}")
            else:
                # Calculate actual output dimensions for pixel width resize (maintain aspect ratio)
                original_width, original_height = get_image_dimensions(input_path)
                if original_width > 0 and original_height > 0:
                    target_width = clamp_resize_width(original_width, int(resize))
                    # Calculate height maintaining aspect ratio
                    output_height = int((target_width * original_height) / original_width)
                    suffixes.append(f"size{target_width}x{output_height}")
                else:
                    # Fallback to width notation if dimensions can't be determined
                    suffixes.append(f"size{resize}")
        
        if suffixes:
            variant_suffix = f"{base_suffix}_{'_'.join(suffixes)}"
        else:
            variant_suffix = base_suffix
            
        new_name = f"{path.stem}{variant_suffix}.{new_extension}"
        output_path = output_dir / new_name
        
        # Handle file conflicts
        if not self.params.get('overwrite', False):
            counter = 1
            while output_path.exists():
                conflict_name = f"{path.stem}{variant_suffix}_{counter}.{new_extension}"
                output_path = output_dir / conflict_name
                counter += 1
                
        return str(output_path)
    
    def _convert_gif_multiple_variants(self, file_path: str, format_ext: str) -> bool:
        """Convert GIF with multiple variants for size, fps, colors using FFmpeg"""
        gif_variants = self.params.get('gif_variants', {})
        gif_resize_values = self.params.get('gif_resize_values', [])
        self.status_updated.emit(f"Processing GIF variants: {gif_variants}, resize_values: {gif_resize_values}")
        
        # Get variant lists or default single values
        size_variants = gif_resize_values if gif_resize_values else [None]
        fps_variants = gif_variants.get('fps', [None])
        colors_variants = gif_variants.get('colors', [None])
        dither_variants = gif_variants.get('dither', [None])
        
        # Filter out None values to ensure at least one iteration if lists are empty
        if not size_variants: size_variants = [None]
        if not fps_variants: fps_variants = [None]
        if not colors_variants: colors_variants = [None]
        if not dither_variants: dither_variants = [None]
        
        successful_conversions = 0
        total_combinations = len(size_variants) * len(fps_variants) * len(colors_variants) * len(dither_variants)
        current_combination = 0
        
        self.status_updated.emit(f"Starting {total_combinations} GIF variant combinations")
        
        # Store original params
        original_params = self.params.copy()
        
        # Generate all combinations of variants
        for size in size_variants:
            if self.should_stop: break
            for fps in fps_variants:
                if self.should_stop: break
                for colors in colors_variants:
                    if self.should_stop: break
                    for dither in dither_variants:
                        if self.should_stop: break
                    
                        current_combination += 1
                        try:
                            # Update params for this variant
                            if size:
                                self.params['gif_resize_values'] = [size]
                                if str(size).endswith('%'):
                                    self.params['gif_resize_mode'] = 'By ratio (percent)'
                                else:
                                    self.params['gif_resize_mode'] = 'By width (pixels)'
                            
                            if fps:
                                self.params['ffmpeg_fps'] = int(fps)
                            
                            if colors:
                                self.params['ffmpeg_colors'] = int(colors)
                                
                            if dither:
                                self.params['ffmpeg_dither'] = dither

                            # Create output path with variant suffixes
                            output_path = self.get_output_path(file_path, format_ext)
                            
                            # Ensure output directory exists
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            
                            variant_desc = f"size={size}, fps={fps}, colors={colors}, dither={dither}"
                            self.status_updated.emit(f"Processing variant {current_combination}/{total_combinations}: {variant_desc}")
                            
                            # Convert with these parameters using FFmpeg
                            success = self._convert_video_to_gif_ffmpeg_only(file_path, output_path)
                            
                            if success:
                                successful_conversions += 1
                                self.file_completed.emit(file_path, output_path)
                                self.status_updated.emit(f"✓ GIF {variant_desc} completed")
                            else:
                                self.status_updated.emit(f"✗ GIF {variant_desc} failed")
                            
                            # Restore original parameters
                            self.params = original_params.copy()
                                    
                        except Exception as e:
                            self.status_updated.emit(f"GIF variant conversion error: {str(e)}")
        
        if self.should_stop:
            self.status_updated.emit(f"GIF variants conversion stopped by user: {successful_conversions}/{current_combination} completed")
        else:
            self.status_updated.emit(f"GIF variants completed: {successful_conversions}/{total_combinations} successful")
        
        return successful_conversions > 0


    
    def _convert_video_multiple_variants(self, file_path: str) -> bool:
        """Convert video with multiple size and quality variants"""
        try:
            video_variants = self.params.get('video_variants', [])
            quality_variants = self.params.get('quality_variants', [])
            
            # If no variants, fallback to single conversion
            if not video_variants and not quality_variants:
                return self.convert_video(file_path)
            
            # If only one type of variant, treat as single list
            if not video_variants:
                video_variants = [None]  # No size variants
            if not quality_variants:
                quality_variants = [None]  # No quality variants
            
            all_success = True
            total_combinations = len(video_variants) * len(quality_variants)
            current_combination = 0
            
            self.status_updated.emit(f"Creating {total_combinations} video variants")
            
            # Generate all combinations of size and quality variants
            for size_variant in video_variants:
                if self.should_stop:
                    break
                for quality_variant in quality_variants:
                    if self.should_stop:
                        break
                    current_combination += 1
                    
                    try:
                        # Determine output format based on codec
                        format_map = {
                            'H.264 (MP4)': 'mp4',
                            'H.265 (MP4)': 'mp4', 
                            'WebM (VP9, faster)': 'webm',
                            'WebM (AV1, slower)': 'webm',
                            'AV1 (MP4)': 'mp4'
                        }
                        selected_codec = self.params.get('codec', 'H.264 (MP4)')
                        output_format = format_map.get(selected_codec, 'mp4')
                        
                        # Generate output path with both size and quality variant suffixes
                        output_path = self.get_output_path_with_video_variants(file_path, output_format, size_variant, quality_variant)
                        
                        # Ensure output directory exists
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        if not self.params.get('overwrite', False) and os.path.exists(output_path):
                            self.status_updated.emit(f"Skipping existing file: {os.path.basename(output_path)}")
                            continue
                        
                        variant_desc = []
                        if size_variant:
                            variant_desc.append(f"Size: {size_variant}")
                        if quality_variant is not None:
                            variant_desc.append(f"Quality: {quality_variant}")
                        variant_info = ", ".join(variant_desc) if variant_desc else "default"
                        
                        self.status_updated.emit(f"Processing variant {current_combination}/{total_combinations}: {variant_info}")
                        
                        # Prepare video input
                        input_args = {}
                        
                        # Handle time cutting first (apply to input)
                        enable_time_cutting = self.params.get('enable_time_cutting', False)
                        if enable_time_cutting:
                            time_start = self.params.get('time_start', 0.0)
                            time_end = self.params.get('time_end', 1.0)
                            if time_start is not None and time_end is not None and time_start < time_end:
                                video_duration = get_video_duration(file_path)
                                if video_duration and video_duration > 0:
                                    start_time = time_start * video_duration
                                    end_time = time_end * video_duration
                                    input_args['ss'] = start_time
                                    input_args['to'] = end_time
                        
                        input_stream = ffmpeg.input(file_path, **input_args)
                        video_stream = input_stream.video
                        
                        # Check if video has audio stream before creating reference
                        has_audio = has_audio_stream(file_path)
                        audio_stream = input_stream.audio if has_audio else None
                        
                        # Apply retime (speed change) after cutting and before other filters
                        retime_enabled = self.params.get('retime_enabled') or self.params.get('enable_retime')
                        retime_speed = self.params.get('retime_speed', 1.0)
                        if retime_enabled and retime_speed and retime_speed != 1.0:
                            try:
                                speed = float(retime_speed)
                                speed = max(0.1, min(3.0, speed))
                                self.status_updated.emit(f"DEBUG: Applying retime at {speed:.2f}x to variant")
                                video_stream = video_stream.filter('setpts', f'PTS/{speed}')
                                if audio_stream is not None:
                                    try:
                                        if speed <= 2.0:
                                            audio_stream = audio_stream.filter('atempo', speed)
                                        else:
                                            # Chain atempo to stay within valid range
                                            audio_stream = audio_stream.filter('atempo', 2.0).filter('atempo', speed / 2.0)
                                    except Exception as audio_err:
                                        self.status_updated.emit(f"DEBUG: Skipping audio retime: {audio_err}")
                                        audio_stream = None
                            except Exception as e:
                                self.status_updated.emit(f"DEBUG: Skipping retime: {e}")
                        
                        # Video encoding options
                        codec_map = {
                            'H.264 (MP4)': 'libx264',
                            'H.265 (MP4)': 'libx265', 
                            'WebM (VP9, faster)': 'libvpx-vp9',
                            'WebM (AV1, slower)': 'libaom-av1',
                            'AV1 (MP4)': 'libaom-av1'
                        }
                        
                        codec = codec_map.get(selected_codec, 'libx264')
                        output_args = {'vcodec': codec}
                        
                        # For WebM/VP9/AV1, we need to handle audio codec and format-specific parameters
                        if selected_codec in ['WebM (VP9, faster)', 'WebM (AV1, slower)']:
                            # WebM uses VP9/AV1 video codec and Opus audio codec
                            output_args['acodec'] = 'libopus'  # Use Opus audio codec for WebM
                            output_args['f'] = 'webm'          # WebM container format
                            
                            # Apply CRF quality for VP9
                            if quality_variant is not None:
                                output_args['crf'] = map_ui_quality_to_crf(quality_variant, codec)
                            
                            # Optimize AV1 speed
                            if codec == 'libaom-av1':
                                output_args['cpu-used'] = 4
                        else:
                            # For MP4 codecs, ensure MP4 format
                            output_args['f'] = 'mp4'
                            
                            # Apply CRF quality for MP4 codecs
                            if quality_variant is not None:
                                output_args['crf'] = map_ui_quality_to_crf(quality_variant, codec)
                            
                            # Optimize AV1 speed for MP4 container too
                            if codec == 'libaom-av1':
                                output_args['cpu-used'] = 4
                                
                        # Frame rate (always use original as per user request)
                        # fps = self.params.get('fps', 'Keep Original')
                        # if fps != 'Keep Original':
                        #     output_args['r'] = fps
                        
                        # Apply video size variant
                        if size_variant:
                            if size_variant.endswith('%'):
                                # Percentage resize
                                percent = float(size_variant[:-1]) / 100
                                scale_w = f"trunc(iw*{percent}/2)*2"
                                scale_h = f"trunc(ih*{percent}/2)*2"
                                video_stream = ffmpeg.filter(video_stream, 'scale', scale_w, scale_h)
                            else:
                                # Width-based resize (maintain aspect ratio)
                                new_width = int(size_variant)
                                video_stream = ffmpeg.filter(video_stream, 'scale', str(new_width), '-2')  # -2 maintains aspect ratio and ensures even height
                        
                        # Combine video and audio streams for output
                        if audio_stream is not None:
                            output = ffmpeg.output(video_stream, audio_stream, output_path, **output_args)
                        else:
                            output = ffmpeg.output(video_stream, output_path, **output_args)
                        
                        if self.params.get('overwrite', False):
                            output = ffmpeg.overwrite_output(output)
                        
                        # Check for cancellation
                        if self.should_stop:
                            return False
                            
                        # Run video conversion with cancellation support
                        self.run_ffmpeg_with_cancellation(output)
                        
                        self.file_completed.emit(file_path, output_path)
                        self.status_updated.emit(f"✓ Video variant {variant_info} completed")
                        
                    except Exception as e:
                        # More detailed FFmpeg error reporting
                        error_msg = f"FFmpeg error with video variant {current_combination}: {str(e)}"
                        self.status_updated.emit(error_msg)
                        all_success = False
                        continue
                    except Exception as e:
                        self.status_updated.emit(f"Error with video variant {current_combination}: {str(e)}")
                        all_success = False
                        continue
            
            if self.should_stop:
                self.status_updated.emit(f"Video variants conversion stopped by user: {current_combination}/{total_combinations} completed")
            else:
                self.status_updated.emit(f"Video variants completed: {total_combinations} files created")
            
            return all_success
            
        except Exception as e:
            self.status_updated.emit(f"Error in video multiple variants conversion: {str(e)}")
            return False
    
    def get_output_path_with_video_variants(self, file_path: str, format_ext: str, size_variant: str = None, quality_variant: int = None) -> str:
        """Generate output path for video variant with size and quality suffixes"""
        path = Path(file_path)
        base_dir = _resolve_output_dir(self.params, path)
        base_name = path.stem
        suffix = self.params.get('suffix', '_converted')
        
        # Create variant suffixes
        variant_parts = []
        
        # Size variant suffix
        if size_variant:
            if size_variant.endswith('%'):
                # Calculate actual output dimensions for percent resize
                original_width, original_height = get_video_dimensions(file_path)
                if original_width > 0 and original_height > 0:
                    percent = float(size_variant[:-1]) / 100
                    output_width = int(original_width * percent)
                    output_height = int(original_height * percent)
                    variant_parts.append(f"{output_width}x{output_height}")
                else:
                    # Fallback to percent notation if dimensions can't be determined
                    percent_val = size_variant[:-1].replace('.', '_')
                    variant_parts.append(f"{percent_val}p")
            elif size_variant.startswith('L'):
                # Longer edge resize (no upscaling) - use same logic as conversion
                target_longer_edge = int(size_variant[1:])
                original_width, original_height = get_video_dimensions(file_path)
                if original_width > 0 and original_height > 0:
                    longer_edge = max(original_width, original_height)
                    # Don't upscale if longer edge is already smaller than target
                    if longer_edge >= target_longer_edge:
                        if original_width > original_height:
                            # Width is longer: scale by width
                            output_width = target_longer_edge
                            output_height = int((target_longer_edge * original_height) / original_width)
                        else:
                            # Height is longer: calculate width to maintain aspect ratio
                            ratio = target_longer_edge / original_height
                            output_width = int(original_width * ratio)
                            output_height = target_longer_edge
                        # Ensure even dimensions
                        output_width = output_width if output_width % 2 == 0 else output_width - 1
                        output_height = output_height if output_height % 2 == 0 else output_height - 1
                        variant_parts.append(f"{output_width}x{output_height}")
                    else:
                        # No resize needed (no upscaling)
                        variant_parts.append(f"{original_width}x{original_height}")
                else:
                    # Fallback to longer edge notation if dimensions can't be determined
                    variant_parts.append(f"L{target_longer_edge}")
            else:
                # Calculate actual output dimensions for pixel width resize (maintain aspect ratio)
                original_width, original_height = get_video_dimensions(file_path)
                if original_width > 0 and original_height > 0:
                    target_width = int(size_variant)
                    # Calculate height maintaining aspect ratio
                    output_height = int((target_width * original_height) / original_width)
                    variant_parts.append(f"{target_width}x{output_height}")
                else:
                    # Fallback to width notation if dimensions can't be determined
                    variant_parts.append(f"{size_variant}w")
        
        # Quality variant suffix
        if quality_variant is not None:
            variant_parts.append(f"quality{quality_variant}")
        
        # Combine variant parts
        if variant_parts:
            variant_suffix = "_" + "_".join(variant_parts)
        else:
            variant_suffix = ""
        
        filename = f"{base_name}{suffix}{variant_suffix}.{format_ext}"
        output_path = os.path.join(base_dir, filename)
        
        return output_path
        
    def stop_conversion(self):
        """Stop the conversion process"""
        self.should_stop = True


class ToolChecker:
    """Check if required tools are available"""
    
    @staticmethod
    def check_ffmpeg() -> bool:
        """Check if FFmpeg is available"""
        try:
            ffmpeg_path = get_bundled_tool_path('ffmpeg')
            kwargs = get_subprocess_kwargs()
            kwargs['timeout'] = 5
            result = subprocess.run([ffmpeg_path, '-version'], **kwargs)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
            
    @staticmethod
    def get_tool_status() -> Dict[str, bool]:
        """Get status of all tools"""
        return {
            'ffmpeg': ToolChecker.check_ffmpeg()
        }
        
    @staticmethod
    def get_detailed_status() -> Dict[str, str]:
        """Get detailed status information"""
        status = {}
        
        # Check FFmpeg
        try:
            ffmpeg_path = get_bundled_tool_path('ffmpeg')
            kwargs = get_subprocess_kwargs()
            kwargs['timeout'] = 5
            result = subprocess.run([ffmpeg_path, '-version'], **kwargs)
            if result.returncode == 0:
                # Extract version from first line
                first_line = result.stdout.split('\n')[0]
                status['ffmpeg'] = f"Available - {first_line}"
            else:
                status['ffmpeg'] = "Not working properly"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            status['ffmpeg'] = "Not found - Please install FFmpeg"
            
        # ImageMagick and Pillow not needed - using FFmpeg for everything
        status['imagemagick'] = "Not needed - Using FFmpeg for all image/video processing"
                
        return status


def verify_bundled_tools(timeout: int = 5) -> Dict[str, Dict[str, Optional[str]]]:
    """Run a quick verification of bundled tools by calling their version commands.

    Returns a mapping of tool -> {path, returncode, stdout, stderr}.
    This function intentionally does not raise on missing tools; it's a runtime probe helper.
    """
    tools = ['ffmpeg']
    results: Dict[str, Dict[str, Optional[str]]] = {}

    # load expected checksums from cache if available
    expected_checks = {}
    try:
        if os.path.isdir(_USER_BIN_CACHE):
            checks_path = os.path.join(_USER_BIN_CACHE, 'checksums.json')
            if os.path.exists(checks_path):
                try:
                    expected_checks = json.load(open(checks_path, 'r', encoding='utf-8'))
                except Exception:
                    expected_checks = {}
    except Exception:
        expected_checks = {}

    for t in tools:
        path = get_bundled_tool_path(t)
        cmd = [path, '-version'] if t == 'ffmpeg' else [path, '--version']
        try:
            kwargs = get_subprocess_kwargs()
            kwargs['timeout'] = timeout
            proc = subprocess.run(cmd, **kwargs)
            results[t] = {
                'path': path,
                'returncode': proc.returncode,
                'stdout': proc.stdout.strip() if proc.stdout else '',
                'stderr': proc.stderr.strip() if proc.stderr else ''
            }
            # compute checksum if file exists and is a real path (not bare name)
            try:
                if os.path.exists(path) and os.path.isfile(path):
                    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
                    results[t]['sha256'] = sha
                    exp = expected_checks.get(os.path.basename(path)) if isinstance(expected_checks, dict) else None
                    if exp:
                        results[t]['expected_sha256'] = exp
                        results[t]['checksum_match'] = (sha.lower() == str(exp).lower())
            except Exception:
                pass
        except FileNotFoundError:
            results[t] = {'path': path, 'returncode': None, 'stdout': None, 'stderr': 'not found'}
        except subprocess.TimeoutExpired:
            results[t] = {'path': path, 'returncode': None, 'stdout': None, 'stderr': 'timeout'}
        except Exception as e:
            results[t] = {'path': path, 'returncode': None, 'stdout': None, 'stderr': str(e)}

    return results

