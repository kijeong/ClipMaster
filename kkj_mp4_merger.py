from moviepy.editor import VideoFileClip

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

list_target_files = ['rooms_39c0c30a65e657b95037_videos_video-1715323325540.webm.mp4', 'rooms_39c0c30a65e657b95037_videos_video-1715323571196.webm.mp4', 'rooms_39c0c30a65e657b95037_videos_video-1715325208026.webm.mp4']

for my_mp4 in list_target_files:
    print(f"start: {my_mp4}")  
    video_properties = get_video_properties(my_mp4) 
    print(video_properties)

