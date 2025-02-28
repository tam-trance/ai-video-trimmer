import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

def create_final_video(video_path, segments):
    """Create the final video by concatenating the selected segments."""
    video = VideoFileClip(video_path)
    clips = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        if end - start > 0.1:  # Only include segments longer than 0.1 seconds
            clips.append(video.subclip(start, end))
    
    if clips:
        final_clip = concatenate_videoclips(clips)
        os.makedirs("edited", exist_ok=True)
        output_path = os.path.join("edited", os.path.basename(video_path))
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final_clip.close()
    video.close()
