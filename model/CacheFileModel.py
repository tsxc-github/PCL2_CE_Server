from pydantic import BaseModel

class CacheFileModel(BaseModel):
    updates: str
    announcement: str