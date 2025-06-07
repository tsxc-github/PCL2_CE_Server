import os
# from s3 import upload
# from s3 import s3_client, config
from helper import hash, logger, config, compress, text
import json
import consts
from pathlib import Path
from datetime import datetime, timezone
from model.ChannelInfoModel import ChannelInfoModel
from model.AssetInfoModel import AssetInfoModel, AssetVersionInfoModel, AssetUpdateFileStruct
from model.CacheFileModel import CacheFileModel
from model.AnnouncementModel import AnnouncementModel
from model.LocalFileModel import LocalFileModel

release_config: ChannelInfoModel = None

def init():
    global release_config
    # 初始化配置
    release_config = config.get_release_config()
    # 初始化文件夹
    os.makedirs(
        consts.OSS_UPLOAD_FOLDER,
        exist_ok=True
        )
    os.makedirs(
        ".data/release",
        exist_ok=True
        )
    os.makedirs(
        Path.joinpath(consts.OSS_UPLOAD_FOLDER, "common").resolve().as_posix(),
        exist_ok=True
    )
    for folder in release_config.sources:
        current_source_folder = Path.joinpath(consts.OSS_UPLOAD_FOLDER, folder.name).resolve()
        os.makedirs(
            current_source_folder.joinpath("assets").as_posix(),
            exist_ok=True
        )
        os.makedirs(
            current_source_folder.joinpath("api").as_posix(),
            exist_ok=True
        )

def get_local_asset_info() -> list[LocalFileModel]:
    release_files = Path.iterdir(consts.RELEASE_FILE_FOLDER)
    ret: list[LocalFileModel] = []
    for file in release_files:
        ret.append(
            LocalFileModel(
                path=file.as_posix(),
                name=file.name,
                create_time=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                sha256=hash.get_file_sha256(file.as_posix()),
            )
        )
    return ret

def update_source_cache_file(source_name: str):
    current_source_folder = Path.joinpath(consts.OSS_UPLOAD_FOLDER, source_name).resolve()
    current_source_api_folder = current_source_folder.joinpath("api").resolve()
    res_cahce_file = CacheFileModel(
        updates=hash.get_file_md5(current_source_api_folder.joinpath("updates.json").as_posix()),
        announcement=hash.get_file_md5(current_source_api_folder.joinpath("announcement.json").as_posix())
    )
    with open(current_source_api_folder.joinpath("cache.json").as_posix(), "w+", encoding="utf-8") as f:
        json.dump(
            res_cahce_file.model_dump(),
            f,
            ensure_ascii=False,
            indent=4
        )
    print(f"更新源 {source_name} 的缓存文件已更新，存储在 {current_source_api_folder.joinpath('cache.json').as_posix()}")

