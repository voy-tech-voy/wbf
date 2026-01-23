This is a complex logic flow because we are moving from simple FPS adjustment to geometric transformation.

Here is the high-level architecture instruction for your Coding Agent. It breaks down the logic into Analysis, User Intent (UI), Decision Matrix, and Execution.

📘 Master Instruction: The "Idiot-Proof" Social Converter

Objective:
Build a conversion engine that intelligently handles aspect ratio mismatches (e.g., Landscape source 
→
→
 Vertical output) based on user preference. It must combine this with the existing FPS logic and generate descriptive filenames.

1. The Analysis Phase (Data Gathering)

Before generating any command, the agent must extract three specific data points from the input file:

FPS: (Already implemented).

Width (px)

Height (px)

Derived Metric: Aspect Ratio = Width / Height.

If Ratio > 1: Landscape (Horizontal).

If Ratio < 1: Portrait (Vertical).

If Ratio == 1: Square.

2. The User Interface Controls (UI Toggles)

The Agent needs to expect these inputs from the frontend. These are mutually exclusive modes regarding geometry.

A. Toggle: "Auto-Rotate Landscape" (Boolean)

True: If input is 16:9 Landscape, rotate it 90 degrees to make it Vertical 9:16 (Uses full resolution).

False: Keep orientation as is (requires cropping or filling).

B. Dropdown: "Fill Method" (Enum)

(Only applies if Auto-Rotate is OFF or Video is Square)

Mode 1: CROP_CENTER – Zooms in to fill the screen. Cuts off sides. No black bars.

Mode 2: BLUR_BACKGROUND – Fits the full video in center. Fills empty space with a blurred copy of the video. (Trendy).

Mode 3: FIT_BLACK – Fits video in center. Adds black bars. (Traditional).

3. The Decision Matrix (The Brain)

The agent must apply logic in this order:

Step 1: Check Rotation

IF Auto-Rotate == True AND Input is Landscape (Width > Height):

Action: Apply transpose=1 (90° CW Rotation).

Suffix: _rot.

New State: Input is now treated as Vertical. Skip to FPS logic.

Step 2: Check Geometry (If not rotated)

IF Input is Landscape AND Target is Vertical (9:16):

Sub-Check: Fill Method

If CROP_CENTER: Scale height to 1920, Crop width to 1080. Suffix: _crop.

If BLUR_BACKGROUND: Complex Filter (Split stream 
→
→
 Background Scale+Blur 
→
→
 Foreground Scale 
→
→
 Overlay). Suffix: _blur.

If FIT_BLACK: Scale to fit within 1080x1920, pad with black. Suffix: _fit.

Step 3: Apply FPS Logic

(Logic from previous instruction: Downsample High FPS, Keep Cinematic, etc.)

4. Technical Implementation Specifications
The Suffix System

The output filename must be generated before FFmpeg runs:
[OriginalName]_[Platform]_[GeoMode]_[FPSMode].mp4

Example: myvacation_tiktok_blur_30fps.mp4

Example: gameplay_shorts_rot_60fps.mp4

FFmpeg Filter Construction Guide

The agent must construct the -vf string dynamically.

1. Rotation (Simple)

code
Bash
download
content_copy
expand_less
vf="transpose=1,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,..."

2. Crop Center (Zoom)

code
Bash
download
content_copy
expand_less
vf="scale=1920:1080:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,..."
# Note: We scale based on HEIGHT to ensure we fill the vertical space, then crop width.

3. Blur Background (The "Split" Trick)

code
Bash
download
content_copy
expand_less
vf="split[bg][fg]; \
 [bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg_blurred]; \
 [fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg_scaled]; \
 [bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2,..."
5. Python Logic Implementation

Here is the updated logic for the coding agent.

code
Python
download
content_copy
expand_less
import subprocess
import os

# --- ENUMS FOR UI ---
class FillMethod:
    CROP = "crop"
    BLUR = "blur"
    FIT = "fit"

def get_video_info(file_path):
    """
    Returns dict with fps, width, height.
    """
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,width,height",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    try:
        # Output format: width\nheight\nfps_fraction
        out = subprocess.check_output(cmd).decode("utf-8").strip().split('\n')
        
        # Parse Width/Height
        width = int(out[0])
        height = int(out[1])
        
        # Parse FPS
        fps_str = out[2]
        if '/' in fps_str:
            num, den = fps_str.split('/')
            fps = float(num) / float(den)
        else:
            fps = float(fps_str)
            
        return {"width": width, "height": height, "fps": fps}
    except Exception:
        return {"width": 1920, "height": 1080, "fps": 30.0} # Fallback

