from model.ChannelInfoModel import ChannelInfoModel
import json
import consts

def get_release_config() -> ChannelInfoModel:
    with open(consts.RELEASE_CONFIG_PATH.as_posix(), encoding="utf-8") as f:
        return ChannelInfoModel.model_validate(json.load(f))
