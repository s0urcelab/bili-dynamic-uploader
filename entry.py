
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tinydb import TinyDB, Query, where
from constant import *
from util import get_mp4_path, get_cover_path, resize_cover
from ytb_up.youtube import *

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

# 上传
async def task(item):
    bvid = item['bvid']
    title = item['title']
    uname = item['uname']
    is_portrait = item['is_portrait']
    is_8k = '8K' in item['max_quality']
    etitle = item['etitle'] or title

    if len(get_mp4_path(title)) == 0:
        return logger.error(f'未找到视频：{title}')
    if len(get_cover_path(title)) == 0:
        return logger.error(f'未找到封面：{title}')

    video_path = get_mp4_path(title)[0]
    video_cover = resize_cover(get_cover_path(title)[0])

    try:
        logger.info(f'开始上传：{title}')
        dynamic_list.update({'ustatus': 150}, where('bvid') == bvid)
        await uploader.upload(
            videopath=video_path,
            thumbnail=video_cover,
            title=f'【{uname}】{etitle}{" 竖屏" if is_portrait else ""}{" 8K" if is_8k else ""}',
            description='',
            closewhen100percentupload=True,
            # 公开1，私有0
            publishpolicy=1,
        )
        # 上传成功
        dynamic_list.update({'ustatus': 200}, where('bvid') == bvid)
        logger.info(f'上传成功：{title}')
    except Exception as err:
        dynamic_list.update({'ustatus': -1}, where('bvid') == bvid)
        logger.error(err)
        logger.error(f'上传失败：{title}')

    # # 本地测试
    # await uploader.upload(
    #     videopath=video_path,
    #     thumbnail=video_cover,
    #     title=f'【{uname}】{etitle}{" 竖屏" if is_portrait else ""}{" 8K" if is_8k else ""}',
    #     description='',
    #     # tags=tags,
    #     closewhen100percentupload=True,
    #     # 公开1，私有0
    #     publishpolicy=0,
    # )

async def main():
    logger.info('定时任务：Youtube上传')
    
    sort_by_date = lambda li: sorted(li, key=lambda i: i['pdate'], reverse=False)
    q = (where('ustatus') == 100) & (where('dstatus') == 200)
    li = sort_by_date(dynamic_list.search(q))[:CONCURRENT_TASK_NUM]
    def add_shazam(item):
        q = where('id') == item['shazam_id']
        target = shazam_list.get(q)
        if target != None:
            return {**item, 'etitle': target['title']}
        else:
            return item
    li = list(map(add_shazam, li))
    
    # 启动浏览器
    await uploader.launch()
    for item in li:
        await task(item)
        
    # 关闭浏览器
    await uploader.close()

if __name__ == '__main__':
    scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(main, 'interval', minutes=30, next_run_time=datetime.now())
    scheduler.start()
    asyncio.get_event_loop().run_forever()
