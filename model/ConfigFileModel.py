from pydantic import BaseModel

class ConfigDataModel(BaseModel):
    endpoint: str
    bucket_name: str
    access_key: str
    secret_key: str