import os

from moviepy.editor import VideoFileClip, concatenate_videoclips


def create_final_video(video_path, segments, output_path=None):
    """Create the final video by concatenating the selected segments."""
    # Check if segments is a dictionary with 'filtered_transcription' key
    if isinstance(segments, dict) and "filtered_transcription" in segments:
        segments = segments["filtered_transcription"]

    video = VideoFileClip(video_path)
    clips = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        if end - start > 0.1:  # Only include segments longer than 0.1 seconds
            clips.append(video.subclip(start, end))

    if clips:
        final_clip = concatenate_videoclips(clips)

        # If output_path is not provided, create a default path
        if output_path is None:
            os.makedirs("edited", exist_ok=True)
            output_path = os.path.join("edited", os.path.basename(video_path))

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final_clip.close()
    video.close()

    return output_path
