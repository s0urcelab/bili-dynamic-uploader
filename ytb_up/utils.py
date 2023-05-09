import time
import re
import logging
from time import sleep
from datetime import datetime
from playwright.async_api import *
from .constants import *
from pathlib import Path
import os
from typing import Tuple, Optional,Union


def get_path(file_path: str) -> str:
    # no clue why, but this character gets added for me when running
    # return str(os.path(file_path)).replace("\u202a", "")
    # return file_path.replace("\u202a", "")
    return str(Path(file_path)).replace("\u202a", "")

async def set_channel_language_english(page):
    # why does not work again
    try:
        print('Click your profile icon .')
        page.locator(
            "yt-img-shadow.ytd-topbar-menu-button-renderer > img:nth-child(1)")
        await page.click(
            "yt-img-shadow.ytd-topbar-menu-button-renderer > img:nth-child(1)")
        print(' Click Language or Location icon')
        page.locator("yt-multi-page-menu-section-renderer.style-scope:nth-child(2) > div:nth-child(2) > ytd-compact-link-renderer:nth-child(2) > a:nth-child(1) > tp-yt-paper-item:nth-child(1) > div:nth-child(2) > yt-formatted-string:nth-child(2)")
        await page.click("yt-multi-page-menu-section-renderer.style-scope:nth-child(2) > div:nth-child(2) > ytd-compact-link-renderer:nth-child(2) > a:nth-child(1) > tp-yt-paper-item:nth-child(1) > div:nth-child(2) > yt-formatted-string:nth-child(2)")
        selector_en_path = "ytd-compact-link-renderer.style-scope:nth-child(13) > a:nth-child(1) > tp-yt-paper-item:nth-child(1) > div:nth-child(2) > yt-formatted-string:nth-child(1)"
        print('choose the language or location you like to use.')
        selector_en=page.locator(selector_en_path)
        await selector_en.click()
        # page.click(selector_en)

        # print(page.text_content('//*[@id="label"]'))
        # if page.text_content(selector_en)=="English (US)":
        #     return True
        # else:
        #     return False
        return True
    except TimeoutError:
        return False
# fix google account verify


async def verify(self, page):
    try:

        while True:
            await page.locator('#confirm-button > div:nth-child(2)').click()
            await page.goto("https://accounts.google.com/signin/v2/identifier?service=youtube&uilel=3&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26app%3Ddesktop%26next%3Dhttps%253A%252F%252Fstudio.youtube.com%252Freauth%26feature%3Dreauth%26authuser%3D2%26skip_identity_prompt%3Dtrue&hl=en&authuser=2&rart=ANgoxcfF1TrrQp5lP5ySTmlJmdnwuMbSDi81WlN2aDXRgvpTnD1cv0nXHlRcMz6yv6hnqfERyjXMCgJqa8thKIAqVqatu9kTtA&flowName=GlifWebSignIn&flowEntry=ServiceLogin")
            await page.locator("#identifierId").click()
            await page.fill("#identifierId", self.username)
            await page.locator(
                ".VfPpkd-LgbsSe-OWXEXe-k8QpJ > span:nth-child(4)").click()
            time.sleep(3)
            await page.fill(
                "#password > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > input:nth-child(1)", self.password)
            await page.locator(
                ".VfPpkd-LgbsSe-OWXEXe-k8QpJ > span:nth-child(4)").click()
            time.sleep(60)

    except:
        time.sleep(1)
    # x_path = '//*[@id="textbox"]'
    # if page.wait_for_selector(x_path):
        # break        


async def wait_for_processing(page, process):
    page = page
    if process == True:
        # Wait for processing to complete
        progress_label = await page.wait_for_selector(
            "span.progress-label")
        pattern = re.compile(
            r"(finished processing)|(processing hd.*)|(check.*)")
        current_progress = await progress_label.get_attribute("textContent")
        last_progress = None
        while not pattern.match(current_progress.lower()):
            if last_progress != current_progress:
                logging.info(f'Current progress: {current_progress}')
            last_progress = current_progress
            sleep(5)
            current_progress = await progress_label.get_attribute("textContent")
    else:
        while True:

            x_path = "//span[@class='progress-label style-scope ytcp-video-upload-progress']"
            # TypeError: 'WebElement' object  is not subscriptable
            upload_progress = await page.locator(
                '[class="progress-label style-scope ytcp-video-upload-progress"]').all_text_contents()

            # innerhtml = page.locator(x_path).get_attribute('innerHTML')
            # if re.match(r"\D \.\.\. \D", innerhtml) or re.match(r"^[^\.]+$", innerhtml):
            #     break
            upload_progress=' '.join(upload_progress)
            if not '%' in upload_progress.lower():
                break
            elif 'complete' in upload_progress.lower():
                break

