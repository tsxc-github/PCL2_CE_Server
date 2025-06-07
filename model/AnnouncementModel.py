from pydantic import BaseModel
from typing import Optional

class AnnouncementBtnModel(BaseModel):
    text: str
    command: str
    command_paramter: str

class AnnouncementInfoModel(BaseModel):
    title: str
    detail: str
    id: Optional[str]
    date: Optional[str]
    btn1: Optional[AnnouncementBtnModel]
    btn2: Optional[AnnouncementBtnModel]

class AnnouncementModel(BaseModel):
    content: list[AnnouncementInfoModel]