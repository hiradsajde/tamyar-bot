import os 
import re
import i18n
import json
import subprocess
from utils.constants import types
from telethon import Button , events, types
from utils.handlers import youtube_handler
from utils.config import client
from utils.translation import i18n
from sqlmodel import SQLModel 
from database.models import engine , User
from database.view_models import create_or_get_user, is_spam, get_daily_download
from utils.definitions import is_participant
from hurry.filesize import size
from dotenv import load_dotenv
from utils.config import config
from urllib.parse import urlparse, parse_qs
import asyncio 

def main():
    @client.on(events.NewMessage(func=lambda e: e.is_private))
    async def text_event_handler(event):
            user = create_or_get_user(event.chat_id)
            if is_spam(event.chat_id , config["SPAM_DURATION"]):
                return
            
            channels = []
            get_channels = config["CHANNELS"].split("~")
            for get_channel in get_channels:
                name , url , id = get_channel.split("|")
                channels.append({
                        "name" : name,
                        "url": url,
                        "id" : id,                       "id": -1001594111683, 
                })

            channels_buttons = [] 
            for channel in channels: 
                channels_buttons.append(
                    [Button.url(channel["name"], channel["url"])]
                )
            for channel in channels:
                if not await is_participant(channel["id"],event.chat_id): 
                    await event.reply(i18n.t("sentence.join_sponsers"),buttons=channels_buttons)
                    return
            match(event.text):
                case "/start": 
                    await event.reply(i18n.t("sentence.welcome"))
                case _ :
                    if re.match(r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?",event.text):
                        user_daily_download = get_daily_download(event.chat_id)
                        if user_daily_download > int(config.get("DAILY_DOWNLOAD_LIMIT")): 
                            await event.reply(i18n.t("sentence.max_limit_excited"))
                            return
                        loading = await event.reply("🌕")
                        parsed_url = urlparse(event.text)
                        captured_id = parse_qs(parsed_url.query).get('v')
                        if captured_id :
                            captured_id = captured_id[0]
                        else: 
                            captured_id = parsed_url.path
                        proxy_handler = f"--proxy {config.get('PROXY_TYPE')}://{config.get('PROXY_IP')}:{config.get('PROXY_PORT')}" if config.get('PROXY_TYPE') != None else ""
                        try:
                            dl_info_json = subprocess.check_output(["yt-dlp","--force-generic", *proxy_handler.split(" ") , "-j",f"https://youtu.be/{captured_id}"])
                        except Exception: 
                            loading.delete()
                            event.reply(i18n.t("sentence.error_happens"))
                        dl_info = json.loads(dl_info_json)
                        dl_info_formats_filter = filter(lambda f: (
                            (
                            (f["ext"] == "mp4" and f["video_ext"] == "mp4") or 
                            (f["ext"] == "m4a" and f["audio_ext"] == "m4a")
                            ) and (
                                f["protocol"] == "https"
                            ) and (
                                int(config.get("DAILY_DOWNLOAD_LIMIT")) - user_daily_download > int(f["filesize"]) if f["filesize"] != None else 0
                            )
                            ) , dl_info["formats"])
                        dl_info_text_description = dl_info["description"][:50]
                        dl_info_text_url = dl_info["webpage_url"].replace("https://www.youtube.com/watch?v=","https://youtu.be/")
                        if(len(dl_info_text_description) >= 49):
                            dl_info_text_description += "..."
                        dl_info_text = "🖊️ <u>" + dl_info["title"] + "</u>" + "\n" +\
                        "<i>" + dl_info_text_description + "</i>\n" +\
                        "🔗 " + dl_info_text_url + "\n" +\
                        "<b>👇 " + i18n.t("sentence.choose_format") + "</b>"
                        dl_info_thumbnail_id = -1 
                        while dl_info["thumbnails"][dl_info_thumbnail_id]["url"].split(".")[-1] != "jpg":
                            dl_info_thumbnail_id-=1
                        dl_info_formats_dict = {}
                        max_audio_size = 0
                        for dl_info_format in dl_info_formats_filter:
                            dl_info_formats_dict[dl_info_format["format_note"]] = dl_info_format
                            if dl_info_format["filesize"] > max_audio_size and dl_info_format["ext"] == "m4a":
                                max_audio_size = dl_info_format["filesize"]
                        dl_info_formats = dl_info_formats_dict.values()
                        if len(dl_info_formats) == 0 :
                            await event.reply(i18n.t("sentence.not_enough_credit"))
                            await loading.delete()
                            return
                        dl_info_formats_buttons = []
                        dl_info_format_buttons_lines = len(dl_info_formats) // 2
                        if len(dl_info_formats) % 2 != 0 :
                            dl_info_format_buttons_lines += 1
                        for _ in range(dl_info_format_buttons_lines):
                            dl_info_formats_buttons.append([]) 
                        for i , dl_info_format in enumerate(dl_info_formats):
                            icon = "" 
                            if dl_info_format["ext"] == "m4a":
                                file_size = size(dl_info_format["filesize"])
                            else :
                                file_size = size(dl_info_format["filesize"] + max_audio_size)
                            match(dl_info_format["ext"]):
                                case "mp4":
                                    icon = "📹" 
                                case "m4a":
                                    icon = "🔉"
                            dl_info_formats_buttons[i//2].append(
                                Button.inline(icon + " " + dl_info_format["format_note"] + " - " + file_size,  dl_info_text_url.replace("https://youtu.be/","") + "~" + dl_info_format["format_id"] + "~" + dl_info_format["ext"])
                            )
                        await loading.delete()
                        thumbnail = dl_info["thumbnails"][dl_info_thumbnail_id]["url"]
                        if thumbnail == None: 
                            thumbnail = "./assets/nothumbnail.png"
                        await event.reply(
                            dl_info_text,
                            file= thumbnail,
                            parse_mode= "html",
                            buttons= dl_info_formats_buttons
                        )
                    else :
                        await event.reply(i18n.t("sentence.not_supported"))
    @client.on(events.CallbackQuery(func=lambda e: e.is_private))
    async def callback_event_handler(event):
            if is_spam(event.chat_id , config["SPAM_DURATION"]):
                return
            message = await event.get_message()
            caption = "\n".join(message.text.split("\n")[:-1]) + "\n" + "**" +  i18n.t("sentence.loading") + "**"
            file_id , format_id, ext = event.data.decode("utf-8").split("~")
            title = "".join(message.text.split("\n")[0][1:]).replace("*","").strip()
            await event.edit(caption)
            ytd = youtube_handler(message.chat_id,message.id,f"https://youtu.be/{file_id}",title,format_id,ext)
            loop = asyncio.get_event_loop()
            loop.create_task(ytd.do())
if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    load_dotenv()
    main()
    client.start(bot_token = os.getenv("BOT_TOKEN"))
    client.run_until_disconnected()