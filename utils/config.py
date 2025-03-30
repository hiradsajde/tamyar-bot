
from dotenv import dotenv_values
from telethon import TelegramClient # type: ignore

default_env = {
    "SESSION_NAME" : "bot",
    "SPAM_DURATION" : "1"
}

config = {
    **default_env,
    **dotenv_values()
}
if config.get("PROXY_TYPE") != None:
    client = TelegramClient(
        config.get("SESSION_NAME"), 
        config.get("API_ID"), config.get("API_HASH"),
        proxy=(config.get("PROXY_TYPE"), config.get("PROXY_IP"),config.get("PROXY_PORT"))
    )
else :
    client = TelegramClient(
            config.get("SESSION_NAME"), 
            config.get("API_ID"), config.get("API_HASH"),
    )