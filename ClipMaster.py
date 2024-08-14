#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClipMaster

This script is used to merge video clips into a single video file.
"""

# === IMPORTS ==================================================================
# modules standards Python
import os
import sys
import re
import subprocess
from logging import getLogger
from datetime import datetime
from collections import defaultdict
from typing import Optional

# modules specific
from dateutil import parser
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.config import change_settings
from tqdm import tqdm

change_settings({"FFMPEG_BINARY": "/usr/local/bin/ffmpeg"})

# modules of the project

# ==============================================================================
__author__ = "kijeong"
__date__ = "2024-07-02"
__version__ = "0.0.2"

# === GLOBALS ==================================================================
logger = getLogger("ClipMaster")


# === CONSTRAINTS ==============================================================
MAX_MERGE_VIDEOS = 100
# merged file name prefix
PREFIX_KCLIP = "kclip"
# renamed file name prefix
PREFIX_NCLIP = "nclip"
# sori clip file name prefix
PREFIX_SCLIP = "rooms"

# room ID
COURSE_ENGLISH_BEGNNER_ID = "39c0c30a65e657b95037"
COURSE_ENGLISH_INTERMEDIATE_ID = "4cce07196571bf2dc2cd"

dict_video_type_beginer = defaultdict(lambda: "Unknown")
dict_video_type_beginer.update({
    # drama
    (1600, 858): "drama_expression",

    # phrasal verbs
    (1600, 1398): "phrasal_verbs",
    # before 2024-04-05
    (1600, 1396): "phrasal_verbs",
    # before 2024-06-05
    (1600, 1492): "phrasal_verbs",
    (1600, 1498): "phrasal_verbs",

    # book
    # before 2024-07-31
    (1600, 1562): "book",
    (1600, 1604): "book",
    (1600, 1888): "book_1",
}
)

dict_video_type_intermidiate = defaultdict(lambda: "Unknown")
dict_video_type_intermidiate.update({
    (1600, 732): "drama_with_script",
    (1600, 858): "real_english_expression",
    (1600, 1398): "phrasal_verbs",
    # before 2024-04-05
    (1600, 1396): "phrasal_verbs",
    # before 2024-06-05
    (1600, 1492): "phrasal_verbs",
    (1600, 1498): "phrasal_verbs",
})


class ClipPiece:
    """
    A class to represent a video clip
    """

    def __init__(self):
        self.file_path = None
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.video_size = None
        self.fps = None
        self.file_size = None
        self.course_name = None
        self.video_type = None
        self.room_id = None
        self.date_time = None
        self.video_size = None
        self.file_name_type = None


# === FUNCTIONS ================================================================

def get_course_name(room_id: str) -> str:
    if room_id == COURSE_ENGLISH_BEGNNER_ID:
        return "Beginner"
    elif room_id == COURSE_ENGLISH_INTERMEDIATE_ID:
        return "Intermediate"
    else:
        return "Unknown"


def get_video_type(room_id: str, video_size: tuple):
    dict_video_type = dict_video_type_beginer if room_id == COURSE_ENGLISH_BEGNNER_ID else dict_video_type_intermidiate
    return dict_video_type.get(video_size, "Unknown")


def parse_date(str_date: str) -> Optional[datetime]:
    if not str_date:
        return None
    # ex) 24-05-11 10:10:10.1
    if len(str_date.split("-")[0]) == 2:
        # 2자리 년도를 4자리로 변경
        # 왜냐하면 dateutil.parser가 2자리 년도를 인식하지 못하기 때문
        str_date = "20" + str_date

    try:
        # 먼저 dateutil.parser를 사용하여 날짜 문자열을 파싱합니다.
        dt = parser.parse(str_date, dayfirst=False)
        return dt
    except ValueError:
        # dateutil.parser가 실패하면 직접 형식을 지정해 파싱을 시도합니다.
        '''
        # 테스트 예제
        date_strings = [
            '2024-05-11 10:10:10.1',
            '24-05-11 10',
            '20240511',
            '05월 11일'
        ]
        '''

        date_formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%y-%m-%d %H',
            '%y-%m-%d',
            '%Y%m%d',
            '%m월 %d일'
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(str_date, fmt)
                return dt
            except ValueError:
                continue
        # 모든 시도가 실패하면 None을 반환합니다.
        return None


def get_file_name_type(file_name: str) -> str:
    """
    file name type:
        'unknown'
        'nclip'
        'kclip'
    :param file_name:
    :return:
    """

    if file_name.startswith(PREFIX_KCLIP):
        return 'kclip'
    elif file_name.startswith(PREFIX_NCLIP):
        return 'nclip'
    elif file_name.startswith(PREFIX_SCLIP):
        return 'sclip'
    else:
        return 'unknown'


def get_target_clips(file_path_dir: str) -> list[ClipPiece]:
    import os
    list_files = os.listdir(file_path_dir)
    list_mp4_files = [x for x in list_files if x.endswith(".mp4")]
    list_video_clip = []
    for file_name in tqdm(list_mp4_files, desc="Analyzing video files"):
        file_path = os.path.join(file_path_dir, file_name)
        try:
            clip_piece = get_clip_piece(file_path)
        except Exception as err:
            print(f"Error: {err}")
            continue
        if not clip_piece:
            continue
        list_video_clip.append(clip_piece)
    list_video_clip = sorted(list_video_clip, key=lambda clip: (clip.course_name, clip.video_type, clip.date_time))

    return list_video_clip


def merge_videos_ffmpeg(video_paths: list, output_name: str) -> None:
    """
    Merge the videos using FFmpeg

    ffmpeg 명령어를 직접사용해야 용량과 시간을 절약할 수 있었다.
    ex.
    ffmpeg -f concat -safe 0 -i file_list.txt -c copy output.mp4
    :param video_paths: list of video paths
    :param output_name: name of the output file
    :return:
    """

    with open('file_list.txt', 'w') as file:
        for video in video_paths:
            file.write(f"file '{video}'\n")

    command = [
        'ffmpeg', '-f', 'concat',
        '-safe', '0', '-i', 'file_list.txt',
        '-c', 'copy', output_name
    ]

    subprocess.run(command)


def merge_videos(video_paths: str, output_name: str) -> None:
    clips = [VideoFileClip(video) for video in video_paths]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_name,
                               codec="libx264",
                               ffmpeg_params=["-c:v", "h264_videotoolbox", "-b:v", "5000k"])
    # I try to use the hardware acceleration, but it seems doesn't work
    # ref. https://trac.ffmpeg.org/wiki/HWAccelIntro
    # final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "cuda"])
    # NVIDIA GPU acceleration
    # final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "cuda"])
    # AMD GPU acceleration
    # final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "dxva2"])
    # macOS acceleration
    # final_clip.write_videofile(output_name, codec="libx264", ffmpeg_params=["-c:v", "h264_videotoolbox"])
    # final_clip.write_videofile(output_name, codec="h264_videotoolbox")

    for clip in clips:
        clip.close()


def merge_selected_videos(list_selected_videos: list, output_name: str) -> None:
    video_paths = [x.file_path for x in list_selected_videos]
    merge_videos_ffmpeg(video_paths, output_name)


def get_selected_videos(dict_candidates: dict,
                        choosed_group_id: int,
                        inputed_date_range: str) -> Optional[list]:
    """
    Get the selected videos based on the user input

    :param dict_candidates: all the video groups
    :param choosed_group_id: the group id of the chosen candidate
    :param inputed_date_range: the inputed date range
    :return: the list of selected videos
    """

    if not inputed_date_range:
        print("Invalid date range")
        return None

    if " ~ " not in inputed_date_range and " - " not in inputed_date_range and "a" != inputed_date_range:
        print("Invalid date range format")
        return None

    if " ~ " in inputed_date_range:
        str_date_start, str_date_end = inputed_date_range.split(" ~ ")
    elif " - " in inputed_date_range:
        str_date_start, str_date_end = inputed_date_range.split(" - ")
    elif "a" == inputed_date_range:
        str_date_start = "2000-01-01"
        str_date_end = "2100-12-31"
    else:
        print("Invalid date range format")
        return None

    date_start = parse_date(str_date_start)
    date_end = parse_date(str_date_end)
    date_end = date_end.replace(hour=23, minute=59, second=59)
    if not date_start or not date_end:
        print("Invalid date format")
        return None
    if date_start > date_end:
        print("Invalid date range")
        return None

    if not dict_candidates[choosed_group_id]:
        print("Invalid candidate")
        return None

    list_selected_videos = None
    for clip in dict_candidates[choosed_group_id]:
        if date_start <= clip.date_time <= date_end:
            if not list_selected_videos:
                list_selected_videos = list()
            list_selected_videos.append(clip)

    if not list_selected_videos:
        print("No videos found for the specified date range")
        return None

    if len(list_selected_videos) < 2:
        print("At least two videos are required to merge")
        return None

    if MAX_MERGE_VIDEOS < len(list_selected_videos):
        print(f"Too many videos selected: {len(list_selected_videos)}, MAX: {MAX_MERGE_VIDEOS}")
        return None

    return list_selected_videos


def save_csv_file(clip_piecs: list, output_name: str) -> None:
    """
    Save the video groups to a CSV file

    다운 받은 파일 세부 사항 확인용
    :param clip_piecs: list of video groups
    :param output_name: name of the output file
    :return:
    """
    with open(output_name, "w") as f:
        f.write("room_id, course_name, video_size, video_type, date, path, fps, duration, file_size\n")
        for clip in clip_piecs:
            f.write(f"{clip.room_id}, "
                    f"{clip.course_name}, "
                    f"{clip.video_size[0]}X{clip.video_size[1]}, "
                    f"{clip.video_type}, "
                    f"{clip.date_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"{os.path.basename(clip.file_path)}, "
                    f"{clip.fps:.0f}, "
                    f"{clip.duration:.0f},"
                    f"{clip.file_size}"
                    f"\n")


def get_subject_duration_sum(dict_groups: dict, griup_id: str) -> str:
    """
    Get the total duration of the video clips in a group

    :param dict_groups: groups of video clips
    :param griup_id: the group id
    :return: the total duration
    """

    sum_duration = 0
    for clip in dict_groups[griup_id]:
        sum_duration += clip.duration

    str_total_duration = datetime.utcfromtimestamp(sum_duration).strftime('%H:%M:%S')
    return str_total_duration


def display_menu(clips: list) -> Optional[list]:
    """
    Display a menu to the user to select the videos to merge

    # 매뉴 구성 샘플의 예
    Please select the course you want to merge.
    0. Exit
    1. Beginner book: {count: 8, date range: 24-05-08 ~ 24-05-31, total duration: 00:00:00}
    2. Beginner drama_expression: {count: 9, date range: 24-06-01 ~ 24-06-14, total duration: 00:00:00}
    3. Beginner phrasal_verbs: {count: 10, date range: 24-06-15 ~ 24-06-28, total duration: 00:00:00}
    4. Intermediate drama_with_script: {count: 11, date range: 24-07-01 ~ 24-07-12, total duration: 00:00:00}
    5. Intermediate real_english_expression: {count: 12, date range: 24-07-13 ~ 24-07-26, total duration: 00:00:00}
    6. Intermediate phrasal_verbs: {count: 13, date range: 24-07-27 ~ 24-08-09, total duration: 00:00:00}
    > 2
    Please input date range you want to merge(x: exit, m: menu).
    ex. 24-06-01 ~ 24-06-14
    > 24-06-01 ~ 24-06-14

    :param clips: list of video clips
    :return:
    """

    menu_index = 1
    dict_candidates = defaultdict(list)

    if not clips:
        print("No video clips found.")
        return None

    print("Please select the course you want to merge.")
    print("0. Exit")

    for clip in clips:
        group_id = f'{clip.room_id}_{clip.video_type}'
        dict_candidates[group_id].append(clip)

    # sort clips by date
    for group_id in dict_candidates.keys():
        sorted(dict_candidates[group_id], key=lambda x: x.date_time)

    for group_id, list_clips in dict_candidates.items():
        course_name = list_clips[0].course_name
        video_type = list_clips[0].video_type
        date_start = list_clips[0].date_time
        date_end = list_clips[-1].date_time
        str_date_start = date_start.strftime('%y-%m-%d')
        str_date_end = date_end.strftime('%y-%m-%d')
        sum_duration = get_subject_duration_sum(dict_candidates, group_id)
        print(f"{menu_index}. {course_name} {video_type}: "
              f"{{count: {len(list_clips)}, date range: {str_date_start} ~ {str_date_end}, "
              f"total duration: {sum_duration}}}")
        menu_index += 1

    choosed_index = int(input("> "))
    if not choosed_index:
        sys.exit(0)

    if choosed_index not in range(1, len(dict_candidates) + 1):
        print("Invalid index")
        return None
    choosed_group_id = list(dict_candidates.keys())[choosed_index - 1]

    print(f"Please input date range you want to merge(a: all, x: exit, m: menu).\n"
          f"ex) 24-05-10 ~ 24-05-31")
    inputed_date_range = input("> ")
    if inputed_date_range == 'x':
        sys.exit(0)
    if inputed_date_range == 'm':
        return display_menu(clips)

    list_selected_videos = get_selected_videos(dict_candidates, choosed_group_id, inputed_date_range)
    if not list_selected_videos:
        return display_menu(clips)

    return list_selected_videos


def get_output_name(selected_clips) -> str:
    """
    Get the output name for the merged video

    :param selected_clips: selected video clips
    :return: the output name
    """

    course_name = selected_clips[0].course_name
    video_type = selected_clips[0].video_type

    # ex) Beginner_book_210508_210531_merged.mp4
    output_name = f"{PREFIX_KCLIP}_" \
                  f"{course_name}_" \
                  f"{video_type}_" \
                  f"{selected_clips[0].date_time.strftime('%y%m%d')}_" \
                  f"{selected_clips[-1].date_time.strftime('%y%m%d')}_merged.mp4"
    return output_name


def generate_new_name(date_time, course_name, video_type):
    new_name = f"{PREFIX_NCLIP}_{course_name}_{video_type}_{date_time.strftime('%y%m%d%H%M')}.mp4"
    return new_name


def rename_files(clips: list) -> None:
    """
    Rename the video files

    :param clips: list of video clips
    :return:
    """

    for clip in clips:
        file_name = os.path.basename(clip.file_path)
        if file_name.startswith(PREFIX_NCLIP):
            continue
        video_type = clip.video_type
        if clip.video_type == "unknown":
            video_type = f"unknown_{clip.video_size[0]}X{clip.video_size[1]}"

        new_name = generate_new_name(clip.date_time, clip.course_name, video_type)
        try:
            os.rename(clip.file_path, os.path.join(os.path.dirname(clip.file_path), new_name))
        except Exception as err:
            print(f"Error: {err}")
        print(f"{file_name} -> {new_name}")


def get_clip_piece(file_path: str) -> Optional[ClipPiece]:
    """
    Get the video clip details

    :param file_path: the path of the video file
    :return: the video clip details
    """

    file_name = os.path.basename(file_path)

    if not file_name.endswith('.mp4'):
        return None

    file_name_type = get_file_name_type(file_name)

    if file_name_type == "unknown" or file_name_type == "kclip":
        return None

    pattern = None

    if file_name.startswith(PREFIX_NCLIP):
        # ex)"nclip_Intermediate_phrasal_verbs_2406101101.mp4"
        pattern = r'nclip_(\w+)_([\w_]+)_(\d{10})\.mp4'

    elif file_name.startswith(PREFIX_SCLIP):
        # Regular expression to match the required parts of the file name
        pattern = r'rooms_(\w+)_videos_video-(\d+)\.webm\.mp4'
    else:
        raise ValueError("Invalid file name")

    if not pattern:
        return None

    match = re.search(pattern, file_name)

    if not match:
        logger.debug("File name does not match the expected format")
        return None

    course_name = None
    video_type = None
    str_date_time = None
    room_id = None
    unix_time = None

    if file_name.startswith(PREFIX_NCLIP):
        course_name = match.group(1)
        video_type = match.group(2)
        str_date_time = match.group(3)
    elif file_name.startswith(PREFIX_SCLIP):
        room_id = match.group(1)
        unix_time = match.group(2)

    if str_date_time:
        # Convert the date time string to a datetime object
        date_time = datetime.strptime(str_date_time, "%y%m%d%H%M")
    else:
        # Convert Unix time to a readable date
        date_time = datetime.fromtimestamp(int(unix_time) / 1000)

    clip = VideoFileClip(file_path)
    clip_piece = ClipPiece()
    clip_piece.file_path = file_path
    clip_piece.start_time = 0
    clip_piece.end_time = clip.duration
    clip_piece.duration = clip.duration
    clip_piece.video_size = tuple(clip.size)
    clip_piece.fps = clip.fps
    clip_piece.file_size = os.path.getsize(file_path)

    clip_piece.room_id, clip_piece.date_time = room_id, date_time
    if not course_name:
        clip_piece.course_name = get_course_name(clip_piece.room_id)
    else:
        clip_piece.course_name = course_name
    if not video_type:

        clip_piece.video_type = get_video_type(clip_piece.room_id, clip_piece.video_size)
    else:
        clip_piece.video_type = video_type

    if not file_name_type:
        clip_piece.file_name_type = get_file_name_type(file_name)
    else:
        clip_piece.file_name_type = file_name_type

    clip.close()

    return clip_piece


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python ClipMaster.py (default: ./sample_files)")
        print("Usage: python ClipMaster.py <directory>")
        print("Usage: python ClipMaster.py rename <directory>")
        sys.exit(1)
    directory = None
    if len(sys.argv) == 1:
        # default directory
        directory = "./sample_files"
        print(f"Using the default directory: {directory}")
    if 3 < len(sys.argv):
        print("Too many arguments")
        sys.exit(1)

    if not directory:
        directory = sys.argv[-1]

    if not os.path.exists(directory):
        print("Please provide the directory containing the video files")
        sys.exit(1)

    clips = get_target_clips(directory)

    if len(sys.argv) == 3 and sys.argv[1] == "rename":
        rename_files(clips)
        return 0

    # 다운받은 목록 확인용
    # ex) video_clips_240814_101001.csv
    output_name = f"video_clips_{datetime.now().strftime('%y%m%d_%H%S%M')}.csv"
    save_csv_file(clips, output_name)

    while True:
        selected_clips = display_menu(clips)
        if not selected_clips:
            break
        output_path = get_output_name(selected_clips)
        merge_selected_videos(selected_clips, output_path)
        print(f"Merged file saved as {output_path}")
    print("Done.")


# ==============================================================================
if __name__ == '__main__':
    main()
