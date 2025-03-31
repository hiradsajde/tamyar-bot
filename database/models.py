from sqlmodel import Field, SQLModel, BigInteger, create_engine
from typing import Optional
import time 

class User(SQLModel, table=True): 
    id: Optional[int] = Field(default=None,primary_key=True) 
    chat_id: int = Field(default=None,sa_column=BigInteger)
    last_message: float = Field(default=time.time(),sa_column=BigInteger)
    created_at: float = Field(default=time.time(),sa_column=BigInteger)

class Downlaod(SQLModel, table=True): 
    id: Optional[int] = Field(default=None,primary_key=True) 
    chat_id: int = Field(default=None,sa_column=BigInteger)
    size: int = Field(default=None,sa_column=BigInteger)
    time: int = Field(default=time.time(),sa_column=BigInteger)
    url: str 

class Request(SQLModel, table=True): 
    id: Optional[int] = Field(default=None,primary_key=True) 
    chat_id: int = Field(default=None,sa_column=BigInteger)
    title: str 
    description :str
    file_id: str
    thumbnail: str 
    duration: int = Field(default=None,sa_column=BigInteger)
    time: int = Field(default=time.time(),sa_column=BigInteger)
engine = create_engine("sqlite:///sqlite.db")