from telethon import errors
from utils.config import client

async def is_participant(channel, user) -> bool:
    try:
        await client.get_permissions(channel, user)
        return True
    except errors.UserNotParticipantError:
        return False
