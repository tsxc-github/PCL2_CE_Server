import main
import os
import json

os.system("""curl -L \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/repos/Hex-Dragon/PCL2/releases \
    > release.json""")

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
            print("\n")
            break
    if prerelease:
        get_asset(prerelease=True)
    
get_asset()
    

main.main(ci=True)