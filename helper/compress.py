import zipfile
import bsdiff4

def compress_target_file(input_file_path: str, in_zip_file_name: str, output_path: str):
    with zipfile.ZipFile(output_path, mode="w",compression=zipfile.ZIP_DEFLATED) as compressed_file:
        compressed_file.write(
                filename=input_file_path,
                arcname=in_zip_file_name
            )
    
def make_diff(from_file_path: str, to_file_path: str, output_path: str):
    """
    创建两个文件之间的差异包
    :param from_file_path: 原始文件路径
    :param to_file_path: 目标文件路径
    :param output_path: 输出差异包路径
    """
    bsdiff4.file_diff(
        from_file_path,
        to_file_path,
        output_path
    )