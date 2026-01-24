import os
import json
import consts
from pathlib import Path
from datetime import datetime, timezone
import threadpool

from helper import hash, logger, config, compress, text
from model.ChannelInfoModel import ChannelInfoModel
from model.AssetInfoModel import AssetInfoModel, AssetVersionInfoModel, AssetUpdateFileStruct
from model.CacheFileModel import CacheFileModel
from model.AnnouncementModel import AnnouncementModel
from model.LocalFileModel import LocalFileModel

release_config: ChannelInfoModel

def init():
    global release_config
    # 初始化配置
    release_config = config.get_release_config()
    # 初始化文件夹
    os.makedirs(
        consts.OSS_UPLOAD_FOLDER_OLD,
        exist_ok=True
        )
    os.makedirs(
        ".data/release",
        exist_ok=True
        )
    os.makedirs(
        Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, "common").resolve().as_posix(),
        exist_ok=True
    )
    for folder in release_config.sources:
        current_source_folder = Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, folder.name).resolve()
        os.makedirs(
            current_source_folder.joinpath("assets").as_posix(),
            exist_ok=True
        )
        os.makedirs(
            current_source_folder.joinpath("api").as_posix(),
            exist_ok=True
        )

def get_local_asset_info(folder: Path) -> list[LocalFileModel]:
    release_files = folder.iterdir()
    ret: list[LocalFileModel] = []
    for file in release_files:
        if not file.is_file():
            continue
        ret.append(
            LocalFileModel(
                path=file.as_posix(),
                name=file.name,
                create_time=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                sha256=hash.get_file_sha256(file.as_posix()),
                channel_info=None
            )
        )
    return ret

def deserialize_local_files(files: list[LocalFileModel]) -> list[LocalFileModel]:
    """
    将本地的文件类型依据 Channel 信息进行反序列化
    :param files: 本地文件列表
    :return: 含有了 channel_info 的 LocalFileModel 对象列表
    """
    ret: list[LocalFileModel] = []
    # 第一遍开始大致匹配每个 channel
    for item_channel in release_config.version:
        # 匹配 channel_main_name
        for item_main_name in item_channel.channel_main_name.items():
            current_channel_type = item_main_name[0]
            current_channel_type_key_word = item_main_name[1]
            # 匹配 channel_sub_name
            for item_sub_name in item_channel.channel_sub_name.items():
                current_channel_sub_type = item_sub_name[0]
                current_channel_sub_type_key_word = item_sub_name[1]
                for file in files:
                    if (current_channel_type_key_word in file.path and
                        current_channel_sub_type_key_word in file.name):
                        append_asset = file.model_copy(deep=True)
                        append_asset.channel_info = AssetVersionInfoModel(
                            channel=f"{current_channel_type}{current_channel_sub_type}",
                            name=item_channel.version_name,
                            code=item_channel.version_code
                        )
                        ret.append(append_asset)
    return ret

def update_source_cache_file_v1(source_name: str):
    current_source_api_folder = Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, source_name).resolve()
    current_source_api_update_folder = current_source_api_folder.joinpath("api").resolve()
    res_cahce_file = CacheFileModel(
        updates=hash.get_file_md5(current_source_api_update_folder.joinpath("updates.json").as_posix()),
        announcement=hash.get_file_md5(current_source_api_update_folder.joinpath("announcement.json").as_posix())
    )
    with open(current_source_api_update_folder.joinpath("cache.json").as_posix(), "w+", encoding="utf-8") as f:
        json.dump(
            res_cahce_file.model_dump(),
            f,
            ensure_ascii=False,
            indent=4
        )
    logger.info(f"更新源 {source_name} 的缓存文件已更新，存储在 {current_source_api_update_folder.joinpath('cache.json').as_posix()}")

def get_source_groups() -> list[str]:
    """
    获取所有源的组
    :return: 源组列表
    """
    source_groups: list[str] = []
    for item_source in release_config.sources:
        source_groups.extend(item_source.group)
    return list(set(source_groups))

def update_source_cache_file_v2(group_name: str):
    cache_res: dict[str, str] = {}
    current_source_api_folder = consts.OSS_UPLOAD_FOLDER.joinpath(f"api-{group_name}").resolve()
    current_source_api_update_folder = current_source_api_folder.joinpath("updates").resolve()


    for item_channel in current_source_api_update_folder.iterdir():
        if item_channel.is_file() and item_channel.suffix == ".json":
            cache_res[f"{item_channel.stem}"] = hash.get_file_md5(item_channel.as_posix())
    cache_res["announcement"] = hash.get_file_md5(current_source_api_folder.joinpath("announcement.json").as_posix())
    with open(current_source_api_folder.joinpath("cache.json").as_posix(), "w+", encoding="utf-8") as f:
        json.dump(
            cache_res,
            f,
            ensure_ascii=False
        )
    logger.info(f"更新组 {group_name} 的缓存文件已更新，存储在 {current_source_api_update_folder.joinpath('cache.json').as_posix()}")


