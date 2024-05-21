#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClipMaster

"""

# === IMPORTS ==================================================================
# modules standards Python
import os
import sys
from logging import getLogger

# modules specific
from collections import defaultdict
from moviepy.editor import VideoFileClip, concatenate_videoclips

# modules of the project

# ==============================================================================
__author__ = "kijeong"
__date__ = "2024-05-22"
__version__ = "0.0.1"

# === GLOBALS ==================================================================
logger = getLogger("ClipMaster")


# === CONSTRAINTS ==============================================================
# === FUNCTIONS ================================================================
def get_video_properties(video_path):
    clip = VideoFileClip(video_path)
    width, height = clip.size
    fps = clip.fps
    duration = clip.duration
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration
    }


def get_mp4_files(file_path):
    import os
    list_files = os.listdir(file_path)
    list_mp4_files = [x for x in list_files if x.endswith(".mp4")]
    return list_mp4_files


def get_video_size(file_path):
    clip = VideoFileClip(file_path)
    size = clip.size
    clip.close()
    return size


def group_videos_by_size(directory):
    video_groups = defaultdict(list)
    for file_name in os.listdir(directory):
        if not file_name.endswith('.mp4'):
            continue
        if file_name.startswith('kclip_'):
            continue
        file_path = os.path.join(directory, file_name)
        size = get_video_size(file_path)
        video_groups[tuple(size)].append(file_path)
    return video_groups


def merge_videos(video_paths, output_name):
    clips = [VideoFileClip(video) for video in video_paths]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "cuda"])
    for clip in clips:
        clip.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python merge_videos.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    video_groups = group_videos_by_size(directory)

    for size, videos in video_groups.items():
        print(f"Group for size {size}:")
        for video in videos:
            print(f"  {video}")

        if 1 < len(videos):
            output_name = input(f"Enter the name for the merged file for group {size} (without extension). (skip: n): ")
            if output_name == 'n':
                continue
            output_path = os.path.join(directory, f"kclip_{output_name}.mp4")
            merge_videos(videos, output_path)
            print(f"Merged file saved as {output_path}")
    print("Done.")


# === CLASSES ==================================================================
# ==============================================================================
if __name__ == '__main__':
    main()
