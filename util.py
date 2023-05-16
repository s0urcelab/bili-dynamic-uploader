import html
import re
import glob
import os
from constant import *
from PIL import Image

def replace_illegal(s: str):
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|\n]", '', s)  # replace illegal filename character
    return s
def legal_title(*parts: str, join_str: str = '-'):
    return join_str.join(filter(lambda x: len(x) > 0, map(replace_illegal, parts)))

"""
from_local  => source: hash 本地手动下载，标题-bvid-hash.mp4
none        => source: 0 bilix下载，标题.mp4
from_import => source: 1 外部bvid导入，标题-vid.mp4
none        => source: 2 从动态下载，标题-vid.mp4
none        => source: 3 外部acid导入，标题-vid.mp4
"""
def get_mp4_path(item):
    vid = item['vid']
    source = item['source']
    title = glob.escape(legal_title(item['title'][:30]))
    
    if source in [0]:
        return glob.glob(os.path.join(MEDIA_ROOT, f'{title}*.mp4'))
    elif source in [1, 2, 3]:
        return glob.glob(os.path.join(MEDIA_ROOT, f'*-{glob.escape(vid)}.mp4'))
    else:
        return glob.glob(os.path.join(MEDIA_ROOT, f'*{source}*.mp4'))

def get_cover_path(item):
    vid = item['vid']
    source = item['source']
    title = glob.escape(legal_title(item['title'][:30]))
    
    if source in [0]:
        return glob.glob(os.path.join(MEDIA_ROOT, f'{title}*.jpg'))
    elif source in [1, 2, 3]:
        result = []
        for ext in ('.jpg', '.png', '.jpeg', '.gif'):
            files = glob.glob(os.path.join(MEDIA_ROOT, f'*-{glob.escape(vid)}{ext}'))
            result.extend(files)
        return result
    else:
        return glob.glob(os.path.join(MEDIA_ROOT, f'*{source}*.png'))

def resize_cover(origin_img_path):
    # Check the size of the image file
    if os.path.getsize(origin_img_path) < 1.5 * 1024 * 1024:
        return origin_img_path

    # Open the image file
    image = Image.open(origin_img_path)

    # Calculate the new size of the image
    new_width = int(image.width * 0.4)
    new_height = int(image.height * 0.4)

    # Resize the image
    image_resized = image.resize((new_width, new_height), Image.ANTIALIAS)

    # Save the resized image
    dir_name, file_name = os.path.split(origin_img_path)
    new_img_path = os.path.join(dir_name, 'resized_' + file_name)
    image_resized.save(new_img_path)
    
    return new_img_path
    
    