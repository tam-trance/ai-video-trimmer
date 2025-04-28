import os, glob, json


def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def create_srt_from_json(segments_data):
    """Convert JSON segments to SRT format"""
    srt_lines = []

    # Check if segments_data is a dictionary with 'filtered_transcription' key
    if isinstance(segments_data, dict) and "filtered_transcription" in segments_data:
        segments = segments_data["filtered_transcription"]
    else:
        segments = segments_data

    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment["text"]

        # SRT entry format
        srt_lines.extend(
            [
                str(i),
                f"{start_time} --> {end_time}",
                text,
                "",  # Empty line between entries
            ]
        )

    return "\n".join(srt_lines)



def merge_and_compress_transcriptions(dir_transcriptions, gap_between_videos):
    ''' Take all the *transcription.json, close the gap between video clips, leave a gap between videos, and output a single .srt
    Args:
    
    '''

    continuous_clips = []
    current_time = 0.0

    transcription_files = sorted(glob.glob(os.path.join(dir_transcriptions, '*_transcription.json')))
    for transcription_path in transcription_files:

        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription_file = json.load(f)

        for cut in transcription_file:
            duration = cut['end'] - cut['start']

            new_clip = {
                'start': round(current_time, 2),
                'end': round(current_time + duration, 2),
                'text': cut['text']
            }
            continuous_clips.append(new_clip)

            current_time += duration  # Move forward

        # After finishing one video (one JSON file), insert gap
        current_time += gap_between_videos

    # Save dict to srt file. 
    srt_content = create_srt_from_json(continuous_clips)
    srt_file = os.path.join(dir_transcriptions, f"transcriptions_all_compressed.srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"Saved SRT file to {srt_file}")
    
    return continuous_clips
