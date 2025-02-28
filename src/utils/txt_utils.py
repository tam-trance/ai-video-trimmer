def format_timestamp_txt(seconds):
    """Convert seconds to HH:MM:SS:FF format (FF is frames, assuming 30fps)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remaining = seconds % 60
    seconds_int = int(seconds_remaining)
    # Convert fractional seconds to frames (assuming 30fps)
    frames = int((seconds_remaining - seconds_int) * 30)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}:{frames:02d}"

def create_txt_from_json(segments):
    """Convert JSON segments to the specified text format"""
    txt_lines = []
    for segment in segments:
        start_time = format_timestamp_txt(segment["start"])
        end_time = format_timestamp_txt(segment["end"])
        text = segment["text"]
        
        # Text entry format
        txt_lines.extend([
            f"{start_time} - {end_time}",
            "Unknown",
            text,
            ""  # Empty line between entries
        ])
    
    return "\n".join(txt_lines)