def start_release_file_process(file_path: Path,skip_check: bool = False):
    print("----开始处理发版文件----")
    print("请确认发版信息：")
    for i in release_config.version:
        for j in i.channel_main_name.items():
            display_channel_name = j[1]
            print(f" - 渠道: {display_channel_name}, 版本号: {i.version_name}({i.version_code})")
    if skip_check==False and input("信息是否正确(Y/N)\n> ").strip().lower() != "y":
        print("请填入正确的发版信息后重新启动程序")
        return
    print("获取发版文件列表中……")
    local_files = get_local_asset_info()
    if not local_files:
        print("未找到发版文件，请检查发版文件夹是否存在")
        return
    display_file_list = "\n - ".join([f'{f.name} - {f.create_time}'  for f in local_files])
    print(f"找到 {len(local_files)} 个发版文件:\n - {display_file_list}")
    print("决定文件类型中……")
    
    output_files: list[AssetInfoModel] = []
    for channel_branch in release_config.version:
        current_branch_main = channel_branch.channel_main_name
        for channel_recognize_chars in current_branch_main.items():
            current_channel_type = channel_recognize_chars[0]
            current_channel_type_key_word = channel_recognize_chars[1]
            current_changelog = consts.DATA_FOLDER.joinpath(f"{current_channel_type}_changelog.md")
            if not current_changelog.exists():
                print(f"未找到 {current_channel_type} 的变更日志文件，请检查 changelog 文件是否存在")
                return
            for channel_sub_name in channel_branch.channel_sub_name.items():
                current_channel_sub_type = channel_sub_name[0]
                current_channel_sub_type_key_word = channel_sub_name[1]
                for file in local_files:
                    if (current_channel_type_key_word in file.path and
                        current_channel_sub_type_key_word in file.name):
                        print(f" - 匹配文件: {file.name} - {current_channel_type} - {current_channel_sub_type}")
                        output_files.append(
                            AssetInfoModel(
                                file_name=file.path,
                                version=AssetVersionInfoModel(
                                    channel=f"{current_channel_type}{current_channel_sub_type}",
                                    name=channel_branch.version_name,
                                    code=channel_branch.version_code
                                ),
                                upd_time=file.create_time,
                                sha256=file.sha256,
                                changelog=current_changelog.read_text(encoding="utf-8"),
                                downloads=[]
                            )
                        )

    if not output_files:
        print("未找到匹配的发版文件，请检查发版文件夹是否存在")
        return
    print("文件类型决定完成，开始构造更新文件结构")
    # 构造每一个更新源独属的更新文件结构
    for file in output_files:
        archived_path = Path.joinpath(consts.OSS_UPLOAD_FOLDER, "common").joinpath(file.sha256 + ".zip")
        print(f"开始压缩文件：{file.file_name} -> {archived_path}")
        compress.compress_target_file(file.file_name, consts.RELEASE_ARCHIVE_INNER_FILE_NAME, archived_path)
    print("文件压缩完成")
    print("构建更新源数据……")
    for source in release_config.sources:
        res_upd_file = AssetUpdateFileStruct(
            assets=[]
        )
        current_source_folder = Path.joinpath(consts.OSS_UPLOAD_FOLDER, source.name).resolve()
        current_source_assets_folder = current_source_folder.joinpath("assets").resolve()
        current_source_api_folder = current_source_folder.joinpath("api").resolve()
        # 清空当前源的assets文件夹
        for old_file in current_source_assets_folder.iterdir():
            old_file.unlink(missing_ok=True)

        for file in output_files:
            archived_path = Path.joinpath(consts.OSS_UPLOAD_FOLDER, "common").joinpath(file.sha256 + ".zip")
            current_source_archive_path = current_source_assets_folder.joinpath(file.sha256 + ".zip")
            print(f"将文件 {archived_path} 复制到 {current_source_archive_path}")
            current_source_archive_path.write_bytes(archived_path.read_bytes())
            res_upd_file.assets.append(
                AssetInfoModel(
                    file_name=current_source_archive_path.name,
                    version=file.version,
                    upd_time=file.upd_time,
                    sha256=hash.get_file_sha256(current_source_archive_path.as_posix()),
                    changelog=file.changelog,
                    downloads=[
                        f"{source.url}/assets/{file.sha256}.zip"
                    ]
                )
            )

        with open(current_source_api_folder.joinpath("updates.json").as_posix(), "w+", encoding="utf-8") as f:
            json.dump(
                res_upd_file.model_dump(),
                f,
                ensure_ascii=False,
                indent=4
            )

        update_source_cache_file(source.name)
        
        print(f"更新源 {source.name} 的更新文件结构已构建完成，存储在 {current_source_api_folder.as_posix()}")


def start_announcement_file_process():
    print("----处理公告文件----")
    if not consts.RELEASE_ANNOUNCEMENT_PATH.exists():
        print("未找到公告文件，请检查公告文件是否存在")
        return
    current_announcement = AnnouncementModel.model_validate_json(consts.RELEASE_ANNOUNCEMENT_PATH.read_text(encoding="utf-8"))
    for ans in current_announcement.content:
        if ans.date is None:
            ans.date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if ans.id is None:
            ans.id = text.get_uuid()
    consts.RELEASE_ANNOUNCEMENT_PATH.write_text(
        current_announcement.model_dump_json(indent=4),
        encoding="utf-8"
    )
    print("已完成公告文件补全")
    for source in release_config.sources:
        current_source_announcement = Path.joinpath(consts.OSS_UPLOAD_FOLDER, source.name).joinpath("api").joinpath("announcement.json").resolve()
        if current_source_announcement.exists():
            current_source_announcement.unlink()
        print(f"开始处理公告文件：{consts.RELEASE_ANNOUNCEMENT_PATH.as_posix()} -> {current_source_announcement.as_posix()}")
        current_source_announcement.write_bytes(consts.RELEASE_ANNOUNCEMENT_PATH.read_bytes())

        update_source_cache_file(source.name)
    print("公告文件处理完成")

def main(ci: bool = False):
    global release_config
    init()
    while (True):
        if ci:
            print("----CI模式运行中----")
            c="3"
        else:
            c = input("----选择操作----\n1. 处理发版文件\n2. 处理公告文件\n3. 上传到服务器(暂时不可用)\nq. 退出\n> ").strip().lower()
        
        if c == "1":
            start_release_file_process(consts.RELEASE_FILE_FOLDER)
        elif c == "2":
            start_announcement_file_process()
        elif c == "3":
            start_release_file_process(consts.RELEASE_FILE_FOLDER,True)
            start_announcement_file_process()
            break
        elif c == "q":
            print("退出程序")
            break
        else:
            print("无效的选项，请重新输入")
            continue

        print("----任务已完成----")


if __name__ == "__main__":
    main()