def require_version_check() -> bool:
    logger.info("请确认发版信息：")
    for i in release_config.version:
        for j in i.channel_main_name.items():
            display_channel_name = j[1]
            logger.info(f" - 渠道: {display_channel_name}, 版本号: {i.version_name}({i.version_code})")
    if input("信息是否正确(Y/N)\n> ").strip().lower() != "y":
        logger.info("请填入正确的发版信息后重新启动程序")
        return False
    return True

def get_downloads_from_source_group(group: str, path: str) -> list[str]:
    """
    获取指定源组的下载链接
    :param group: 源组名称
    :param path: 文件相对路径
    :return: 下载链接列表
    """
    downloads: list[str] = []
    for source in release_config.sources:
        if group in source.group:
            downloads.append(f"{source.url}/{path}")
    return downloads

def start_release_file_process_v1(skip_check: bool = False):
    logger.info("----开始处理发版文件(旧版)----")
    if not skip_check and not require_version_check():
        return
    logger.info("获取发版文件列表中……")
    local_files = get_local_asset_info(consts.RELEASE_FILE_FOLDER)
    if not local_files:
        logger.info("未找到发版文件，请检查发版文件夹是否存在")
        return
    display_file_list = "\n - ".join([f'{f.name} - {f.create_time}'  for f in local_files])
    logger.info(f"找到 {len(local_files)} 个发版文件:\n - {display_file_list}")
    logger.info("决定文件类型中……")
    
    output_files: list[AssetInfoModel] = []
    for channel_branch in release_config.version:
        current_branch_main = channel_branch.channel_main_name
        for channel_recognize_chars in current_branch_main.items():
            current_channel_type = channel_recognize_chars[0]
            current_channel_type_key_word = channel_recognize_chars[1]
            current_changelog = consts.DATA_FOLDER.joinpath(f"{current_channel_type}_changelog.md")
            if not current_changelog.exists():
                logger.info(f"未找到 {current_channel_type} 的变更日志文件，请检查 changelog 文件是否存在")
                return
            for channel_sub_name in channel_branch.channel_sub_name.items():
                current_channel_sub_type = channel_sub_name[0]
                current_channel_sub_type_key_word = channel_sub_name[1]
                for file in local_files:
                    if (current_channel_type_key_word in file.path and
                        current_channel_sub_type_key_word in file.name):
                        logger.info(f" - 匹配文件: {file.name} - {current_channel_type} - {current_channel_sub_type}")
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
                                downloads=[],
                                patches=[]
                            )
                        )

    if not output_files:
        logger.info("未找到匹配的发版文件，请检查发版文件夹是否存在")
        return
    logger.info("文件类型决定完成，开始构造更新文件结构")
    # 构造每一个更新源独属的更新文件结构
    for file in output_files:
        archived_path = Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, "common").joinpath(file.sha256 + ".zip")
        logger.info(f"开始压缩文件：{file.file_name} -> {archived_path}")
        compress.compress_target_file(
            file.file_name,
            release_config.file_name,
            archived_path.as_posix())
    logger.info("文件压缩完成")
    logger.info("构建更新源数据……")
    for source in release_config.sources:
        res_upd_file = AssetUpdateFileStruct(
            assets=[]
        )
        current_source_folder = Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, source.name).resolve()
        current_source_assets_folder = current_source_folder.joinpath("assets").resolve()
        current_source_api_folder = current_source_folder.joinpath("api").resolve()
        # 清空当前源的assets文件夹
        for old_file in current_source_assets_folder.iterdir():
            old_file.unlink(missing_ok=True)

        for file in output_files:
            archived_path = Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, "common").joinpath(file.sha256 + ".zip")
            current_source_archive_path = current_source_assets_folder.joinpath(file.sha256 + ".zip")
            logger.info(f"将文件 {archived_path} 复制到 {current_source_archive_path}")
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
                    ],
                    patches=[]
                )
            )

        with open(current_source_api_folder.joinpath("updates.json").as_posix(), "w+", encoding="utf-8") as f:
            json.dump(
                res_upd_file.model_dump(),
                f,
                ensure_ascii=False,
                indent=4
            )

        update_source_cache_file_v1(source.name)
        
        logger.info(f"更新源 {source.name} 的更新文件结构已构建完成，存储在 {current_source_api_folder.as_posix()}")

