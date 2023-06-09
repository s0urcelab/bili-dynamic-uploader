
import asyncio
import logging
import subprocess
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from tinydb import TinyDB, Query, where
from tinydb.operations import increment
from constant import *
from util import get_mp4_path, get_cover_path, resize_cover
from ytb_up.youtube import YoutubeUpload
from ytb_up.exceptions import YoutubeUploadError

# 配置logger
formatter = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=formatter, datefmt='%Y-%m-%d %H:%M:%S', level=getattr(logging, YTB_LOG_LEVEL))
logger = logging.getLogger('bdm')

init_params = {
    "proxy_option": 'socks5://192.168.1.101:7891',
    "headless": YTB_HEADLESS == 'HEADLESS',
    "channel_id": YTB_CHANNEL_ID,
    "channel_cookies": YTB_COOKIE_PATH,
    "recording": False,
    "logger": logger,
}

async def main(scheduler, job_id, is_delay):
    logger.info('定时任务：Youtube上传')
    
    with TinyDB(DB_PATH) as db:
        dynamic_list = db.table('dynamic_list')
        shazam_list = db.table('shazam_list')
        
        sort_by_date = lambda li: sorted(li, key=lambda i: i['pdate'], reverse=False)
        q_wait = (where('ustatus') == 100) & (where('dstatus') == 200) & (where('shazam_id') != 0)
        q_retry = (where('ustatus') < 0) & (where('up_retry') < 3)
        
        retry_list = sort_by_date(dynamic_list.search(q_retry))
        wait_list = sort_by_date(dynamic_list.search(q_wait))
        
        # add shazam info
        def add_shazam(item):
            q = where('id') == item['shazam_id']
            target = shazam_list.get(q)
            if target != None:
                return {**item, 'etitle': target['title']}
            else:
                return item
        merge_list = list(map(add_shazam, [*retry_list, *wait_list][:UPLOAD_TASK_NUM]))
        
        """
        上传视频
        0 正常, -1 仅跳过单个视频上传, -2 跳过本次所有上传任务
        """
        async def task(upload, item) -> int:
            vid = item['vid']
            title = item['title']
            uname = item['uname']
            is_portrait = item['is_portrait'] if ('is_portrait' in item) else 0
            is_8k = '8K' in item['max_quality']
            etitle = item['etitle'] if ('etitle' in item) else title
            
            def upload_failed(err):
                dynamic_list.update({'ustatus': -1}, where('vid') == vid)
                dynamic_list.update(increment('up_retry'), where('vid') == vid)
                logger.error(f'上传失败：{title}')
                logger.error(err)
            
            find_mp4 = get_mp4_path(item)
            find_cover = get_cover_path(item)
            
            if not find_mp4:
                logger.error(f'未找到mp4文件：{title}，跳过该视频')
                return -1
            if not find_cover:
                logger.error(f'未找到封面文件：{title}，跳过该视频')
                return -1

            video_path = find_mp4[0]
            video_cover = resize_cover(find_cover[0])

            logger.info(f'开始上传：{title}')
            dynamic_list.update({'ustatus': 150}, where('vid') == vid)
            try:
                video_id = await upload(
                    video_path=video_path,
                    thumbnail=video_cover,
                    title=f'【{uname}】{etitle}{" 竖屏" if is_portrait else ""}{" 8K" if is_8k else ""}',
                    description='',
                    # 等待上传完成
                    wait_upload_complete=True,
                    # 公开1，私有0
                    publish_policy=1,
                )
                
                # 上传成功
                dynamic_list.update({'ustatus': 200, 'ytb_id': video_id}, where('vid') == vid)
                logger.info(f'上传成功：{title}')
                return 0
            except YoutubeUploadError as err:
                # 达到上传每日限制，修改下一次执行时间为12小时后
                if err.code == 10002:
                    job = scheduler.get_job(job_id)
                    job.modify(next_run_time=datetime.now() + timedelta(hours=12))
                    job.modify(args=[scheduler, 'main', 'DELAY'])
                upload_failed(err)
                return -2
            except Exception as err:
                upload_failed(err)
                return -1
        
        async with YoutubeUpload(**init_params) as uploader:
            for item in merge_list:
                result = await task(uploader.upload, item)
                if result == -2:
                    break
                if result == -1:
                    continue


if __name__ == '__main__':
    scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
    job = scheduler.add_job(main, 'interval', minutes=20, args=[scheduler, 'main', 'DEFAULT'], id='main')
    def self_restart(event):
        job = scheduler.get_job(event.job_id)
        # 延迟执行，不重启
        if 'DELAY' in job.args:
            job.modify(args=[scheduler, 'main', 'DEFAULT'])
        else:
            subprocess.run(["docker", "restart", "bdm-uploader"])
    scheduler.add_listener(self_restart, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()
    asyncio.get_event_loop().run_forever()
