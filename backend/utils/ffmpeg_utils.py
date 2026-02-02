import subprocess
import os

def stitch_timeline(clips: list, captions: list, output_path: str):
    """
    clips = [{"url": "s3://...", "start": 0, "end": 5}, ...]
    captions = [{"text": "Hello", "start": 0, "end": 2}, ...]
    """
    clip_files = []
    
    for i, clip in enumerate(clips):
        local_path = f"/tmp/clip_{i}.mp4"
        
        if clip['url'].startswith('http'):
            subprocess.run(["curl", "-o", local_path, clip['url']], check=True)
        elif clip['url'].startswith('s3://'):
            subprocess.run(["aws", "s3", "cp", clip['url'], local_path], check=True)
        else:
            local_path = clip['url'].replace('file://', '')
        
        clip_files.append(local_path)
    
    concat_file = "/tmp/concat.txt"
    with open(concat_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")
    
    temp_output = "/tmp/stitched_temp.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-c", "copy", temp_output
    ], check=True)
    
    if captions:
        subtitle_file = "/tmp/subs.srt"
        with open(subtitle_file, "w") as f:
            for i, cap in enumerate(captions, 1):
                start = format_srt_time(cap['start'])
                end = format_srt_time(cap['end'])
                f.write(f"{i}\n{start} --> {end}\n{cap['text']}\n\n")
        
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_output, 
            "-vf", f"subtitles={subtitle_file}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&'",
            "-c:a", "copy", output_path
        ], check=True)
    else:
        os.rename(temp_output, output_path)
    
    return output_path

def format_srt_time(seconds: float):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
