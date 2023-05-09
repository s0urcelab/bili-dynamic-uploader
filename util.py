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

def get_mp4_path(name):
    return glob.glob(os.path.join(MEDIA_ROOT, f'{glob.escape(legal_title(name[:30]))}*.mp4'))

def get_cover_path(name): 
    return glob.glob(os.path.join(MEDIA_ROOT, 'extra', f'{glob.escape(legal_title(name[:30]))}*'))

def get_local_mp4(hash):
    return glob.glob(os.path.join(MEDIA_ROOT, 'manual', f'*{hash}*.mp4'))

def get_local_cover(hash):
    return glob.glob(os.path.join(MEDIA_ROOT, 'manual', f'*{hash}*.png'))

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
    
    