import subprocess

def get_video_fps(file_path):
    """
    Returns the exact float FPS of the input video.
    """
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream=r_frame_rate", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    
    try:
        # Run command and get output (e.g., "30000/1001" or "24/1")
        output = subprocess.check_output(cmd).decode("utf-8").strip()
        
        # Parse fraction
        if '/' in output:
            num, den = output.split('/')
            return float(num) / float(den)
        else:
            return float(output)
            
    except Exception as e:
        print(f"Error detecting FPS: {e}")
        return 30.0 # Default fallback

# --- USAGE LOGIC ---

fps = get_video_fps("my_video.mp4")

# Logic to determine which FFmpeg command to use
if fps > 31:
    # SCENARIO A: High Framerate (Standardize to 30fps)
    # We must downsample to prevent Instagram's erratic server compression.
    mode = "DOWNSAMPLE"
    ffmpeg -i input_high_fps.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,tmix=frames=2:weights='1 1',fps=30,unsharp=5:5:0.5:5:5:0.0" -c:v libx264 -preset veryslow -profile:v high -level:v 4.2 -g 60 -bf 2 -pix_fmt yuv420p -colorspace bt709 -color_trc bt709 -color_primaries bt709 -b:v 15M -maxrate 20M -bufsize 30M -c:a aac -b:a 320k -ar 48000 output_downsample.mp4

    
elif fps < 29:
    # SCENARIO B: Cinematic (24fps / 25fps)
    # BEST PRACTICE: Keep Native. 
    # Forcing 24->30 creates "judder" (stutter). Instagram handles 24fps better 
    # than a cheap local conversion.
    mode = "NATIVE_CINEMATIC"
    ffmpeg -i input_cinematic.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,unsharp=5:5:0.5:5:5:0.0" -c:v libx264 -preset veryslow -profile:v high -level:v 4.2 -g 60 -bf 2 -pix_fmt yuv420p -colorspace bt709 -color_trc bt709 -color_primaries bt709 -b:v 15M -maxrate 20M -bufsize 30M -c:a aac -b:a 320k -ar 48000 output_cinematic.mp4

    
else:
    # SCENARIO C: Standard (29.97 / 30fps)
    # Pass through as is.
    mode = "PASSTHROUGH"
    ffmpeg -i input_standard.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,unsharp=5:5:0.5:5:5:0.0" -c:v libx264 -preset veryslow -profile:v high -level:v 4.2 -g 60 -bf 2 -pix_fmt yuv420p -colorspace bt709 -color_trc bt709 -color_primaries bt709 -b:v 15M -maxrate 20M -bufsize 30M -c:a aac -b:a 320k -ar 48000 output_standard_master.mp4
   


# Summary of Params for the Agent
# Parameter	Value	Why?
# GOP (-g)	60	Forces a keyframe every 2 seconds (at 30fps). Crucial for Instagram's streaming chunks.
# Bitrate	15M	The "Sweet Spot." Higher gets crunched; lower looks bad.
# Audio	48kHz	Standardizes audio sample rate to prevent drift.
# Sharpening	5:5:0.5	"Optical" sharpening (wide radius, low strength). Avoids the "fried" digital look.
# Preset	veryslow	Uses maximum computing power to squeeze quality into the 15MB limit.