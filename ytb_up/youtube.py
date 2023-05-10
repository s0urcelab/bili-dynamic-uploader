import os
import sys
import json
import logging
from time import sleep
from datetime import datetime, date, timedelta
from .constants import *
from .exceptions import *
from .utils import *
from .login import *
from playwright.async_api import async_playwright
class YoutubeUpload:
    def __init__(
        self,
        root_profile_directory: str = "",
        proxy_option: str = "",
        timeout: int = 3,
        headless: bool = True,
        channel_cookies: str = "",
        recording: bool = False,
        logger: logging.Logger = None,
    ) -> None:
        self.timeout = timeout
        self.log = logger
        self.channel_cookies = channel_cookies
        self.root_profile_directory = root_profile_directory
        self.proxy_option = proxy_option
        self.headless = headless
        self.recording = recording
        self._playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        self._playwright = await self._start_playwright()
        browserLaunchOption = {
            "headless": self.headless,
            "timeout": 300000,
        }
        if self.proxy_option:
            browserLaunchOption['proxy'] = {"server": self.proxy_option}
            self.log.debug(f'Firefox with proxy: "{self.proxy_option}"')
            
        self.browser = await self._start_browser("firefox", **browserLaunchOption)
        self.log.debug(f'Firefox is now running in "{"Headless" if self.headless else "Normal"}" mode.')
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # await self.context.close()
        await self.browser.close()
        await self._playwright.stop()
        self.log.debug('Firefox is now closed.')

    async def click_next(self, page) -> None:
        await page.locator(NEXT_BUTTON).click()
        sleep(self.timeout)

    async def not_uploaded(self, page) -> bool:
        s = await page.locator(STATUS_CONTAINER).text_content()
        return s.find(UPLOADED) != -1

    async def upload(
        self,
        video_path: str = "",
        title: str = "",
        description: str = "",
        thumbnail: str = "",
        publish_policy: int = 0,
        # mode a:release_offset exist,publish_data exist will take date value as a starting date to schedule videos
        # mode b:release_offset not exist, publishdate exist , schedule to this specific date
        # mode c:release_offset not exist, publishdate not exist,daily count to increment schedule from tomorrow
        # mode d: offset exist, publish date not exist, daily count to increment with specific offset schedule from tomorrow
        release_offset: str = '0-1',
        publish_date: datetime = datetime(
            date.today().year,  date.today().month,  date.today().day, 10, 15),
        tags: list = [],
        wait_upload_complete: bool = True
    ) -> str:
        """Uploads a video to YouTube.
        Returns if the video was uploaded and the video id.
        """
        self.context = await self.browser.new_context()
        
        if self.channel_cookies:
            self.log.debug(f'Load cookies: {self.channel_cookies}')

            await self.context.clear_cookies()

            await self.context.add_cookies(
                json.load(
                    open(
                        self.channel_cookies,
                        'r'
                    )
                )
            )
        
        if not video_path:
            raise FileNotFoundError(
                f'Cannot find video in path: "{video_path}"')
            
        page = await self.context.new_page()

        # if self.channel_cookies:
        #     self.log.debug(f'Load cookies: {self.channel_cookies}')

        #     await self.context.clear_cookies()

        #     await self.context.add_cookies(
        #         json.load(
        #             open(
        #                 self.channel_cookies,
        #                 'r'
        #             )
        #         )
        #     )
        #     # login_using_cookie_file(self,self.channel_cookies,page)

            # await page.reload()
            
        await page.goto(YOUTUBE_URL, timeout=300000)
        islogin = await confirm_logged_in(page)
        self.log.debug(
            f'Checking login status: {"PASS" if islogin else "FAILED"}')

        if not islogin:
            self.log.debug('Try to load cookie files')
            await self.context.clear_cookies()

            await self.context.add_cookies(
                json.load(
                    open(
                        self.channel_cookies,
                        'r'
                    )
                )
            )

            self.log.debug('Success load cookie files')
            await page.goto(YOUTUBE_URL, timeout=30000)
            self.log.debug('Start to check login status')

            islogin = await confirm_logged_in(page)

            # https://github.com/xtekky/google-login-bypass/blob/main/login.py

        # self.log.debug('Start change locale to EN')

        # await set_channel_language_english(page)
        # self.log.debug('Finish change locale to EN')
        
        # 开始上传
        await page.goto(YOUTUBE_UPLOAD_URL, timeout=300000)
        # sleep(self.timeout)
        
        has_upload_modal = await page.locator(UPLOAD_DIALOG_MODAL).count()
        if not has_upload_modal:
            raise RuntimeError('未识别到上传弹窗')
        
        self.log.debug('Found Upload Modal')

        self.log.debug(f'Trying to upload "{video_path}"...')
        if os.path.exists(get_path(video_path)):
            page.locator(
                INPUT_FILE_VIDEO)
            await page.set_input_files(INPUT_FILE_VIDEO, get_path(video_path))
        
        sleep(self.timeout)
        
        # textbox = page.locator(TEXTBOX)
    #     <h1 slot="primary-header" id="dialog-title" class="style-scope ytcp-confirmation-dialog">
    #   Verify it's you
    # </h1>

        self.log.debug(f'Detecting verify...')
        try:
            hint = await page.locator('#dialog-title').text_content()
            if '验证是您本人在操作' in hint:
                # fix google account verify
                raise YoutubeUploadError('触发Youtube风控，终止本次任务')
                # await page.close()

                # await page.click('text=Login')
                # time.sleep(60)
                # await page.locator('#confirm-button > div:nth-child(2)').click()
        except:
            self.log.debug(f"Detect PASS")

        hint = await page.locator('div.error-short.style-scope.ytcp-uploads-dialog').text_content()
        if '已达到每日上传数上限' in hint:
            # try:
            # <div class="error-short style-scope ytcp-uploads-dialog">Daily upload limit reached</div>

            # daylimit=await self.page.is_visible(ERROR_SHORT_XPATH)
            # self.close()

            raise YoutubeUploadError('达到每日上传数上限，终止本次任务')
            # if daylimit:
            # self.close()


        # get file name (default) title
        # title=title if title else page.locator(TEXTBOX).text_content()
        # print(title)
        sleep(self.timeout)
        
        if len(title) > TITLE_COUNTER:
            self.log.debug(
                f"Title was not set due to exceeding the maximum allowed characters ({len(title)}/{TITLE_COUNTER})")
            title = title[:TITLE_COUNTER-1]

        # TITLE
        self.log.debug(f'Trying to set "{title}" as title...')
        
        titlecontainer = page.locator(TEXTBOX)
        await titlecontainer.click()
        await page.keyboard.press("Backspace")
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.press("Delete")

        await page.keyboard.type(title)

        if description:
            if len(description) > DESCRIPTION_COUNTER:
                self.log.debug(
                    f"Description was not set due to exceeding the maximum allowed characters ({len(description)}/{DESCRIPTION_COUNTER})"
                )
                description = description[:4888]

            self.log.debug(f'Trying to set "{description}" as description...')
            self.log.debug('click description field to input')
            await page.locator(DESCRIPTION_CONTAINER).click()
            self.log.debug('clear existing description')
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            self.log.debug('filling new description')

            await page.keyboard.type(description)

        need_set_thum = await page.locator(INPUT_FILE_THUMBNAIL).count()
        if thumbnail and need_set_thum:
            self.log.debug(f'Trying to set "{thumbnail}" as thumbnail...')
            if os.path.exists(get_path(thumbnail)):
                await page.locator(INPUT_FILE_THUMBNAIL).set_input_files(get_path(thumbnail))
            else:
                if os.path.exists(thumbnail.encode('utf-8')):
                    # print('thumbnail found', thumbnail)
                    await page.locator(INPUT_FILE_THUMBNAIL).set_input_files(thumbnail.encode('utf-8'))
            sleep(self.timeout)
        # try:
        #     self.log.debug('Trying to set video to "Not made for kids"...')

        #     kids_section=page.locator(NOT_MADE_FOR_KIDS_LABEL)
        #     await page.locator(NOT_MADE_FOR_KIDS_RADIO_LABEL).click()
        #     sleep(self.timeout)
        #     print('not made for kids task done')
        # except:
        #     print('failed to set not made for kids')
        if tags and (len(tags) > 0):
            self.log.debug('Tags:', tags)
            if type(tags) == list:
                tags = ",".join(str(tag) for tag in tags)
                tags = tags[:500]
            else:
                tags = tags
            self.log.debug('Overwrite prefined channel tags', tags)
            if len(tags) > TAGS_COUNTER:
                self.log.debug(
                    f"Tags were not set due to exceeding the maximum allowed characters ({len(tags)}/{TAGS_COUNTER})")
                tags = tags[:TAGS_COUNTER]
            self.log.debug('Click show more button')
            sleep(self.timeout)
            await page.locator(MORE_OPTIONS_CONTAINER).click()

            self.log.debug(f'Trying to set "{tags}" as tags...')
            await page.locator(TAGS_CONTAINER).locator(TEXT_INPUT).click()
            self.log.debug('Clear existing tags')
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            self.log.debug('Filling new tags')
            await page.keyboard.type(tags)


        if wait_upload_complete:
            await wait_for_processing(page, process=False)
            self.log.debug('Uploading progress check...')
        # if "complete" in page.locator(".progress-label").text_content():

        # sometimes you have 4 tabs instead of 3
        # this handles both cases
        for _ in range(3):
            try:
                await self.click_next(page)
                self.log.debug('Click "Next"...')
            except:
                self.log.debug('Click "Next" failed.')
        if not publish_policy in [0, 1, 2]:
            publish_policy = 0
        if publish_policy == 0:
            self.log.debug("Trying to set video visibility to private...")

            public_main_button = page.locator(PRIVATE_BUTTON)
            await page.locator(PRIVATE_RADIO_LABEL).click()
        elif publish_policy == 1:
            self.log.debug("Trying to set video visibility to public...")

            public_main_button = page.locator(PUBLIC_BUTTON)
            await page.locator(PUBLIC_RADIO_LABEL).click()
        else:
            # mode a:release_offset exist,publish_data exist will take date value as a starting date to schedule videos
            # mode b:release_offset not exist, publishdate exist , schedule to this specific date
            # mode c:release_offset not exist, publishdate not exist,daily count to increment schedule from tomorrow
            # mode d: offset exist, publish date not exist, daily count to increment with specific offset schedule from tomorrow
            # print('date', type(publish_date), publish_date)
            if type(publish_date) == str:
                publish_date = datetime.fromisoformat(publish_date)
            if release_offset and not release_offset == "0-1":
                self.log.debug('mode a sta', release_offset)
                if not int(release_offset.split('-')[0]) == 0:
                    offset = timedelta(months=int(release_offset.split(
                        '-')[0]), days=int(release_offset.split('-')[-1]))
                else:
                    offset = timedelta(days=1)
                if publish_date is None:
                    publish_date = datetime(
                        date.today().year,  date.today().month,  date.today().day, 10, 15)
                else:
                    publish_date += offset

            else:
                if publish_date is None:
                    publish_date = datetime(
                        date.today().year,  date.today().month,  date.today().day, 10, 15)
                    offset = timedelta(days=1)
                else:
                    publish_date = publish_date
                # dailycount=4

                # release_offset=str(int(start_index/30))+'-'+str(int(start_index)/int(setting['dailycount']))

            self.log.debug(
                f"Trying to set video schedule time...{publish_date}")

            await setscheduletime(page, publish_date)
            # set_time_cssSelector(page,publish_date)
        self.log.debug('Publish setting task done')
        video_id = await self.get_video_id(page)
        # option 1 to check final upload status
        if wait_upload_complete:
            self.log.debug('Check is upload finished')
            while await self.not_uploaded(page):
                self.log.debug('Still uploading...')
                sleep(1)

        self.log.debug('Click Done button')
        done_button = page.locator(DONE_BUTTON)
        if await done_button.get_attribute("aria-disabled") == "true":
            error_message = await page.locator(ERROR_CONTAINER).text_content()
            raise Exception(error_message)

        await done_button.click()

        sleep(5)
        
        # 上传完成
        self.log.debug("Upload is complete")
        await self.context.close()
        # await page.close()
        # await self.close()
        # page.locator("#close-icon-button > tp-yt-iron-icon:nth-child(1)").click()
        # print(page.expect_popup().locator("#html-body > ytcp-uploads-still-processing-dialog:nth-child(39)"))
        # page.wait_for_selector("ytcp-dialog.ytcp-uploads-still-processing-dialog > tp-yt-paper-dialog:nth-child(1)")
        # page.locator("ytcp-button.ytcp-uploads-still-processing-dialog > div:nth-child(2)").click()
        return video_id

    async def get_video_id(self, page) -> Optional[str]:
        try:
            video_url_container = page.locator(
                VIDEO_URL_CONTAINER)
            video_url_element = video_url_container.locator(
                VIDEO_URL_ELEMENT
            )

            video_id = await video_url_element.get_attribute(HREF)
            video_id = video_id.split("/")[-1]
            return video_id
        except:
            raise Exception('Video id not found.')

    # @staticmethod
    async def _start_playwright(self):
        #  sync_playwright().start()
        return await async_playwright().start()

    async def _start_browser(self, browsertype: str, **kwargs):
        if browsertype == "chromium":
            return await self._playwright.chromium.launch(**kwargs)

        if browsertype == "firefox":
            return await self._playwright.firefox.launch(**kwargs)
            # if self.recording:
            #     return await self._playwright.firefox.launch(record_video_dir=os.path.abspath('')+os.sep+"screen-recording", **kwargs)
            # else:
            #     return await self._playwright.firefox.launch( **kwargs)

        if browsertype == "webkit":
            return await self._playwright.webkit.launch(**kwargs)

        raise RuntimeError(
            "You have to select either 'chromium', 'firefox', or 'webkit' as browser.")

