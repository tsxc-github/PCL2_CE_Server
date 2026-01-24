# 使用方法

## 编辑 `.data/channel_rules.json` 文件

这个文件的结构看起来是下面这样。

```json
{
    "version":[
        {
            "channel_main_name": {
                "fr": "Beta"
            },
            "channel_sub_name": {
                "arm64": "ARM64",
                "x64": "x64"
            },
            "version_name": "2.10.7",
            "version_code": 367
        },
        {
            "channel_main_name": {
                "sr": "Release"
            },
            "channel_sub_name": {
                "arm64": "ARM64",
                "x64": "x64"
            },
            "version_name": "2.10.6",
            "version_code": 366
        }
    ],
    "sources": [
        "https://static.example.com/assets"
    ],
    "file_name": "Plain Craft Launcher Community Edition.exe"
}
```

CE 版本有 fr 和 sr 两个通道，也有 x64 和 arm64 两个不同目标编译平台版本，因此这里划分出 `channel_main_name` 与 `channel_sub_name`。<br/>
这两个在自动化脚本中认定为字典类型，Key 表明 channel 的名称，Value 表明包含什么字符的文件名属于此 channel。<br/>
最后组合主次 channel 名称得到最终的 channel 名称。

例如文件名 `PCL-CE-Beta-ARM64.exe` 包含 `Beta` 和 `ARM64` 关键字，因此其 `channel_main_name` 为 fr，`channel_sub_name` 为 arm64，最终组合得到的 channel 名称为 `frarm64`。

`version_name` 和 `version_code` 字面意思。

`sources` 字段是一个文本数组，用于指定多个下载源。

`file_name` 字段表示程序打包后在压缩包内的名称。

## 放入文件

将需要发行的文件放入 `.data/upload` 文件夹内

## 确保 `.data/oss/api/announcement.json` 存在

文件结构看起来是下面这样

```json
{
    "content": [
        {
            "title": "公告系统已上线",
            "detail": "公告系统将用于不定期投放调查问卷、安全提醒等方面。\n如果你不想被公告打扰，可以在 设置->其它->系统->启动器公告 处选择 关闭所有公告。",
            "id": "4a625783-2847-494b-b1f5-346140080a54",
            "date": "2025-05-02 13:32:38.920055+00:00",
            "btn1": {
                "text": "让我康康",
                "command": "打开网页",
                "command_paramter": "https://www.bilibili.com/video/BV1GJ411x7h7"
            },
            "btn2": null
        }
    ]
}
```

所有字段必须存在。

其中 `id` 与 `date` 可以为 null，为 null 后会自动补上内容。

`btn1` 与 `btn2` 可以为 null。

btn 中 `command` 与 `command_paramter` 与现有的自定义主页的 Event 参数使用方法一致。