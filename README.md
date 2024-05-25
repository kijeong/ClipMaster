# ClipMaster
이 프로젝트는 SoriChat 영어 수업용 영상에서 원하는 클립들을 합쳐서 하나의 영상으로 만들어주는 프로그램입니다.

## 사용환경
- MacOS, Python 3.11
- 다양한 운용체제 환경에 맞게 적절하게 수정해서 사용하실 수 있습니다.

## SoriChat 주소
- 초보영어: https://sori.team/room/39c0c30a65e657b95037
- 중급영어: https://sori.team/room/4cce07196571bf2dc2cd

## 필요한 라이브러리
- ffmpeg (brew install ffmpeg)
- moviepy
- python-dateutil

## 사용법
1. SoriChat에서 다운로드 받은 영상 파일들을 하나의 폴더에 넣습니다.
1. python ClipMaster.py 영상_파일이_있는_폴더 
   - ex. python ClipMaster.py /Users/username/Downloads
   - if you use virtualenv, first activate it.
   - ex. source /Users/username/venv/bin/activate
1. 프로그램이 실행되면, 영상 파일들의 목록 정보가 출력됩니다.
1. 합치기를 원하는 영상 파일들의 분류와 날짜 범위를 지정합니다.
1. 합쳐진 영상 파일이 생성됩니다.
   - ex. kclip_Intermediate_phrasal_verbs_240510_240521_merged.mp4
     - 중급영어의 구동사 영상 2024년 5월 10일부터 2024년 5월 21일까지의 영상 파일을 합친 것입니다.

## 참고
- 영상 파일은 mp4 확장자여야 합니다.
- 영상 파일 이름의 형식은 다음과 같아야 합니다.
  - rooms_(\w+)_videos_video-(\d+)\.webm\.mp4
  - SoriChat에서 영상을 다운로드 받으면 위와 같은 형식입니다.
    - (\w+)는 방 이름을 나타내며, (\d+)는 날짜 정보를 나타냅니다.
- 프로그램 실행 후 video_groups.csv 파일을 보면 다운 받으신 영상 파일들의 정보를 확인할 수 있습니다.
