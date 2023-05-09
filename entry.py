
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tinydb import TinyDB, Query, where
from tinydb.operations import increment
from constant import *
from util import get_mp4_path, get_cover_path, resize_cover
from ytb_up.youtube import *
from ytb_up.exceptions import *

# 配置logger
formatter = '%(levelname)s %(message)s'
logging.basicConfig(format=formatter, level=getattr(logging, YTB_LOG_LEVEL))
logger = logging.getLogger('bdm')

db = TinyDB(DB_PATH)
dynamic_list = db.table('dynamic_list', cache_size=0)
shazam_list = db.table('shazam_list', cache_size=0)

uploader = YoutubeUpload(
    proxy_option='socks5://192.168.1.101:7891',
    headless=True,
    channel_cookies=YTB_COOKIE_PATH,
    record_video=False,
    username=YTB_UN,
    password=YTB_PW,
    logger=logger,
)

# # 本地测试
# uploader = YoutubeUpload(
#     # root_profile_directory='',
#     proxy_option='socks5://192.168.1.101:7891',
#     headless=False,
#     channel_cookies=YTB_COOKIE_PATH,
#     record_video=True,
#     username=YTB_UN,
#     password=YTB_PW,
#     logger=logger,
# )

def add_shazam(item):
    q = where('id') == item['shazam_id']
    target = shazam_list.get(q)
    if target != None:
        return {**item, 'etitle': target['title']}
    else:
        return item
    
# 上传视频
# 0正常, -1仅跳过单个视频上传, -2跳过本次所有上传任务
async def task(item) -> int:
    bvid = item['bvid']
    title = item['title']
    uname = item['uname']
    is_portrait = item['is_portrait']
    is_8k = '8K' in item['max_quality']
    etitle = item['etitle'] or title
    
    def upload_failed(err):
        dynamic_list.update({'ustatus': -1}, where('bvid') == bvid)
        dynamic_list.update(increment('up_retry'), where('bvid') == bvid)
        logger.error(err)
        logger.error(f'上传失败：{title}')
        
    if not get_mp4_path(title):
        logger.error(f'未找到视频文件：{title}，跳过该视频')
        return -1
    if not get_cover_path(title):
        logger.error(f'未找到封面文件：{title}，跳过该视频')
        return -1

    video_path = get_mp4_path(title)[0]
    video_cover = resize_cover(get_cover_path(title)[0])

    logger.info(f'开始上传：{title}')
    dynamic_list.update({'ustatus': 150}, where('bvid') == bvid)
    try:
        video_id = await uploader.upload(
            video_path=video_path,
            thumbnail=video_cover,
            title=f'【{uname}】{etitle}{" 竖屏" if is_portrait else ""}{" 8K" if is_8k else ""}',
            description='',
            # 等待上传完成
            wait_upload_complete=True,
            # 公开1，私有0
            publish_policy=1,
        )
    except YoutubeUploadError as err:
        upload_failed(err)
        return -2
    except Exception as err:
        upload_failed(err)
        return -1
    
    # 上传成功
    dynamic_list.update({'ustatus': 200, 'ytb_id': video_id}, where('bvid') == bvid)
    logger.info(f'上传成功：{title}')
    return 0

    # # 本地测试
    # await uploader.upload(
    #     video_path=video_path,
    #     thumbnail=video_cover,
    #     title=f'【{uname}】{etitle}{" 竖屏" if is_portrait else ""}{" 8K" if is_8k else ""}',
    #     description='',
    #     # 等待上传完成
    #     wait_upload_complete=True,
    #     # 公开1，私有0
    #     publish_policy=0,
    # )

async def main():
    logger.info('定时任务：Youtube上传')
    
    sort_by_date = lambda li: sorted(li, key=lambda i: i['pdate'], reverse=False)
    q_wait = (where('ustatus') == 100) & (where('dstatus') == 200)
    q_retry = (where('ustatus') < 0) & (where('up_retry') < 3)
    
    retry_list = sort_by_date(dynamic_list.search(q_retry))
    wait_list = sort_by_date(dynamic_list.search(q_wait))
    
    # add shazam info
    merge_list = list(map(add_shazam, [*retry_list, *wait_list][:CONCURRENT_TASK_NUM]))
    
    # 启动浏览器
    await uploader.launch()
    for item in merge_list:
        result = await task(item)
        if result == -2:
            break
        if result == -1:
            continue

    # 关闭浏览器
    await uploader.close()

if __name__ == '__main__':
    scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(main, 'interval', minutes=30, next_run_time=datetime.now())
    scheduler.start()
    asyncio.get_event_loop().run_forever()
