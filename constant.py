import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ['DB_PATH']
MEDIA_ROOT = os.environ['MEDIA_ROOT']
YTB_COOKIE_PATH = os.environ['YTB_COOKIE_PATH']
CONCURRENT_TASK_NUM = int(os.environ['CONCURRENT_TASK_NUM'])
YTB_LOG_LEVEL = os.environ['YTB_LOG_LEVEL']
YTB_UN = os.environ['YTB_UN']
YTB_PW = os.environ['YTB_PW']