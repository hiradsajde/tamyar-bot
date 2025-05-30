from sqlmodel import SQLModel, Session, select 
from database.models import engine , User, Downlaod, Request
from time import time 

with Session(engine) as session: 
    def create_or_get_user(chat_id):
        statement = select(User).where(User.chat_id == chat_id) 
        user = session.exec(statement).first()
        if user == None:
            user = User(chat_id=chat_id, lastmessage=round(time(),2)) 
            session.add(user)
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
    def create_request(chat_id,title,description,file_id,duration,thumbnail):
        session.add(Request(chat_id=chat_id, title=title, description=description,file_id=file_id,duration=duration,thumbnail=thumbnail))
        session.commit()
    def get_request(file_id,chat_id):
        statement = select(Request).where(Request.file_id == file_id).where(Request.chat_id == chat_id)
        request = session.exec(statement).first()
        return request
    def delete_request(file_id,chat_id):
        statement = select(Request).where(Request.file_id == file_id).where(Request.chat_id == chat_id)
        request = session.exec(statement).first()
        session.delete(request)
        session.commit()
