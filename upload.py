import asyncio
import logging
import glob
from datetime import datetime,date,timedelta
from dotenv import load_dotenv
from tinydb import TinyDB, Query, where
from ytb_up.youtube import *

# 加载.env的环境变量
load_dotenv()
# 配置logger
logger = logging.getLogger()

DB_PATH = os.environ['DB_PATH']
CONCURRENT_TASK_NUM = int(os.environ['CONCURRENT_TASK_NUM'])

db = TinyDB(DB_PATH)
config = db.table('config')
dynamic_list = db.table('dynamic_list', cache_size=0)

# if you use some kinda of proxy to access youtube, 
proxy_option = 'socks5://192.168.1.101:7891'

CHANNEL_COOKIES = '/app/cookies.json'
video_path = '/media/白丝妹妹，叮叮当当～.mp4'
video_thumbnail = '/media/extra/白丝妹妹，叮叮当当～.jpg'
# CHANNEL_COOKIES = './cookies.json'
# video_path = '\\\\HTPC\Dance\白丝妹妹，叮叮当当～.mp4'
# video_thumbnail = '\\\\HTPC\Dance\extra\白丝妹妹，叮叮当当～.jpg'

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

def replace_illegal(s: str):
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|\n]", '', s)  # replace illegal filename character
    return s
def legal_title(*parts: str, join_str: str = '-'):
    return join_str.join(filter(lambda x: len(x) > 0, map(replace_illegal, parts)))

MP4_FILE_PATH = lambda name: glob.glob(os.path.join('/media', f'{glob.escape(legal_title(name[:30]))}*.mp4'))
ATTACHMENT_FILE_PATH = lambda name: glob.glob(os.path.join('/media/extra', f'{glob.escape(legal_title(name[:30]))}*'))  

# 上传
async def task(item):
    bvid = item['bvid']
    title = item['title']
    uname = item['uname']
    etitle = item['etitle'] or title

    if not MP4_FILE_PATH(title):
        raise Exception('未找到视频')
    if not ATTACHMENT_FILE_PATH(title):
        raise Exception('未找到封面')

    video_path = MP4_FILE_PATH(title)[0]
    video_cover = ATTACHMENT_FILE_PATH(title)[0]

    dynamic_list.update({'ustatus': 150}, where('bvid') == bvid)

    await uploader.upload(
        videopath=video_path,
        title=f'【{uname}】{etitle}',
        description='',
        thumbnail=video_cover,
        # tags=tags,
        closewhen100percentupload=True,
        # 公开1，私有0
        publishpolicy=1
    )

async def async_task():
    sort_by_date = lambda li: sorted(li, key=lambda i: i['pdate'], reverse=False)
    # 等待上传
    q1 = where('ustatus') == 100
    wait_list = sort_by_date(dynamic_list.search(q1))[:CONCURRENT_TASK_NUM]

    coros = [task(i) for i in wait_list]
    ret_list = await asyncio.gather(*coros, return_exceptions=True)
    for idx, item in enumerate(ret_list):
        item_bvid = li[idx]['bvid']
        item_title = li[idx]['title']
        if isinstance(item, Exception):
            dynamic_list.update({'ustatus': -1}, where('bvid') == item_bvid)
            logger.error(f'上传失败 {item_title}')
        else:
            # 上传成功
            dynamic_list.update({'ustatus': 200}, where('bvid') == item_bvid)
            logger.info(f'上传成功 {item_title}')
    

if __name__ == '__main__':
    logger.info('定时任务：开始准备上传')
    asyncio.run(async_task())
