from pydantic import BaseModel


class AssetVersionInfoModel(BaseModel):
    channel: str
    name: str
    code: int

class AssetInfoModel(BaseModel):
    file_name: str
    version: AssetVersionInfoModel
    upd_time: str
    downloads: list[str]
    sha256: str
    changelog: str

class AssetUpdateFileStruct(BaseModel):
    assets: list[AssetInfoModel]