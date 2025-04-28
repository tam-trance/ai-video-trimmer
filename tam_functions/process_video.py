import glob
import os
import sys
import json
import argparse
import pymiere
from pydub import AudioSegment

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.audio.processing import detect_segments, extract_audio, filter_segments
from src.llm.suggestion import get_llm_suggestion
from src.transcription.whisper import transcribe_segments
from src.utils.json_utils import save_json
from src.utils.srt_utils import create_srt_from_json, merge_and_compress_transcriptions
from src.utils.xml_utils import prepare_clips, generate_full_xml, save_pretty_xml
from src.video.editor import create_final_video
from tam_functions.config import *

from pymiere.wrappers import get_system_sequence_presets
from pymiere.wrappers import time_from_seconds, timecode_from_time
sequence_preset_path = "/Users/tamtran/Documents/Adobe/Premiere Pro (Beta)/25.0/Profile-tamtran/Settings/Custom/4K 30fps actually.sqpreset"



def seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS:MS format"""
    # Handle milliseconds
    ms = int((seconds % 1) * 100)
    
    # Handle hours, minutes, seconds
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    secs = int(seconds) % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{ms:02d}"



def generate_video_transcription(
    video_path, dump_dir, generate_suggestion=False, generate_srt=True, generate_video=False, output_video=None
):
    """
    Process a video file to extract audio, transcribe it, get suggestions, and optionally
    create an SRT file and edited video.

    Args:
        video_path (str): Path to the video file to process
        generate_srt (bool): Whether to generate an SRT subtitle file
        generate_video (bool): Whether to generate an edited video
        output_video (str, optional): Path for the output video. If None, creates in the 'edited' folder.

    Returns:
        bool: True if successful
    """
    print(f"Processing {video_path}")
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Get directory for output - use the directory where the script is located
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create necessary directories relative to the script directory
    os.makedirs(os.path.join(script_dir, dump_dir), exist_ok=True)

    # Step 1: Extract full audio from the video
    temp_audio_file = os.path.join(script_dir, dump_dir, f"{base_name}_tmp_audio.wav")
    extract_audio(video_path, temp_audio_file)

    # Step 2: Load audio and detect segments based on sound levels
    audio = AudioSegment.from_file(temp_audio_file)
    raw_segments = detect_segments(audio, chunk_ms=100) # list[Dict]
    raw_segments_file = os.path.join(
        script_dir, dump_dir, f"{base_name}_segments_raw.json"
    )
    save_json(raw_segments, raw_segments_file)
    print(f"Saved raw segments JSON to {raw_segments_file}")


    # Step 2b: Filter the segments based on the length
    filtered_segments = filter_segments(raw_segments, min_duration_sec=1.0)
    filtered_segments_file = os.path.join(
        script_dir, dump_dir, f"{base_name}_segments_filtered.json"
    )
    save_json(filtered_segments, filtered_segments_file)
    print(f"Saved filtered segments JSON to {filtered_segments_file}")

    # Step 3: For each segment, transcribe the audio using Whisper
    raw_transcription = transcribe_segments(audio, filtered_segments)
    raw_transcription_file = os.path.join(
        script_dir, dump_dir, f"{base_name}_transcription.json"   
    )
    save_json(raw_transcription, raw_transcription_file)
    print(f"Saved raw transcription JSON to {raw_transcription_file}")
    transcription_for_srt = raw_transcription

    os.remove(temp_audio_file)

    # Step 4: Send raw transcription to an LLM for filtering and save suggestion JSON locally
    if generate_suggestion:
        suggestion = get_llm_suggestion(raw_transcription)
        suggestion_file = os.path.join(script_dir, dump_dir, f"{base_name}_suggestion.json")  
        save_json(suggestion, suggestion_file)
        print(f"Saved LLM suggestion JSON to {suggestion_file}")
        transcription_for_srt = suggestion

    # Step 5: Create SRT file if requested
    if generate_srt:
        srt_content = create_srt_from_json(transcription_for_srt)
        srt_file = os.path.join(script_dir, dump_dir, f"{base_name}.srt")
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"Saved SRT file to {srt_file}")

    # Step 6: Create the final video if requested
    if generate_video:
        if output_video is None:
            output_video = os.path.join(script_dir, dump_dir, f"{base_name}_edited.mp4")
        create_final_video(video_path, transcription_for_srt, output_video)
        print(f"Saved edited video to {output_video}")

    return transcription_for_srt


def create_project_from_videos(base_dir, raw_folder, dump_folder, project_file=None):
    """Process all video files in the 'raw' directory"""

    # Step 0: Same project for all videos. Project should be created and open already.
    project = pymiere.objects.app.project
    qe_project = pymiere.objects.qe.project

    video_files = sorted(glob.glob(os.path.join(base_dir, raw_folder, "*")))
    for video_file in video_files:
            
        assert os.path.isfile(video_file) and video_file.lower().endswith(
            (".mp4", ".mov", ".avi", ".mkv")
        )
        
        # Step 1: Load or generate transcription for the video
        video_basename = os.path.splitext(os.path.basename(video_file))[0]
        dump_dir = os.path.join(base_dir, dump_folder)
        # check if file exists in dump_dir
        if os.path.exists(os.path.join(dump_dir, f"{video_basename}_transcription.json")):
            print(f"Loading existing transcription for {video_basename}")
            transcription_for_srt = json.load(open(os.path.join(dump_dir, f"{video_basename}_transcription.json")))
        else:
            transcription_for_srt = generate_video_transcription(video_file, dump_dir) # List[Dict]
        srt_filepath = os.path.join(dump_dir, f"{video_basename}.srt")

        # Step 2: Create new Pr sequence and import video
        # create sequence # (don't use pymiere.objects.app.project.createNewSequence() as it pop a window requiring user intervention)
        video_basename = os.path.splitext(os.path.basename(video_file))[0]
        sequence_name = f"seq {video_basename}"  
        pymiere.objects.qe.project.newSequence(sequence_name, sequence_preset_path)  # (TT: creates new empty sequence)
        # # find newly created sequence by name  
        # sequence = [s for s in pymiere.objects.app.project.sequences if s.name == sequence_name][0]  
        # # open sequence in UI (TT: creates new sequence with video file 3 times)
        # pymiere.objects.app.project.openSequence(sequenceID=sequence.sequenceID)  
        # # this is now our active sequence  
        # print(pymiere.objects.app.project.activeSequence)

        # import media into Premiere 
        sequence = project.activeSequence
        media_path = os.path.abspath(video_file)  # Use absolute path
        success = project.importFiles(  
            [media_path, srt_filepath],
            suppressUI=True,  
            targetBin=project.getInsertionBin(),  
            importAsNumberedStills=False  
        )  

        if not success:
            raise Exception("Failed to import media file")

        # find media we imported  
        items = project.rootItem.findItemsMatchingMediaPath(media_path, ignoreSubclips=False)  
        if not items or len(items) == 0:
            raise Exception("Could not find imported media in project")

        # add clip to active sequence  
        project.activeSequence.videoTracks[0].insertClip(items[0], time_from_seconds(0))

        # Access the QE project
        qe_sequence = qe_project.getActiveSequence()
        qe_video_track = qe_sequence.getVideoTrackAt(0)

        # Step 3: Cut the video based on the transcription segments
        cut_points = []
        for segment in transcription_for_srt:
            cut_points.extend([segment["start"], segment["end"]])
        cut_points = sorted(set(cut_points))

        # sequence = project.activeSequence
        for point in cut_points:
            time_obj = time_from_seconds(point)
            timecode = timecode_from_time(time_obj, sequence)
            qe_video_track.razor(timecode)
            print(f"Cut made at {seconds_to_timestamp(point)}")

    # Step 4: Pause: Import the SRT file to Pr. Remove unwanted clips.
    # input("ACTION: Apply cuts to audio. Apply SRT file as subtitles. Remove unwanted clips. [ENTER]")
    # ^ can also batch manual step at the end for all videos



def create_xml_from_videos(base_dir, raw_folder, dump_folder, gap_between_videos):
    '''
    Args:
        gap_between_videos (int): frames between the different videos.
    '''

    # Step 1: Generate transcriptions and cuttings from all videos first.
    video_files = sorted(glob.glob(os.path.join(base_dir, raw_folder, "*")))
    preprocessed_videos = {}
    for video_file in video_files:
            
        assert os.path.isfile(video_file) and video_file.lower().endswith(
            (".mp4", ".mov", ".avi", ".mkv")
        )
        
        # Step 1: Load or generate transcription for the video
        video_basename = os.path.splitext(os.path.basename(video_file))[0]
        dump_dir = os.path.join(base_dir, dump_folder)
        # check if file exists in dump_dir
        if os.path.exists(os.path.join(dump_dir, f"{video_basename}_transcription.json")):
            print(f"Loading existing transcription for {video_basename}")
            transcription_for_srt = json.load(open(os.path.join(dump_dir, f"{video_basename}_transcription.json")))
        else:
            transcription_for_srt = generate_video_transcription(video_file, dump_dir) # List[Dict]
        srt_filepath = os.path.join(dump_dir, f"{video_basename}.srt")

        # Append transcription preprocessing to output data
        preprocessed_videos[video_basename] = {
            'video_name': video_basename,
            'video_path': video_file,
            'video_transcriptions': transcription_for_srt
        }

    # Step 2: Compute aggregrated clips, their clip indexes, their frame indexes. Incorporate gap_between_video. 
    clips_video, clips_audio, file_registry = prepare_clips(preprocessed_videos, gap_between_videos)

    # Step 3: Process clip data into XML file.
    xml_root = generate_full_xml(clips_video, clips_audio)

    # Step 4: Save XML file to dump_dir. Print statement. End there.
    save_pretty_xml(xml_root, os.path.join(base_dir, dump_dir, "auto_generated_sequence.xml"))

    # SKIP: Open Premiere Pro project and import files. Just do that part manually. 
    



if __name__ == "__main__":

    # video_file = "/Users/tamtran/Documents/devy/00_repos/VideoEditing/ai-video-trimmer/raw/IMG_0644_short2min.mov"
    # video_file = "/Users/tamtran/Documents/devy/00_repos/VideoEditing/ai-video-trimmer/raw/IMG_0644.mov"
    # generate_video_transcription(video_file, generate_suggestion=False)

    if False:
        base_dir = "/Users/tamtran/Documents/devy/00_repos/VideoEditing/ai-video-trimmer"
        raw_folder = "raw"
        dump_folder = "dump_xml"
        # project_file = "projects/test_aivideotrimmer4.prproj"
        # create_project_from_videos(base_dir, raw_folder, dump_folder)
        create_xml_from_videos(base_dir, raw_folder, dump_folder, GAP_BETWEEN_VIDEOS)
        merge_and_compress_transcriptions(os.path.join(base_dir, dump_folder), GAP_BETWEEN_VIDEOS)

    # args for command line
    if True:
        base_dir, raw_folder, dump_folder = None, None, None
        parser = argparse.ArgumentParser(description='Process video files.')
        parser.add_argument('--base_dir', type=str, default=base_dir, help='Base directory')
        parser.add_argument('--raw_folder', type=str, default=raw_folder, help='Raw folder')
        parser.add_argument('--dump_folder', type=str, default=dump_folder, help='Dump folder')
        args = parser.parse_args()
        abs_base_dir = os.path.abspath(args.base_dir)
        # create_project_from_videos(args.base_dir, args.raw_folder, args.dump_folder)
        create_xml_from_videos(abs_base_dir, args.raw_folder, args.dump_folder, GAP_BETWEEN_VIDEOS)
        merge_and_compress_transcriptions(os.path.join(abs_base_dir, args.dump_folder), GAP_BETWEEN_VIDEOS)
