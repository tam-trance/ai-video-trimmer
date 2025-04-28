import os, sys

import xml.etree.ElementTree as ET
import xml.dom.minidom

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tam_functions.config import *

# === HELPER FUNCTIONS ===
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def seconds_to_frames(seconds):
    return round(seconds * FRAME_RATE)

def frame_to_ticks(frame):
    return frame * TICKS_PER_FRAME

def create_rate_element(parent):
    rate = ET.SubElement(parent, "rate")
    ET.SubElement(rate, "timebase").text = str(FRAME_RATE)
    ET.SubElement(rate, "ntsc").text = "FALSE"


def create_codec_element(parent):
    codec = ET.SubElement(parent, "codec")
    ET.SubElement(codec, "name").text = "Apple ProRes 422"

    appspecificdata = ET.SubElement(codec, "appspecificdata")
    ET.SubElement(appspecificdata, "appname").text = "Final Cut Pro"
    ET.SubElement(appspecificdata, "appmanufacturer").text = "Apple Inc."
    ET.SubElement(appspecificdata, "appversion").text = "7.0"

    data = ET.SubElement(appspecificdata, "data")
    qtcodec = ET.SubElement(data, "qtcodec")
    ET.SubElement(qtcodec, "codecname").text = "Apple ProRes 422"
    ET.SubElement(qtcodec, "codectypename").text = "Apple ProRes 422"
    ET.SubElement(qtcodec, "codectypecode").text = "apcn"
    ET.SubElement(qtcodec, "codecvendorcode").text = "appl"
    ET.SubElement(qtcodec, "spatialquality").text = "1024"
    ET.SubElement(qtcodec, "temporalquality").text = "0"
    ET.SubElement(qtcodec, "keyframerate").text = "0"
    ET.SubElement(qtcodec, "datarate").text = "0"


def create_timecode_element(parent):
    timecode = ET.SubElement(parent, "timecode")
    create_rate_element(timecode)
    ET.SubElement(timecode, "string").text = "00:00:00:00"
    ET.SubElement(timecode, "frame").text = "0"
    ET.SubElement(timecode, "displayformat").text = "NDF"


def create_media_element(parent):
    '''Hierarchy: xmeml > sequence > media > video > track > file > media > video/audio'''

    media = ET.SubElement(parent, "media")
    
    # --- Video ---
    video = ET.SubElement(media, "video")
    video_sample = ET.SubElement(video, "samplecharacteristics")
    
    video_rate = ET.SubElement(video_sample, "rate")
    ET.SubElement(video_rate, "timebase").text = "30"
    ET.SubElement(video_rate, "ntsc").text = "FALSE"
    
    ET.SubElement(video_sample, "width").text = "3840"
    ET.SubElement(video_sample, "height").text = "2160"
    ET.SubElement(video_sample, "anamorphic").text = "FALSE"
    ET.SubElement(video_sample, "pixelaspectratio").text = "square"
    ET.SubElement(video_sample, "fielddominance").text = "none"
    
    # --- Audio ---
    audio = ET.SubElement(media, "audio")
    audio_sample = ET.SubElement(audio, "samplecharacteristics")
    
    ET.SubElement(audio_sample, "depth").text = "16"
    ET.SubElement(audio_sample, "samplerate").text = "44100"
    
    ET.SubElement(audio, "channelcount").text = "1"
    audio_channel = ET.SubElement(audio, "audiochannel")
    ET.SubElement(audio_channel, "sourcechannel").text = "1"


