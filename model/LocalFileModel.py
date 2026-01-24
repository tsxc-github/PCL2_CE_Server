from pydantic import BaseModel, Field
from typing import Optional
from model.AssetInfoModel import AssetVersionInfoModel

class LocalFileModel(BaseModel):
    path: str
    name: str
    sha256:str
    create_time: str
    channel_info: Optional[AssetVersionInfoModel]