import main
import os
import json
import re
import shutil

os.system("""curl -L \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/repos/tsxc-github/PCL2-CE/releases \
    > release.json""")

channel_rules={
    "version":[],
    "sources": [
        {
            "name": "edgeone",
            "url": "https://edgeone.update.pcl.mzmcos.tsxc.xyz/",
            "group": ["v2"]
        },
        {
            "name": "CloudFlare",
            "url": "https://cloudflare.update.pcl.mzmcos.tsxc.xyz/",
            "group": ["v2"]
        },
        {
            "name": "GitHub",
            "url": "https://github.com/PCL-Community/PCL2_CE_Server/raw/refs/heads/main",
            "group": ["v2"]
        }
    ],
    "file_name": "Plain Craft Launcher Community Edition.exe"
}

def get_asset(prerelease: bool = False):
    json_data = json.load(open("release.json", "r", encoding="utf-8"))
    for release in json_data:
        if release["prerelease"] == prerelease:
            print(f"Release: {release['tag_name']}")
            print(f"Published at: {release['published_at']}")
            print(f"Assets:")
            for asset in release["assets"]:
                print(f" - {asset['name']} ({asset['size']} bytes)")
                os.system(f"""
                    curl -L \
                    -H "Accept: application/vnd.github+json" \
                    -H "X-GitHub-Api-Version: 2022-11-28" \
                    {asset["browser_download_url"]} \
                    > ./.data/release/{asset["name"]}
                """)
                
            os.system(f"""
                curl -L \
                -H "Accept: application/vnd.github+json" \
                -H "X-GitHub-Api-Version: 2022-11-28" \
                {release["tarball_url"]} \
                > code.tar.gz
            """)

            os.system("mkdir code")
            os.system("tar -xzf code.tar.gz -C ./code")
            folders = [entry for entry in os.listdir("./code") if os.path.isdir("./code/"+entry)]
            code=open("./code/"+folders[0]+"/Plain Craft Launcher 2/Modules/Base/ModBase.vb","r",encoding="utf-8").read()
            shutil.rmtree("./code")
            
            pattern = r"Public Const VersionCode As Integer = \d+ '内部版本号"
            re.search(pattern, code)
            version_code = re.search(pattern, code).group(0)
            version_code = int(re.search(r"\d+", version_code).group(0))
            print(f" - Version Code: {version_code}")
            
            channel_rules["version"].append(
                {
                    "channel_main_name": {
                    },
                    "channel_sub_name": {
                        "arm64":"ARM64",
                        "x64":"x64",
                    },
                    "version_name":f"{release["name"]}",
                    "version_code": version_code
                }
            )
            if prerelease:
                channel_rules["version"][-1]["channel_main_name"]["fr"] = "Beta"
                with open("./.data/fr_changelog.md", "w", encoding="utf-8") as f:
                    f.write(release["body"])
            else:
                channel_rules["version"][-1]["channel_main_name"]["sr"] = "Release"
                with open("./.data/sr_changelog.md", "w", encoding="utf-8") as f:
                    f.write(release["body"])
                    
            with open("./.data/channel_rules.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(channel_rules, ensure_ascii=False, indent=4))
            print("Channel rules updated successfully.")
            
            
            print("\n")
            break
    
    if prerelease == False:
        get_asset(prerelease=True)
    
get_asset()
    

main.main(ci=True)