def update_diff_patch() -> list[str]:
    archives = get_local_asset_info(consts.ARCHIVE_RELEASE_FOLDER)
    current = get_local_asset_info(consts.RELEASE_FILE_FOLDER)
    # 制作每一个 archive -> current 的差异包
    ret: list[str] = []
    logger.info("清空旧的差异包文件夹……")
    patch_folder = consts.OSS_UPLOAD_FOLDER.joinpath("static").joinpath("patch")
    for file in patch_folder.iterdir():
        file.unlink(missing_ok=True)

    logger.info(f"开始制作差异包……(存档:{len(archives)}, 当前: {len(current)}, 预估产生差异包数量: {len(archives) * len(current) - len(archives)})")
    patch_folder.mkdir(parents=True, exist_ok=True)
    making_pool = threadpool.ThreadPool(15)

    for archive in archives:
        for item in current:
            if archive.sha256 == item.sha256:
                continue
            else:
                def make_diff_pack_thread(archive: LocalFileModel, item: LocalFileModel):
                    if archive.sha256 == item.sha256:
                        return
                    cur_filename = f"{archive.sha256}_{item.sha256}.patch"
                    ret.append(cur_filename)
                    compress.make_diff(
                        from_file_path=archive.path,
                        to_file_path=item.path,
                        output_path=patch_folder.joinpath(cur_filename).as_posix()
                    )
                    logger.info(f"完成差异包: {archive.sha256} -> {item.sha256}")
                making_pool.putRequest(
                    threadpool.WorkRequest(
                        make_diff_pack_thread,
                        args=(archive, item)
                    )
                )

    making_pool.wait()
    logger.info(f"差异包制作完成，共计 {len(ret)} 个差异包")
    return ret

def start_release_file_process_v2(skip_check=False):
    logger.info("----开始处理发版文件(新版)----")
    consts.OSS_UPLOAD_FOLDER.joinpath("static").joinpath("raw").mkdir(parents=True, exist_ok=True)
    consts.ARCHIVE_RELEASE_FOLDER.mkdir(parents=True, exist_ok=True)

    if not skip_check and not require_version_check():
        return
    logger.info("获取发版文件列表中……")
    local_files = get_local_asset_info(consts.RELEASE_FILE_FOLDER)
    if not local_files:
        logger.info("未找到发版文件，请检查发版文件夹是否存在")
        return
    display_file_list = "\n - ".join([f'{f.name} - {f.create_time}'  for f in local_files])
    logger.info(f"找到 {len(local_files)} 个发版文件:\n - {display_file_list}")

    # 存档文件
    for file in local_files:
        source_file = Path(file.path)
        dest_file = consts.ARCHIVE_RELEASE_FOLDER.joinpath(file.sha256 + ".bin")
        if dest_file.exists() and source_file.stat().st_size == dest_file.stat().st_size:
            logger.info(f"文件 {source_file.name} 已存在，跳过存档")
            continue
        logger.info(f"存档文件 {source_file.name} 到 {dest_file.as_posix()}")
        dest_file.write_bytes(source_file.read_bytes())

    # 制作差异包
    patch_files: list[str] = []
    if not skip_check:
        if input("本次发版是否制作并包含差分包？(Y/N)").strip().lower() == "y":
            patch_files = update_diff_patch()

    logger.info("决定文件类型中……")
    local_files = deserialize_local_files(local_files)
    if not local_files:
        logger.info("未找到匹配的发版文件，请检查发版文件夹是否存在")
        return
    display_file_list = "\n - ".join([f'{f.name} - {f.create_time} - {f.channel_info.channel} - {f.channel_info.name}'
                                      if f.channel_info else f'{f.name} channel_info data is null!'
                                      for f in local_files])
    logger.info(f"文件类型决定完成，找到 {len(local_files)} 个发版文件:\n - {display_file_list}")

    # 清空最新版本文件夹
    for file in consts.OSS_UPLOAD_FOLDER.joinpath("static").joinpath("raw").iterdir():
        file.unlink(missing_ok=True)
    # 复制最新版本文件
    for file in local_files:
        source_file = Path(file.path)
        dest_file = consts.OSS_UPLOAD_FOLDER.joinpath("static").joinpath("raw").joinpath(file.sha256 + ".zip")
        if dest_file.exists():
            logger.info(f"文件 {source_file.name} 已存在，跳过复制")
            continue
        logger.info(f"压缩并复制文件 {source_file.name} 到 {dest_file.as_posix()}")
        compress.compress_target_file(
            input_file_path=source_file.as_posix(),
            in_zip_file_name=release_config.file_name,
            output_path=dest_file.as_posix()
        )

    # 构造更新通道的更新文件
    # 每个更新源
    for item_source in get_source_groups():
        for item_channel in release_config.version:
            for item_main_name in item_channel.channel_main_name.items():
                current_channel_main_name = item_main_name[0]
                for item_sub_name in item_channel.channel_sub_name.items():
                    current_channel_sub_name = item_sub_name[0]
                    current_channel_type = f"{current_channel_main_name}{current_channel_sub_name}"
                    file_in_current_channel = list(filter(
                        lambda x: x.channel_info and x.channel_info.channel == current_channel_type,
                        local_files
                    ))
                

                    cur_assets: list[AssetInfoModel] = []
                    for item_file in file_in_current_channel:
                        if item_file.channel_info is None: # 加这个是因为 Pylance 会报错，实际上前面的逻辑已经保证了 item_file.channel_info 不为 None
                            logger.error(f"文件 {item_file.name} 的 channel_info 为空，跳过")
                            continue
                        cur_file_info = Path(item_file.path)
                        cur_assets.append(AssetInfoModel(
                            file_name=cur_file_info.name,
                            version=item_file.channel_info,
                            upd_time=item_file.create_time,
                            sha256=item_file.sha256,
                            changelog=consts.DATA_FOLDER.joinpath(f"{current_channel_main_name}_changelog.md").read_text(encoding="utf-8"),
                            downloads=get_downloads_from_source_group(item_source, f"static/raw/{item_file.sha256}.zip"),
                            patches=patch_files
                        ))
                    cur_source_file = AssetUpdateFileStruct(
                        assets=cur_assets
                    )
                    target_path = consts.OSS_UPLOAD_FOLDER.joinpath(f"api-{item_source}").joinpath("updates").joinpath(f"updates-{current_channel_type}.json")
                    if not target_path.parent.exists():
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path.as_posix(), "w+", encoding="utf-8") as f:
                        json.dump(
                            cur_source_file.model_dump(),
                            f,
                            ensure_ascii=False,
                            indent=4
                        )
        update_source_cache_file_v2(item_source)

