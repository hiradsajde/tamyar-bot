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
from database.models import engine
from database.view_models import create_or_get_user, is_spam, get_daily_download , create_request, get_request
from utils.definitions import is_participant, check_output , ytdlp_sentence , is_joined_sponsers
from hurry.filesize import size
from dotenv import load_dotenv
from utils.config import config
from urllib.parse import urlparse, parse_qs
from time import time 
import asyncio 

def main():
    @client.on(events.NewMessage(func=lambda e: e.is_private))
    async def text_event_handler(event):
            create_or_get_user(event.chat_id)
            if is_spam(event.chat_id , config["SPAM_DURATION"]):
                return
            if not await is_joined_sponsers(event,"send"): 
                return 
            match(event.text):
                case "/start": 
                    await event.reply(i18n.t("sentence.welcome"))
                case _ :
                    if re.match(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)",event.text):
                        if re.match(r"^(?:(?:https?:)?\/\/)?(?:(?:(?:www|m(?:usic)?)\.)?youtu(?:\.be|be\.com)\/(?:shorts\/|live\/|v\/|e(?:mbed)?\/|watch(?:\/|\?(?:\S+=\S+&)*v=)|oembed\?url=https?%3A\/\/(?:www|m(?:usic)?)\.youtube\.com\/watch\?(?:\S+=\S+&)*v%3D|attribution_link\?(?:\S+=\S+&)*u=(?:\/|%2F)watch(?:\?|%3F)v(?:=|%3D))?|www\.youtube-nocookie\.com\/embed\/)([\w-]{11})[\?&#]?\S*$",event.text):
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
                                captured_id = parsed_url.path.split("/")[-1]
                            thumb_name = f"./downloads/{str(event.chat_id) + str(time())}"
                            try:
                                proxy_handler = f"--proxy {config.get('PROXY_TYPE')}://{config.get('PROXY_IP')}:{config.get('PROXY_PORT')}" if config.get('PROXY_TYPE') else None
                                out = ["yt-dlp","--cookies","./cookies.txt","-s","--print","%(.{title,description,formats,thumbnails,duration})#j","--convert-thumbnails","jpg", "--write-thumbnail", "-o" , f"{thumb_name}.%(ext)s","--no-simulate","--skip-download",f"https://youtu.be/{captured_id}"]
                                if proxy_handler: 
                                    flag , proxy = proxy_handler.split(" ")
                                    out.insert(1, flag)
                                    out.insert(2, proxy)
                                async with client.action(event.chat_id , "photo"):
                                    dl_info_json = await check_output(*out)
                            except Exception as e:
                                print(e) 
                                await loading.delete()
                                await event.reply(i18n.t("sentence.error_happens"))
                                return
                            if not os.path.isfile(f"{thumb_name}.jpg"):
                                thumb_name = "./assets/nothumbnail"
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
                            dl_info_text_url = f"https://youtu.be/{captured_id}"
                            
                            if(len(dl_info_text_description) >= 49):
                                dl_info_text_description += "..."
                            dl_info_text = "🖊️ <u>" + dl_info["title"] + "</u>" + "\n" +\
                            "<i>" + dl_info_text_description + "</i>\n" +\
                            "🔗 " + dl_info_text_url + "\n" +\
                            "<b>👇 " + i18n.t("sentence.choose_format") + "</b>" + "\n" +\
                            config.get("MAIN_MENTION")
                            dl_info_thumbnail_id = -1 
                            create_request(chat_id=event.chat_id,title=dl_info["title"],description=dl_info_text_description,file_id=captured_id,duration=dl_info["duration"],thumbnail=thumb_name)
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
                                if dl_info_format["ext"] == "m4a":
                                    file_size = size(dl_info_format["filesize"])
                                else :
                                    file_size = size(dl_info_format["filesize"] + max_audio_size)
                                icon = "" 
                                match(dl_info_format["ext"]):
                                    case "mp4":
                                        icon = "📹" 
                                    case "m4a":
                                        icon = "🔉"
                                dl_info_formats_buttons[i//2].append(
                                    Button.inline(icon + " " + dl_info_format["format_note"] + " - " + file_size, captured_id + "~" + dl_info_format["format_id"] + "~" + dl_info_format["ext"])
                                )
                            await loading.delete()
                            await event.reply(
                                dl_info_text,
                                file= await client.upload_file(f"{thumb_name}.jpg"),
                                parse_mode= "html",
                                buttons= dl_info_formats_buttons
                            )
                            os.remove(f"{thumb_name}.jpg")
                        else :
                            await event.reply(i18n.t("sentence.not_supported"))
                    else :
                        await event.reply(i18n.t("sentence.invalid_url"),parse_mode="html")
    @client.on(events.CallbackQuery(func=lambda e: e.is_private))
    async def callback_event_handler(event):
            if is_spam(event.chat_id , config["SPAM_DURATION"]):
                return
            data = event.data.decode("utf-8")
            match(data):
                case "is_joined":
                    if not await is_joined_sponsers(event,"answer"): 
                        return
                    else : 
                        await event.edit(i18n.t("sentence.welcome"))
                case _ :
                    file_id , format_id, ext = data.split("~")
                    file_info = get_request(file_id,event.chat_id)
                    message = await event.get_message()
                    caption = "🖊️ <u>" + file_info.title + "</u>" + "\n" +\
                        "<i>" + file_info.description + "</i>\n" +\
                        "🔗 https://youtu.be/" + file_info.file_id + "\n" +\
                        "<b>" + i18n.t("sentence.loading") + "</b>" + "\n" +\
                        config.get("MAIN_MENTION")
                    await event.edit(caption,parse_mode="html")
                    ytd = youtube_handler(
                        message.chat_id,
                        message.id,
                        file_id,
                        format_id,
                        ext
                    )
                    loop = asyncio.get_event_loop()
                    loop.create_task(ytd.do())
if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    load_dotenv()
    main()
    client.start(bot_token = os.getenv("BOT_TOKEN"))
    client.run_until_disconnected()