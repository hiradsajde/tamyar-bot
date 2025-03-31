import i18n
import asyncio
from telethon import errors
from utils.config import client

async def is_participant(channel, user) -> bool:
    try:
        await client.get_permissions(channel, user)
        return True
    except errors.UserNotParticipantError:
        return False
    
async def check_output(*args, **kwargs):
    p = await asyncio.create_subprocess_exec(
        *args, 
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs,
    )   
    stdout_data, stderr_data = await p.communicate()
    if p.returncode == 0:
        return stdout_data
def ytdlp_sentence(data):
    if "Extracting URL" in data: 
        sentence = i18n.t("sentence.extracting_url")
    elif "Downloading webpage" in data: 
        sentence = i18n.t("sentence.downloading_webpage")
    elif "Downloading tv client config" in data: 
        sentence = i18n.t("sentence.downloading_tv_client_config")
    elif "Downloading player" in data: 
        sentence = i18n.t("sentence.downloading_player")
    elif "Downloading tv player" in data:
        sentence = i18n.t("sentence.downloadingـtvـplayer")
    else :
        sentence = ""
    return sentence