import os
import time 
import random
import subprocess
from glob import glob
from utils.config import client
from utils.translation import i18n
from database.view_models import create_download , get_request
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from utils.definitions import ytdlp_sentence
from utils.config import config 
import asyncio

class youtube_handler :
    def __init__(self , chat_id , message_id , file_id , format_id, ext):
        self.file_id = file_id
        self.format_id = format_id 
        self.chat_id = chat_id 
        self.message_id = message_id
        self.ext = ext 
        self.name = f"{str(int(time.time()))}{random.randrange(100000000,999999999)}"
        self.file_info = get_request(self.file_id, self.chat_id)
    async def get_file(self):
        url = f"https://youtu.be/{self.file_id}"
        proxy_handler = f"--proxy {config.get('PROXY_TYPE')}://{config.get('PROXY_IP')}:{config.get('PROXY_PORT')}" if config.get('PROXY_TYPE') != None else " "
        if self.ext == "m4a": 
            out = ["yt-dlp","--write-thumbnail","--convert-thumbnails","jpg","--cookies","./cookies.txt","-o",f"./downloads/{self.name}/{self.file_info.title}.%(ext)s","-f",self.format_id,"--add-metadata","--embed-thumbnail",url]
        else : 
            out = ["yt-dlp","--write-thumbnail","--convert-thumbnails","jpg","--cookies","./cookies.txt","-o",f"./downloads/{self.name}/{self.file_info.title}.%(ext)s","-f",f"{self.format_id}+bestaudio","--audio-multistreams","--video-multistreams","-S","res,ext:mp4","--add-metadata" , "--embed-thumbnail",url]
        if proxy_handler: 
            flag , proxy = proxy_handler.split(" ")
            out.insert(1, flag)
            out.insert(2, proxy)
        proc = subprocess.Popen(out, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        line = 0
        result = [[]]
        last_complition_percentage = -1
        channel = await client.get_entity(self.chat_id)
        messages = await client.get_messages(channel, ids=[self.message_id])

        for c in iter(lambda: proc.stdout.read(1), b""):
            char = c.decode("utf-8",errors="ignore") 
            if char == "[":
                result[line].insert(0 , "[")
                result[line] = "".join(result[line])
                if "[youtube]" in result[line]:
                    c_line_data = result[line] 
                    sentence = ytdlp_sentence(c_line_data)
                    caption = "🖊️ <u>" + self.file_info.title + "</u>" + "\n" +\
                        "<i>" + self.file_info.description + "</i>\n" +\
                        "🔗 https://youtu.be/" + self.file_info.file_id + "\n" +\
                        "<b>" + str(sentence) + "</b> " + "\n" +\
                        config.get("MAIN_MENTION")
                    for message in messages:
                        await message.edit(caption,parse_mode="html")
                                
                if "[download]" in result[line] and "%" in result[line]:
                    c_line_data = result[line].split("[download]")[1].split("at")[0].split("of")
                    complition_percentage , _ = float(c_line_data[0].strip().split("%")[0]) , c_line_data[1].strip()
                    if last_complition_percentage != int(complition_percentage):
                        loadbar = "■" * int(complition_percentage // 10) + "□" * (10 - int(complition_percentage // 10))
                        caption = "🖊️ <u>" + self.file_info.title + "</u>" + "\n" +\
                        "<i>" + self.file_info.description + "</i>\n" +\
                        "🔗 https://youtu.be/" + self.file_info.file_id + "\n" +\
                        "<b>" + i18n.t("sentence.downloading") + "</b>" + "\n" +\
                        "✔️ <b>" + format(int(complition_percentage), '03d') + "%</b> " + loadbar + "\n" +\
                        config.get("MAIN_MENTION")
                        last_complition_percentage = int(complition_percentage)
                        if complition_percentage == 100 :
                            files = self.get_target_files(self.ext)
                            while len(files) == 0 :
                                files = self.get_target_files(self.ext)
                                await asyncio.sleep(0.1)
                            for file in files:
                                last_complition_percentage = -1
                                caption = "🖊️ <u>" + self.file_info.title + "</u>" + "\n" +\
                                          "<i>" + self.file_info.description + "</i>\n" +\
                                          "🔗 https://youtu.be/" + self.file_info.file_id + "\n" +\
                                          config.get("MAIN_MENTION")
                                async def progress_callback(downloaded,total):
                                    nonlocal last_complition_percentage
                                    complition_percentage = int((downloaded/total)*100)
                                    if  last_complition_percentage != int(complition_percentage):
                                        last_complition_percentage = int(complition_percentage)
                                        loadbar = "■" * int(complition_percentage // 10) + "□" * (10 - int(complition_percentage // 10))
                                        caption = "🖊️ <u>" + self.file_info.title + "</u>" + "\n" +\
                                        "<i>" + self.file_info.description + "</i>\n" +\
                                        "🔗 https://youtu.be/" + self.file_info.file_id + "\n" +\
                                        "<b>" + i18n.t("sentence.uploading") + "</b> " + "\n" +\
                                        "✔️ <b>" + format(int(complition_percentage), '03d') + "%</b>" + loadbar + "\n" +\
                                        config.get("MAIN_MENTION")
                                        if complition_percentage == 100 :
                                            for message in messages:
                                                await message.delete()    
                                            create_download(chat_id=self.chat_id,size=total,url=url)

                                        else:
                                            for message in messages:
                                                await message.edit(caption,parse_mode="html")
                                thumb = f"./downloads/{self.name}/{self.file_info.title}.jpg"
                                for message in messages:
                                    if self.ext == "m4a": 
                                        message= await client.send_file(
                                            caption= caption,
                                            entity = message.chat_id,
                                            reply_to = message.reply_to.reply_to_msg_id, 
                                            file = file,
                                            progress_callback=progress_callback, 
                                            parse_mode="html", 
                                            attributes=(DocumentAttributeAudio(self.file_info.duration),)
                                        )
                                        if message:
                                            self.delete()
                                    else:
                                        async with client.action(message.chat_id, "video"):
                                            message = await client.send_file(
                                                caption= caption,
                                                entity = message.chat_id,
                                                reply_to = message.reply_to.reply_to_msg_id, 
                                                file = file,
                                                thumb = thumb,
                                                progress_callback=progress_callback, 
                                                parse_mode="html", 
                                                attributes=(DocumentAttributeVideo(self.file_info.duration,0,0),)
                                            )
                                            if message:
                                                self.delete()
                        else :
                            for message in messages:
                                try:
                                    await message.edit(caption,parse_mode="html")
                                except Exception as e:
                                    continue
                result.append([])
                line += 1 
            else:
                result[line].append(char)
    def delete(self):
        files = self.get_files()
        for file in files :
            os.remove(file)
        if os.path.isdir(f"./downloads/{self.name}") : 
            os.rmdir(f"./downloads/{self.name}")
    def get_files(self):
        files = glob(f"./downloads/{self.name}/*") 
        return files
    def get_target_files(self,ext):
        files = [file_name for file_name in glob(f"./downloads/{self.name}/*.{ext}") if not (file_name.endswith(".part") or file_name.endswith(".jpg"))]
        return files
    async def do(self):
        try :
            await self.get_file()
        except Exception as e:
            self.delete()
            print(e)
            