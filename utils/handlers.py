import os
import time 
import random
import subprocess
import glob
import asyncio
import glob 
from utils.config import client
from utils.translation import i18n
from database.view_models import create_download
from utils.config import config 

class youtube_handler :
    def __init__(self , chat_id , message_id ,  url, title , format_id, ext):
        self.url = url 
        self.title = title
        self.format_id = format_id 
        self.chat_id = chat_id 
        self.message_id = message_id
        self.ext = ext 
        self.name = f"{str(int(time.time()))}{random.randrange(100000000,999999999)}"
    async def get_file(self):
        proxy_handler = f"--proxy {config.get('PROXY_TYPE')}://{config.get('PROXY_IP')}:{config.get('PROXY_PORT')}" if config.get('PROXY_TYPE') != None else ""
        if self.ext == "m4a":
            proc = subprocess.Popen(["yt-dlp",self.url,*proxy_handler.split(" "),"-o",f"./downloads/{self.name}/{self.title}.%(ext)s","-f",self.format_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else: 
            proc = subprocess.Popen(["yt-dlp",self.url,*proxy_handler.split(" "),"-o",f"./downloads/{self.name}/{self.title}.%(ext)s","-f",f"{self.format_id}+bestaudio","--audio-multistreams","--video-multistreams","-S","res,ext:mp4"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
                if "[download]" in result[line] and "%" in result[line]:
                    c_line_data = result[line].split("[download]")[1].split("at")[0].split("of")
                    complition_percentage , size = float(c_line_data[0].strip().split("%")[0]) , c_line_data[1].strip()
                    if last_complition_percentage != int(complition_percentage):
                        loadbar = "■" * int(complition_percentage // 10) + "□" * (10 - int(complition_percentage // 10))
                        for message in messages:
                            message_text = "\n".join(message.text.split("\n")[:-2]) + "\n" + i18n.t("sentence.downloading") + "\n" + "✔️ **" + format(int(complition_percentage), '03d') + "%** " + loadbar + "\n" + config.get("MAIN_MENTION")
                            await message.edit(message_text)
                        last_complition_percentage = int(complition_percentage)
                        if complition_percentage == 100 :
                            files = self.get_files()
                            for file in files:
                                message_text = "\n".join(message.text.split("\n")[:-2]) + "\n" + config.get("MAIN_MENTION")
                                last_complition_percentage = -1
                                async def progress_callback(downloaded,total):
                                    nonlocal last_complition_percentage
                                    complition_percentage = int((downloaded/total)*100)
                                    if  last_complition_percentage != int(complition_percentage):
                                        last_complition_percentage = int(complition_percentage)
                                        loadbar = "■" * int(complition_percentage // 10) + "□" * (10 - int(complition_percentage // 10))
                                        message_text = "\n".join(message.text.split("\n")[:-2]) + "\n" + i18n.t("sentence.uploading") + "\n" + f"✔️ **{format(int(complition_percentage), '03d')}%** "+ loadbar + "\n" + config.get("MAIN_MENTION")
                                        if complition_percentage == 100 :
                                            await message.delete()    
                                            create_download(chat_id=self.chat_id,size=total,url=self.url)

                                        else:
                                            await message.edit(message_text)
                                await client.send_file(
                                    caption= message_text,
                                    entity = message.chat_id,
                                    reply_to = message.reply_to.reply_to_msg_id, 
                                    file = file,
                                    progress_callback=progress_callback
                                )
                            self.delete()
                    await asyncio.sleep(0.5)
                result.append([])
                line += 1 
            else:
                result[line].append(char)
    def delete(self):
        files = self.get_files()
        if len(files) > 0:
            for file in files :
                os.remove(file)
            os.rmdir(f"./downloads/{self.name}/")
    def get_files(self):
        files = [file_name for file_name in glob.glob(f"./downloads/{self.name}/{self.title}.*") if not file_name.endswith(".part")]
        return files
    async def do(self):
        try :
            await self.get_file()
        except Exception as e:
            print(e)
            self.delete()