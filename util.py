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
from_import => source: 1 外部bvid导入，标题.mp4
none        => source: 0 正常下载，标题.mp4
none        => source: 2 新下载器，标题-bvid.mp4
"""
def get_mp4_path(item):
    source = item['source']
    title = glob.escape(legal_title(item['title'][:30]))
    if source in [0, 1]:
        return glob.glob(os.path.join(MEDIA_ROOT, f'{title}*.mp4'))
    else:
        key = item['bvid'] if (source == 2) else item['source']
        return glob.glob(os.path.join(MEDIA_ROOT, f'*{key}*.mp4'))

def get_cover_path(item):
    source = item['source']
    title = glob.escape(legal_title(item['title'][:30]))
    if source in [0, 1]:
        return glob.glob(os.path.join(MEDIA_ROOT, f'{title}*.jpg'))
    else:
        key = item['bvid'] if (source == 2) else item['source']
        result = []
        for ext in ('.jpg', '.png'):
            files = glob.glob(os.path.join(MEDIA_ROOT, f'*{key}*{ext}'))
            result.extend(files)
        return result
    
# def get_mp4_path(name):
#     return glob.glob(os.path.join(MEDIA_ROOT, f'{glob.escape(legal_title(name[:30]))}*.mp4'))

# def get_cover_path(name): 
#     return glob.glob(os.path.join(MEDIA_ROOT, 'extra', f'{glob.escape(legal_title(name[:30]))}*'))

# def get_local_mp4(hash):
#     return glob.glob(os.path.join(MEDIA_ROOT, 'manual', f'*{hash}*.mp4'))

# def get_local_cover(hash):
#     return glob.glob(os.path.join(MEDIA_ROOT, 'manual', f'*{hash}*.png'))

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
    
    