def build_filter_chain(info, allow_rotation, fill_method, fps_mode):
    """
    Constructs the complex filter string based on geometry + FPS.
    """
    filters = []
    w = info['width']
    h = info['height']
    is_landscape = w > h
    suffix_geo = ""
    
    # --- GEOMETRY LOGIC ---
    
    # 1. Rotation Check
    if allow_rotation and is_landscape:
        # Rotate 90 degrees CW
        filters.append("transpose=1") 
        # After rotation, dimensions swap mentally, so we treat it as filling the screen
        filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
        filters.append("crop=1080:1920")
        suffix_geo = "_rot"
    
    # 2. Geometry Transforms (If not rotating)
    else:
        if fill_method == FillMethod.CROP:
            # Scale so the Shortest side matches the Target
            filters.append("scale=1080:1920:force_original_aspect_ratio=increase")
            filters.append("crop=1080:1920")
            suffix_geo = "_crop"
            
        elif fill_method == FillMethod.FIT:
            # Scale to fit inside, pad with black
            filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
            filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black")
            suffix_geo = "_fit"
            
        elif fill_method == FillMethod.BLUR:
            # Complex filter chain handled separately due to syntax
            # We return a specific marker to handle this in the main function
            return "COMPLEX_BLUR", "_blur"

    # --- FPS LOGIC (Appended to the chain) ---
    # Note: FPS logic is added to the end of the geometry filters
    
    fps_filter = ""
    suffix_fps = ""
    
    if info['fps'] > 31:
        fps_filter = "tmix=frames=2:weights='1 1',fps=30"
        suffix_fps = "_30fps"
    elif info['fps'] < 29:
        # Cinematic - no change to FPS, just GOP adjust later
        suffix_fps = "_native"
    else:
        fps_filter = "fps=30"
        suffix_fps = "_30fps"

    if fps_filter:
        filters.append(fps_filter)

    # Always add color/detail polish at the end
    filters.append("unsharp=5:5:0.5:5:5:0.0")
    
    return ",".join(filters), suffix_geo + suffix_fps

def generate_ffmpeg_cmd(input_file, output_dir, platform_name="social", 
                        allow_rotation=False, fill_method=FillMethod.BLUR):
    
    info = get_video_info(input_file)
    
    # Determine Filters and Suffixes
    vf_chain, suffixes = build_filter_chain(info, allow_rotation, fill_method, info['fps'])
    
    # Determine Output Filename
    filename = os.path.basename(input_file)
    name_no_ext = os.path.splitext(filename)[0]
    final_output = os.path.join(output_dir, f"{name_no_ext}_{platform_name}{suffixes}.mp4")
    
    # GOP Calculation
    gop = int(info['fps'] * 2) if info['fps'] < 29 else 60

    cmd = ["ffmpeg", "-y", "-i", input_file]

    # Handle the "Blur" Scenario (Complex Filter)
    if vf_chain == "COMPLEX_BLUR":
        # We need a filter_complex graph instead of simple -vf
        # This graph:
        # 1. Splits input
        # 2. Bg: Scale to cover, Crop, Blur
        # 3. Fg: Scale to fit
        # 4. Overlay
        # 5. Apply FPS logic (if needed) and Unsharp
        
        fps_part = ",tmix=frames=2:weights='1 1',fps=30" if info['fps'] > 31 else (",fps=30" if info['fps'] >= 29 else "")
        
        filter_graph = (
            f"[0:v]split[bg][fg];"
            f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg_blur];"
            f"[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg_scaled];"
            f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2{fps_part},unsharp=5:5:0.5:5:5:0.0[outv]"
        )
        cmd.extend(["-filter_complex", filter_graph, "-map", "[outv]", "-map", "0:a?"])
    else:
        # Standard Simple Filter
        cmd.extend(["-vf", vf_chain])

    # Universal Encoding Settings
    cmd.extend([
        "-c:v", "libx264", "-preset", "veryslow", "-profile:v", "high", "-level:v", "4.2",
        "-g", str(gop), "-bf", "2", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709",
        "-b:v", "15M", "-maxrate", "20M", "-bufsize", "30M",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
        final_output
    ])
    
    return cmd

# --- EXAMPLE USAGE FOR AGENT ---
# cmd = generate_ffmpeg_cmd("landscape_vid.mp4", "./out", allow_rotation=False, fill_method=FillMethod.BLUR)
# subprocess.run(cmd)