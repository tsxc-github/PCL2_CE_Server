from pydantic import BaseModel, Field

class LocalFileModel(BaseModel):
    path: str
    name: str
    sha256:str
    create_time: str