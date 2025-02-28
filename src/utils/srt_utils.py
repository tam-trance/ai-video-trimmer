def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def create_srt_from_json(segments):
    """Convert JSON segments to SRT format"""
    srt_lines = []
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment["text"]
        
        # SRT entry format
        srt_lines.extend([
            str(i),
            f"{start_time} --> {end_time}",
            text,
            ""  # Empty line between entries
        ])
    
    return "\n".join(srt_lines)