# === MAIN XML GENERATION ===
def prepare_clips(preprocessed_videos, gap_between_videos):
    '''
    Compute the clip and cut indexing for XML generation. Account for both video and audio tracks.

    Args:
        preprocessed_videos[video_basename] = {
            'video_name': video_basename,
            'video_path': video_file,
            'video_transcriptions': transcription_for_srt
        }
    '''

    clips_video = {}
    timeline_cursor = 0
    clip_id = 1
    masterclip_id_counter = 0  # file-id and masterclip-id have same indexing. corresponds to number of imported videos.

    file_registry = {}

    for video_basename, video_data in preprocessed_videos.items():
        video_name = video_data['video_name']
        video_path = video_data['video_path']
        cuts = video_data['video_transcriptions']

        if video_name not in file_registry:
            file_registry[video_name] = {
                'file_id': f"file-{masterclip_id_counter}",
                'masterclip_id': f"masterclip-{masterclip_id_counter}",
                'video_path': video_path,
                'duration': 0 # compute
            }
            masterclip_id_counter += 1

        for cut in cuts:
            source_in = seconds_to_frames(cut['start'])
            source_out = seconds_to_frames(cut['end'])
            clip_duration_frames = source_out - source_in  # +1 or no? no bc timeline and source indexing deltas should match

            # Add clip indexing for video tracks.
            clips_video[f"clip_video_{str(clip_id)}"] = {
                'clip_video_id': clip_id,
                'video_name': video_name,
                'file_id': file_registry[video_name]['file_id'],
                'masterclip_id': file_registry[video_name]['masterclip_id'],
                'video_path': file_registry[video_name]['video_path'],
                'duration': file_registry[video_name]['duration'],
                'timeline_start': timeline_cursor,
                'timeline_end': timeline_cursor + clip_duration_frames,
                'source_in': source_in,
                'source_out': source_out,
            }

            timeline_cursor += clip_duration_frames
            clip_id += 1

        # Insert a gap between different videos
        timeline_cursor += gap_between_videos

    total_number_video_clips = clip_id # copy to be safe

    # Add clip indexing for audio tracks. Handled after all video track indexing.
    # Do not reset clip_id. 
    clips_audio = {} # But do create a separate lookup dict.
    for clip_key, clip_values in clips_video.items():
            
            # Add audio clip id into clips_video dict.
            clip_video_id = clip_values['clip_video_id']
            clip_audio_id = clip_video_id + total_number_video_clips 
            clip_values['clip_audio_id'] = clip_audio_id

            # Create separate clips_audio with key by audio clip.
            clips_audio[f"clip_audio_{clip_audio_id}"] = clip_values # copy to be safe

    return clips_video, clips_audio, file_registry


