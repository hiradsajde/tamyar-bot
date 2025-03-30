from sqlmodel import SQLModel, Session, select 
from database.models import engine , User, Downlaod
from time import time 

with Session(engine) as session: 
    def create_or_get_user(chat_id):
        statement = select(User).where(User.chat_id == chat_id) 
        user = session.exec(statement).first()
        if user == None: 
            session.add(User(chat_id=chat_id, lastmessage=round(time(),2)))
            session.commit()
        return user 
    def is_spam(chat_id,delay): 
        user = create_or_get_user(chat_id)
        last_message = user.last_message
        user.last_message = round(time(),2)
        session.add(user)
        session.commit()
        if time() - last_message < int(delay) and time() - user.created_at > int(delay):
            return True 
        return False
    def create_download(chat_id , size, url):
        session.add(Downlaod(chat_id=chat_id,size=size,url=url))
        session.commit() 
    def get_daily_download(chat_id): 
        statement = select(Downlaod).where(Downlaod.time > time() - 60 * 60 * 24).where(Downlaod.chat_id == chat_id)
        downloads = session.exec(statement).all()
        total = 0
        for download in downloads:
            total += download.size
        return total