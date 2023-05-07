from ytb_up.youtube import *
from datetime import datetime,date,timedelta
import asyncio

# if you use some kinda of proxy to access youtube, 
proxy_option = 'socks5://192.168.1.101:7891'

CHANNEL_COOKIES = '/app/cookies.json'
video_path = '/media/白丝妹妹，叮叮当当～.mp4'
video_thumbnail = '/media/extra/白丝妹妹，叮叮当当～.jpg'


# for cookie issue,
title = '【你的灰鸽鸽】叮叮当当'
description = ''
uploader = YoutubeUpload(
    # use r"" for paths, this will not give formatting errors e.g. "\n"
    # root_profile_directory='',
    proxy_option=proxy_option,
    headless=True,
    # if you want to silent background running, set headless true
    CHANNEL_COOKIES=CHANNEL_COOKIES,
    recordvideo=False
    # for test purpose we need to check the video step by step ,
)

if __name__ == '__main__':
    print('定时任务：开始测试上传')
    asyncio.run(uploader.upload(
        videopath=video_path,
        title=title,
        description=description,
        thumbnail=video_thumbnail,
        # tags=tags,
        closewhen100percentupload=True,
        publishpolicy=1
    ))