async def setscheduletime(page, publish_date: datetime):
    hour_to_post, date_to_post, publish_date_hour=hour_and_date(
        publish_date)
    date_to_post=publish_date.strftime("%b %d, %Y")
    hour_xpath=get_hour_xpath(hour_to_post)
    # Clicking in schedule video
    print('click schedule')
    await page.locator(
        '//html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-review/div[2]/div[1]/ytcp-video-visibility-select/div[2]/tp-yt-paper-radio-button/div[1]/div[1]').click()
    sleep(1)
    # Writing date
    print('click date')
    await page.locator('#datepicker-trigger > ytcp-dropdown-trigger:nth-child(1) > div:nth-child(2) > div:nth-child(4)').click()

    # page.locator(
        # '//html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-review/div[2]/div[1]/ytcp-video-visibility-select/div[2]/ytcp-visibility-scheduler/div[1]/ytcp-datetime-picker/div/ytcp-text-dropdown-trigger[1]/ytcp-dropdown-trigger/div/div[3]').click()
    sleep(1)
    page.locator('//*[@id="input-4"]')
    
    # page.locator(
        # '//html/body/ytcp-date-picker/tp-yt-paper-dialog/div/form/tp-yt-paper-input/tp-yt-paper-input-container/div[2]/div/iron-input/input').click()
    await page.keyboard.press("Control+KeyA")
    await page.keyboard.type(date_to_post)
    await page.keyboard.press("Enter")

    sleep(1)
    print('click hour')
# #input-1
    try:
        await page.locator(
            '#input-1').click()
        sleep(1)
        await page.locator(hour_xpath).click()
    except:
        # input_hour=page.wait_for_selector(
            # 'input.tp-yt-paper-input').click()
        print('no hour input found')
    await page.keyboard.press("Control+KeyA")
    await page.keyboard.type(hour_to_post)
    await page.keyboard.press("Enter")

    sleep(1)


def hour_and_date( now_date_hour):
    # now_date_hour += datetime.timedelta(seconds=TIME_BETWEEN_POSTS)
    hour_to_post=now_date_hour.strftime('%H:%M')
    hour, minutes=hour_to_post.split(
        ':')[0], int(hour_to_post.split(':')[1])
    setting_minutes=minutes//15
    minutes=setting_minutes * 15
    if minutes == 0:
        minutes='00'
    hour_to_post=f'{hour}:{minutes}'
    date_to_post=now_date_hour.strftime('%d/%m/%Y')
    return hour_to_post, date_to_post, now_date_hour

def get_hour_xpath( input_hour):
    hour_xpath=dict()
    xpath_time=0
    for hour in range(24):
        if hour < 10 and hour >= 0:
            hour=f'0{hour}'
        for minute in range(0, 46, 15):
            if minute == 0:
                minute='00'
            xpath_time += 1
            hour_xpath.update(
                {f'{hour}:{minute}': f'//html/body/ytcp-time-of-day-picker/tp-yt-paper-dialog/tp-yt-paper-listbox/tp-yt-paper-item[{xpath_time}]'})
    return hour_xpath[input_hour]

def _set_time_cssSelector(page, publish_date: datetime):
    # Start time scheduling
    page.locator("SCHEDULE").click()

    # Open date_picker
    page.locator(
        "#datepicker-trigger > ytcp-dropdown-trigger:nth-child(1)").click()

    date_input=page.locator(
        "input.tp-yt-paper-input").click()
    date_input.clear()
    # Transform date into required format: Mar 19, 2021
    page.keyboard.press("Control+KeyA")
    page.keyboard.type(publish_date.strftime("%b %d, %Y"))
    page.keyboard.press("KeyReturn")
    # Open time_picker
    page.locator(
        "#time-of-day-trigger > ytcp-dropdown-trigger:nth-child(1) > div:nth-child(2)"
    ).click()

    time_list=page.locator(
        "tp-yt-paper-item.tp-yt-paper-item")
    # Transform time into required format: 8:15 PM
    time_str=publish_date.strftime("%I:%M %p").strip("0")

    time=[time for time in time_list[2:] if time.text == time_str][0]
    time.click()

def _set_basic_settings(page, title: str, description: str, thumbnail_path: str=None):

    title_input=page.wait_for_selector(
                '//ytcp-mention-textbox[@label="Title"]//div[@id="textbox"]'                )

    # Input meta data (title, description, etc ... )
    description_input=page.wait_for_selector(
        '//ytcp-mention-textbox[@label="Description"]//div[@id="textbox"]'
    )
    thumbnail_input=page.wait_for_selector(
        "input#file-loader"
    )

    title_input.clear()
    title_input.send_keys(title)
    description_input.send_keys(description)
    if thumbnail_path:
        thumbnail_input.send_keys(thumbnail_path)


def __is_videos_available(self,page):
    # if there are no videos to be deleted, this element should be visible
    # if not visible throw error, and proceed to delete more videos
    try:
        page.wait_for_selector(
            "//ytcp-video-section-content[@id='video-list']/div/div[2]/div")
        # return True, there are no more video to be deleted
        return True
    except:
        return False


def waitfordone(page):
    # wait until video uploads
    # uploading progress text contains ": " - Timp ramas/Remaining time: 3 minutes.
    # we wait until ': ' is removed, so we know the text has changed and video has entered processing stage
    uploading_progress_text=page.locator(UPLOADING_PROGRESS_SELECTOR).text_content()
    while ': ' in uploading_progress_text:
        sleep(5)
        page.locator(UPLOADING_PROGRESS_SELECTOR).text_content()

