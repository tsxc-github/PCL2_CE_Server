from pydantic import BaseModel

class ChannelInfoVersionModel(BaseModel):
    channel_main_name: dict[str, str] #fr or sr, according to the file name
    channel_sub_name: dict[str, str] #arm64 or x64, according to the file name
    version_name: str #2.10.7a
    version_code: int #267

class ChannelSourceModel(BaseModel):
    name: str
    url: str
    group: list[str]

class ChannelInfoModel(BaseModel):
    version: list[ChannelInfoVersionModel]
    sources: list[ChannelSourceModel]
    file_name: str
    