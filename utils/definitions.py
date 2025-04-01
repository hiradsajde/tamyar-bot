import i18n
import asyncio
from telethon import errors
from utils.config import client, config
from telethon import Button

async def is_participant(channel, user) -> bool:
    try:
        await client.get_permissions(channel, user)
        return True
    except errors.UserNotParticipantError:
        return False

async def is_joined_sponsers(event, mode):
    channels = []
    get_channels = config["CHANNELS"].split("~")
    for get_channel in get_channels:
        name , url , id = get_channel.split("|")
        channels.append({
                "name" : name,
                "url": url,
                "id" : int(id),
        })
    channels_buttons = [] 
    for channel in channels: 
        channels_buttons.append(
            [Button.url(channel["name"], channel["url"])]
        )
    channels_buttons.append(
        [Button.inline(i18n.t("button.joined"), "is_joined")]
    )
    for channel in channels:
        if not await is_participant(channel["id"],event.chat_id): 
            match(mode):
                case "send":
                    await event.reply(i18n.t("sentence.join_sponsers"),buttons=channels_buttons)
                case "answer": 
                    await event.answer(i18n.t("sentence.not_joined_sponsers"))
            return False
    return True
    
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