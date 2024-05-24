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
from logging import getLogger
from datetime import datetime
from collections import defaultdict
from typing import Optional, Tuple

# modules specific
from dateutil import parser
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.config import change_settings

change_settings({"FFMPEG_BINARY": "/usr/local/bin/ffmpeg"})

# modules of the project

# ==============================================================================
__author__ = "kijeong"
__date__ = "2024-05-24"
__version__ = "0.0.1"

# === GLOBALS ==================================================================
logger = getLogger("ClipMaster")


# === CONSTRAINTS ==============================================================
MAX_MERGE_VIDEOS = 100
PREFIX_KCLIP = "kclip_"
COURSE_ENGLISH_BEGNNER_ID = "39c0c30a65e657b95037"
COURSE_ENGLISH_INTERMEDIATE_ID = "4cce07196571bf2dc2cd"
dict_video_type_beginer = {
    (1600, 858): "drama_expression",
    (1600, 1398): "phrasal_verbs",
    (1600, 1604): "book",
    (1600, 1888): "book_1",
}
dict_video_type_intermidiate = {
    (1600, 732): "drama_with_script",
    (1600, 858): "real_english_expression",
    (1600, 1398): "phrasal_verbs",
}


# === FUNCTIONS ================================================================

def get_course_name(room_id: str) -> str:
    if room_id == COURSE_ENGLISH_BEGNNER_ID:
        return "Beginner"
    elif room_id == COURSE_ENGLISH_INTERMEDIATE_ID:
        return "Intermediate"
    else:
        return "Unknown"


def get_video_type(room_id: str, video_size: tuple) -> str:
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


def extract_roomid_datetime_from_filename(file_name: str) -> Optional[Tuple[str, datetime]]:
    """
    Extract the room ID and date time from the file name

    :param file_name: file name to extract the information from
    :return:
    """

    # Regular expression to match the required parts of the file name
    pattern = r'rooms_(\w+)_videos_video-(\d+)\.webm\.mp4'
    match = re.search(pattern, file_name)

    if not match:
        logger.debug("File name does not match the expected format")
        return None

    room_id = match.group(1)
    unix_time = match.group(2)

    # Convert Unix time to a readable date
    date_time = datetime.fromtimestamp(int(unix_time) / 1000)

    return room_id, date_time


def get_video_properties(video_path: str) -> dict:
    clip = VideoFileClip(video_path)
    fps = clip.fps
    duration = clip.duration
    file_size = os.path.getsize(video_path)
    return {
        "size": clip.size,
        "fps": fps,
        "duration": duration,
        "file_size": file_size
    }


def get_mp4_files(file_path: str) -> list[str]:
    import os
    list_files = os.listdir(file_path)
    list_mp4_files = [x for x in list_files if x.endswith(".mp4")]
    return list_mp4_files


def get_video_size(file_path: str) -> tuple[int, int]:
    clip = VideoFileClip(file_path)
    size = clip.size
    clip.close()
    return size


def group_videos_by_room(directory: str):
    """
    Group the videos by room ID and video size

    :param directory: Directory containing the video files
    :return: dictionary of video groups
    """

    video_groups = defaultdict(dict)
    for file_name in os.listdir(directory):
        if not file_name.endswith('.mp4'):
            continue
        # Skip the kclip files
        # because they are not the videos we are interested in
        # because they made by this program
        if file_name.startswith(PREFIX_KCLIP):
            continue
        file_path = os.path.join(directory, file_name)
        room_id, date_time = extract_roomid_datetime_from_filename(file_name)
        if not room_id or not date_time:
            continue
        dict_properties = get_video_properties(file_path)
        size = tuple(dict_properties['size'])
        fps = dict_properties['fps']
        duration = dict_properties['duration']
        if size not in video_groups[room_id]:
            video_groups[room_id][size] = []
        video_groups[room_id][size].append((date_time, file_path, fps, duration))

    # sort the videos by size, then by date
    if video_groups:
        for room_id, dict_size in video_groups.items():
            for size in dict_size.keys():
                video_groups[room_id][size].sort(key=lambda x: x[0])

    return video_groups


def merge_videos(video_paths: str, output_name: str) -> None:
    clips = [VideoFileClip(video) for video in video_paths]
    final_clip = concatenate_videoclips(clips)
    # I try to use the hardware acceleration but it seems doesn't work
    # ref. https://trac.ffmpeg.org/wiki/HWAccelIntro
    # final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "cuda"])
    # NVIDIA GPU acceleration
    # final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "cuda"])
    # AMD GPU acceleration
    # final_clip.write_videofile(output_name, ffmpeg_params=["-hwaccel", "dxva2"])
    # MacOS acceleration
    # final_clip.write_videofile(output_name, codec="libx264", ffmpeg_params=["-c:v", "h264_videotoolbox"])
    # final_clip.write_videofile(output_name, codec="h264_videotoolbox")
    final_clip.write_videofile(output_name,
                               codec="libx264",
                               ffmpeg_params=["-c:v", "h264_videotoolbox", "-b:v", "5000k"])

    for clip in clips:
        clip.close()


def merge_selected_videos(list_selected_videos: list, output_name: str) -> None:
    video_paths = [x[1] for x in list_selected_videos]
    merge_videos(video_paths, output_name)