def start_announcement_file_process():
    logger.info("----处理公告文件----")
    if not consts.RELEASE_ANNOUNCEMENT_PATH.exists():
        logger.info("未找到公告文件，请检查公告文件是否存在")
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
    logger.info("已完成公告文件补全")
    for source in release_config.sources:
        current_source_announcement = Path.joinpath(consts.OSS_UPLOAD_FOLDER_OLD, source.name).joinpath("api").joinpath("announcement.json").resolve()
        if current_source_announcement.exists():
            current_source_announcement.unlink()
        logger.info(f"开始处理公告文件：{consts.RELEASE_ANNOUNCEMENT_PATH.as_posix()} -> {current_source_announcement.as_posix()}")
        current_source_announcement.write_bytes(consts.RELEASE_ANNOUNCEMENT_PATH.read_bytes())

        update_source_cache_file_v1(source.name)
    for item_groups in get_source_groups():
        current_source_announcement = consts.OSS_UPLOAD_FOLDER.joinpath(f"api-{item_groups}").joinpath("announcement.json").resolve()
        if current_source_announcement.exists():
            current_source_announcement.unlink()
        logger.info(f"开始处理公告文件：{consts.RELEASE_ANNOUNCEMENT_PATH.as_posix()} -> {current_source_announcement.as_posix()}")
        current_source_announcement.write_bytes(consts.RELEASE_ANNOUNCEMENT_PATH.read_bytes())
        update_source_cache_file_v2(item_groups)

    logger.info("公告文件处理完成")

def start_upload():
    logger.info("上传到服务器(暂时不可用)")
    pass

def main(ci=False):
    global release_config
    init()
    if not release_config:
        return
    if ci:
        start_release_file_process_v1(True)
        start_release_file_process_v2(True)
        start_announcement_file_process()
        return

    while (True):
        logger.info("----选择操作----\n1. 处理发版文件(新版)\n2. 处理发版文件(旧版)\n3. 处理公告文件\n4. 上传到服务器(暂时不可用)\nq. 退出")
        c = input("> ").strip().lower()
        if c == "1":
            start_release_file_process_v2()
        elif c == "2":
            start_release_file_process_v1()
        elif c == "3":
            start_announcement_file_process()
        elif c == "4":
            start_upload()
        elif c == "q":
            logger.info("退出程序")
            break
        else:
            logger.info("无效的选项，请重新输入")
            continue

        logger.info("----任务已完成----")


if __name__ == "__main__":
    main()