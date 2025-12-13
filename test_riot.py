import os
import requests

# 環境変数からAPIキー取得
RIOT_API_KEY = os.environ.get("RIOT_API_KEY")

if not RIOT_API_KEY:
    print("⚠️ 環境変数 RIOT_API_KEY が設定されていません")
    exit()

# テスト用にサモナー情報取得（例: サモナー名 "プテラノ首領"）
summoner_name = "プテラノ首領"
url = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
headers = {"X-Riot-Token": RIOT_API_KEY}

try:
    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code != 200:
        print(f"⚠️ APIエラー: {data}")
    else:
        print("✅ サモナー情報取得成功！")
        print(f"サモナー名: {data['name']}")
        print(f"PUUID: {data['puuid']}")
        print(f"サモナーID: {data['id']}")
except Exception as e:
    print(f"⚠️ 例外が発生しました: {e}")