def get_selected_videos(video_groups: dict,
                        list_candidates: list,
                        choosed_index: int,
                        inputed_date_range: str) -> Optional[list]:
    """
    Get the selected videos based on the user input

    :param video_groups: all the video groups
    :param list_candidates: list of candidates
    :param choosed_index: the index of the chosen candidate
    :param inputed_date_range: the inputed date range
    :return: the list of selected videos
    """

    str_date_start, str_date_end = inputed_date_range.split(" ~ ")
    date_start = parse_date(str_date_start)
    date_end = parse_date(str_date_end)
    if not date_start or not date_end:
        print("Invalid date format")
        return None
    if date_start > date_end:
        print("Invalid date range")
        return None
    if choosed_index not in range(1, len(list_candidates)):
        print("Invalid index")
        return None
    if not list_candidates[choosed_index]:
        print("Invalid candidate")
        return None

    room_id, video_size = list_candidates[choosed_index]
    list_selected_videos = None
    list_videos = video_groups[room_id][video_size]
    for date, path, fps, duration in list_videos:
        if date_start <= date <= date_end:
            if not list_selected_videos:
                list_selected_videos = []
            list_selected_videos.append((date, path, fps, duration))

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


def save_csv_file(video_groups: dict, output_name: str) -> None:
    """
    Save the video groups to a CSV file

    다운 받은 파일 세부 사항 확인용
    :param video_groups: dictionary of video groups
    :param output_name: name of the output file
    :return:
    """
    with open(output_name, "w") as f:
        f.write("room_id, course_name, video_size, video_type, date, path, fps, duration\n")
        for room_id, dict_sizes in video_groups.items():
            course_name = get_course_name(room_id)
            for video_size, list_videos in dict_sizes.items():
                video_type = get_video_type(room_id, video_size)
                for date, path, fps, duration in list_videos:
                    f.write(f"{room_id}, "
                            f"{course_name}, "
                            f"{video_size[0]}X{video_size[1]}, "
                            f"{video_type}, "
                            f"{date.strftime('%Y-%m-%d %H:%M:%S')}, "
                            f"{os.path.basename(path)}, "
                            f"{fps:.0f}, "
                            f"{duration:.0f}\n")


def get_subject_duration_sum(dict_sizes: dict, video_size: tuple) -> str:
    sum_duration = 0
    for date, path, fps, duration in dict_sizes[video_size]:
        sum_duration += duration
    str_total_duration = datetime.utcfromtimestamp(sum_duration).strftime('%H:%M:%S')
    return str_total_duration


def display_menu(video_groups: dict) -> Tuple[list, tuple]:
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
    ex) 24-06-01 ~ 24-06-14
    > 24-06-01 ~ 24-06-14

    :param video_groups:
    :return:
    """

    menu_index = 1
    list_candidates = [None, ]

    print("Please select the course you want to merge.")
    print("0. Exit")
    for room_id, dict_sizes in video_groups.items():
        course_name = get_course_name(room_id)
        if not dict_sizes:
            continue

        # print the videos in each group
        # ex. video_size: (1600, 1398), list_videos: [(datetime, path, fps, duration), ...]
        for video_size, list_videos in dict_sizes.items():
            if not list_videos:
                continue

            video_type = get_video_type(room_id, video_size)
            sum_duration = get_subject_duration_sum(dict_sizes, video_size)
            print(f"{menu_index}. {course_name} {video_type}: {{count: {len(list_videos)}, " 
                  f"date range: {list_videos[0][0].strftime('%y-%m-%d')} ~ {list_videos[-1][0].strftime('%y-%m-%d')}, "
                  f"total duration: {sum_duration} }}")
            # 여기서 list_videos를 list_candidates에 추가할 수도 있지만, room_id와 video_size를 함께 저장하는 것이 더 범용적으로 사용할 수 있을것 같다.
            list_candidates.append((room_id, video_size))
            menu_index += 1

    choosed_index = int(input("> "))
    if not choosed_index:
        sys.exit(0)

    print(f"Please input date range you want to merge(x: exit, m: menu).\n"
          f"ex) 24-05-10 ~ 24-05-31")
    inputed_date_range = input("> ")
    if inputed_date_range == 'x':
        sys.exit(0)
    if inputed_date_range == 'm':
        return display_menu(video_groups)

    list_selected_videos = get_selected_videos(video_groups, list_candidates, choosed_index, inputed_date_range)
    if not list_selected_videos:
        return display_menu(video_groups)

    return list_selected_videos, list_candidates[choosed_index]


def get_output_name(room_id: str, video_size: tuple, list_videos: list) -> str:
    """
    Get the output name for the merged video

    :param room_id: the room ID
    :param video_size: the video size
    :param list_videos: the list of selected videos
    :return: the output name
    """

    course_name = get_course_name(room_id)
    video_type = get_video_type(room_id, video_size)
    # ex) Beginner_book_210508_210531_merged.mp4
    output_name = f"{course_name}_" \
                  f"{video_type}_" \
                  f"{list_videos[0][0].strftime('%y%m%d')}_" \
                  f"{list_videos[-1][0].strftime('%y%m%d')}_merged.mp4"
    return output_name


def main():
    if len(sys.argv) != 2:
        print("Usage: python ClipMaster.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    video_groups = group_videos_by_room(directory)
    # 다운받은 목록 확인용
    save_csv_file(video_groups, "video_groups.csv")
    list_selected_videos, (room_id, video_size) = display_menu(video_groups)
    if not list_selected_videos:
        return
    output_path = get_output_name(room_id, video_size, list_selected_videos)
    merge_selected_videos(list_selected_videos, output_path)
    print(f"Merged file saved as {output_path}")
    print("Done.")


# ==============================================================================
if __name__ == '__main__':
    main()
