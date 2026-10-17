import modal

app = modal.App("video-processor")

# Kerakli kutubxona va ffmpeg sozlamalari
image = modal.Image.debian_slim().pip_install(
    "moviepy==1.0.3",
    "imageio-ffmpeg"
)

@app.function(image=image, cpu=2.0, memory=2048, timeout=300)
def apply_color_filter(video_bytes: bytes, filter_type: str) -> bytes:
    import tempfile
    import os
    from moviepy.editor import VideoFileClip, vfx

    # Vaqtinchalik fayllar yaratamiz
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_tmp:
        input_tmp.write(video_bytes)
        input_path = input_tmp.name

    output_path = tempfile.mktemp(suffix=".mp4")

    try:
        clip = VideoFileClip(input_path)

        # Tanlangan filtr bo'yicha ishlov beramiz
        if filter_type == "sunset":
            processed = clip.fx(vfx.colorx, 1.2)
        elif filter_type == "cyberpunk":
            processed = clip.fx(vfx.lum_contrast, lum=0, contrast=0.3, saturation=1.5)
        elif filter_type == "cinematic":
            processed = clip.fx(vfx.gamma_corr, 0.8)
        else:
            processed = clip

        processed.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast"
        )
        clip.close()
        processed.close()

        with open(output_path, "rb") as f:
            result_bytes = f.read()

        return result_bytes

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
