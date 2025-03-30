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
    chat_id: int 
    size: int = Field(default=None,sa_column=BigInteger)
    time: int = Field(default=time.time(),sa_column=BigInteger)
    url: str 

engine = create_engine("sqlite:///sqlite.db")