def generate_full_xml(clips_video, clips_audio):
    xmeml = ET.Element("xmeml", version="4")

    sequence = ET.SubElement(xmeml, "sequence", id="sequence-1")
    ET.SubElement(sequence, "uuid").text = generate_uuid()
    last_key = list(clips_video.keys())[-1]
    last_value = clips_video[last_key]
    ET.SubElement(sequence, "duration").text = str(last_value['timeline_end'])
    create_rate_element(sequence)
    ET.SubElement(sequence, "name").text = "Auto Generated Sequence"

    media = ET.SubElement(sequence, "media")

    # --- Create sequence > media > video ---
    video = ET.SubElement(media, "video")
    video_format = ET.SubElement(video, "format")
    video_sample = ET.SubElement(video_format, "samplecharacteristics")
    create_rate_element(video_sample)
    create_codec_element(video_sample)
    ET.SubElement(video_sample, "width").text = "3840"
    ET.SubElement(video_sample, "height").text = "2160"
    ET.SubElement(video_sample, "anamorphic").text = "FALSE"
    ET.SubElement(video_sample, "pixelaspectratio").text = "square"
    ET.SubElement(video_sample, "fielddominance").text = "lower"
    ET.SubElement(video_sample, "colordepth").text = str(24)

    # --- Create video > first track (where all the clips are) ---
    track = ET.SubElement(video, "track")
    file_written = set()

    for (clip_video_key, clip_video_value), (clip_audio_key, clip_audio_value) in zip(clips_video.items(), clips_audio.items()):

        clip = clip_video_value

        clipitem = ET.SubElement(track, "clipitem", id=f"clipitem-{clip['clip_video_id']}") # computed values
        ET.SubElement(clipitem, "masterclipid").text = str(clip['masterclip_id']) # computed values
        ET.SubElement(clipitem, "name").text = clip['video_name']
        ET.SubElement(clipitem, "enabled").text = "TRUE"
        ET.SubElement(clipitem, "duration").text = str(clip['duration']) # computed values
        create_rate_element(clipitem)

        ET.SubElement(clipitem, "start").text = str(clip['timeline_start'])
        ET.SubElement(clipitem, "end").text = str(clip['timeline_end'])
        ET.SubElement(clipitem, "in").text = str(clip['source_in'])
        ET.SubElement(clipitem, "out").text = str(clip['source_out'])
        ET.SubElement(clipitem, "pproTicksIn").text = str(frame_to_ticks(clip['source_in']))
        ET.SubElement(clipitem, "pproTicksOut").text = str(frame_to_ticks(clip['source_out']))

        ET.SubElement(clipitem, "alphatype").text = "none"
        ET.SubElement(clipitem, "pixelaspectratio").text = "square"
        ET.SubElement(clipitem, "anamorphic").text = "FALSE"

        # insert the <file> info only if it's the first <clipitem> of that <file>
        if clip['video_name'] not in file_written:
            file = ET.SubElement(clipitem, "file", id=clip['file_id'])
            ET.SubElement(file, "name").text = clip['video_name']
            ET.SubElement(file, "pathurl").text = f"file://{clip['video_path']}"
            create_rate_element(file)
            ET.SubElement(file, "duration").text = str(clip['duration']) # computed value
            create_timecode_element(file)
            create_media_element(file)
            file_written.add(clip['video_name'])
        else:
            ET.SubElement(clipitem, "file", id=clip['file_id'])

        # Link element placeholder
        link = ET.SubElement(clipitem, "link")
        ET.SubElement(link, "linkclipref").text = f"clipitem-{clip['clip_video_id']}" # computed value?
        ET.SubElement(link, "mediatype").text = "video" # modularize for "audio" too
        ET.SubElement(link, "trackindex").text = "1"
        ET.SubElement(link, "clipindex").text = str(clip['masterclip_id']) # computed value

        link = ET.SubElement(clipitem, "link")
        ET.SubElement(link, "linkclipref").text = f"clipitem-{clip['clip_audio_id']}" # computed value?
        ET.SubElement(link, "mediatype").text = "audio" # modularize for "audio" too
        ET.SubElement(link, "trackindex").text = "1"
        ET.SubElement(link, "clipindex").text = str(clip['masterclip_id']) # computed value
        ET.SubElement(link, "groupindex").text = "1"

        # Logging and color info placeholders
        ET.SubElement(clipitem, "logginginfo")
        ET.SubElement(clipitem, "colorinfo")
    
    ET.SubElement(track, "enabled").text = "TRUE"
    ET.SubElement(track, "locked").text = "FALSE"


    # --- Create sequence > media > audio ---
    audio = ET.SubElement(media, "audio")
    ET.SubElement(audio, "numOutputChannels").text = str(2)
    audio_format = ET.SubElement(audio, "format")
    audio_sample = ET.SubElement(audio_format, "samplecharacteristics")
    ET.SubElement(audio_format, "depth").text = str(16)
    ET.SubElement(audio_format, "samplerate").text = str(44100)
    audio_outputs = ET.SubElement(audio, "outputs")
    outputs_group = ET.SubElement(audio_outputs, "group")
    ET.SubElement(outputs_group, "index").text = str(1)
    ET.SubElement(outputs_group, "numchannels").text = str(1)
    ET.SubElement(outputs_group, "downmix").text = str(0)
    group_channel = ET.SubElement(outputs_group, "channel")
    ET.SubElement(group_channel, "index").text = str(1)
    outputs_group2 = ET.SubElement(audio_outputs, "group")
    ET.SubElement(outputs_group, "index").text = str(2)
    ET.SubElement(outputs_group, "numchannels").text = str(1)
    ET.SubElement(outputs_group, "downmix").text = str(0)
    group_channel = ET.SubElement(outputs_group, "channel")
    ET.SubElement(group_channel, "index").text = str(2)

    # --- Create audio > first track (where all the clips are) ---
    track = ET.SubElement(audio, "track")

    for (clip_video_key, clip_video_value), (clip_audio_key, clip_audio_value) in zip(clips_video.items(), clips_audio.items()):

        clip = clip_audio_value

        clipitem = ET.SubElement(track, "clipitem", id=f"clipitem-{clip['clip_audio_id']}") # computed values
        ET.SubElement(clipitem, "masterclipid").text = str(clip['masterclip_id']) # computed values
        ET.SubElement(clipitem, "name").text = clip['video_name']
        ET.SubElement(clipitem, "enabled").text = "TRUE"
        ET.SubElement(clipitem, "duration").text = str(clip['duration']) # computed values
        create_rate_element(clipitem)

        ET.SubElement(clipitem, "start").text = str(clip['timeline_start'])
        ET.SubElement(clipitem, "end").text = str(clip['timeline_end'])
        ET.SubElement(clipitem, "in").text = str(clip['source_in'])
        ET.SubElement(clipitem, "out").text = str(clip['source_out'])
        ET.SubElement(clipitem, "pproTicksIn").text = str(frame_to_ticks(clip['source_in']))
        ET.SubElement(clipitem, "pproTicksOut").text = str(frame_to_ticks(clip['source_out']))

        ET.SubElement(clipitem, "file", id=clip['file_id']) # no need to repeat <file>
        sourcetrack = ET.SubElement(clipitem, "sourcetrack")
        ET.SubElement(sourcetrack, "mediatype").text = "audio"
        ET.SubElement(sourcetrack, "trackindex").text = str(1)

        # Link element placeholder
        link = ET.SubElement(clipitem, "link")
        ET.SubElement(link, "linkclipref").text = f"clipitem-{clip['clip_video_id']}" # computed value?
        ET.SubElement(link, "mediatype").text = "video" # modularize for "audio" too
        ET.SubElement(link, "trackindex").text = "1"
        ET.SubElement(link, "clipindex").text = str(clip['masterclip_id']) # computed value

        link = ET.SubElement(clipitem, "link")
        ET.SubElement(link, "linkclipref").text = f"clipitem-{clip['clip_audio_id']}" # computed value?
        ET.SubElement(link, "mediatype").text = "audio" # modularize for "audio" too
        ET.SubElement(link, "trackindex").text = "1"
        ET.SubElement(link, "clipindex").text = str(clip['masterclip_id']) # computed value
        ET.SubElement(link, "groupindex").text = "1"

        # Logging and color info placeholders
        ET.SubElement(clipitem, "logginginfo")
        ET.SubElement(clipitem, "colorinfo")

        ET.SubElement(track, "enabled").text = "TRUE"
        ET.SubElement(track, "locked").text = "FALSE"
        ET.SubElement(track, "outputchannelindex").text = str(1)


    # ---- Tail items of <sequence> -----
    timecode = ET.SubElement(sequence, "timecode")
    create_rate_element(timecode)
    ET.SubElement(timecode, "string").text = "00:00:00:00"
    ET.SubElement(timecode, "frame").text = "0"
    ET.SubElement(timecode, "displayformat").text = "NDF"
    labels = ET.SubElement(sequence, "labels")
    ET.SubElement(labels, "label2").text = "Forest" # why?
    ET.SubElement(sequence, "logginginfo")


    return xmeml


def save_pretty_xml(root_element, output_file_path):
    xml_str = ET.tostring(root_element, encoding='utf-8')
    parsed = xml.dom.minidom.parseString(xml_str)
    pretty_xml_as_str = parsed.toprettyxml(indent="  ")
    # pretty_xml_as_str = pretty_xml_as_str.replace('  ', '\t') # with tabs instead of spaces

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml_as_str)

    print(f"✅ Saved XML to {output_file_path}")