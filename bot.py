import os
import discord
from discord.ext import commands
import requests

# Discord Bot Token
DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']

# Riot API Key
RIOT_API_KEY = os.environ['RIOT_API_KEY']

# Intents設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Data Dragon 日本語データ取得 ---
ddragon_champion_url = "https://ddragon.leagueoflegends.com/cdn/13.23.1/data/ja_JP/champion.json"
ddragon_item_url = "https://ddragon.leagueoflegends.com/cdn/13.23.1/data/ja_JP/item.json"

try:
    champion_data = requests.get(ddragon_champion_url, timeout=10).json()
    item_data = requests.get(ddragon_item_url, timeout=10).json()
except Exception as e:
    print(f"Data Dragon 取得失敗: {e}")
    champion_data = {}
    item_data = {}

# --- TFT ランク情報取得 ---
@bot.command(name="tft_rank")
async def tft_rank(ctx, summoner_name: str):
    try:
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
        headers = {"X-Riot-Token": RIOT_API_KEY}
        summoner = requests.get(url_summoner, headers=headers).json()
        summoner_id = summoner["id"]

        url_rank = f"https://jp1.api.riotgames.com/tft/league/v1/entries/by-summoner/{summoner_id}"
        rank_data = requests.get(url_rank, headers=headers).json()
        if not rank_data:
            await ctx.send(f"{summoner_name} はまだランク戦をプレイしていません。")
            return

        data = rank_data[0]
        await ctx.send(
            f"{summoner_name} のランク情報:\n"
            f"{data['tier']} {data['rank']} - {data['leaguePoints']}LP\n"
            f"勝利: {data['wins']} / 敗北: {data['losses']}"
        )
    except Exception as e:
        await ctx.send(f"エラー: {e}")

# --- TFT マッチ履歴取得 ---
@bot.command(name="tft_history")
async def tft_history(ctx, summoner_name: str, count: int = 3):
    try:
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
        headers = {"X-Riot-Token": RIOT_API_KEY}
        summoner = requests.get(url_summoner, headers=headers).json()
        puuid = summoner["puuid"]

        url_matches = f"https://asia.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        match_ids = requests.get(url_matches, headers=headers).json()
        if not match_ids:
            await ctx.send(f"{summoner_name} のマッチ履歴が見つかりません。")
            return

        for match_id in match_ids:
            url_match = f"https://asia.api.riotgames.com/tft/match/v1/matches/{match_id}"
            match_data = requests.get(url_match, headers=headers).json()

            participant = next(p for p in match_data["info"]["participants"] if p["puuid"] == puuid)
            placement = participant["placement"]

            # ユニット名日本語化
            units = []
            for u in participant.get("units", []):
                champ_key = u["character_id"]
                champ_name_jp = champion_data.get("data", {}).get(champ_key, {}).get("name", champ_key)
                units.append(champ_name_jp)
            units_str = ", ".join(units) if units else "なし"

            # アイテム名日本語化
            items = []
            for u in participant.get("units", []):
                if u.get("itemNames"):
                    for item in u["itemNames"]:
                        item_name_jp = item_data.get("data", {}).get(item, {}).get("name", item)
                        items.append(item_name_jp)
            items_str = ", ".join(items) if items else "なし"

            await ctx.send(
                f"試合ID: {match_id}\n"
                f"順位: {placement}\n"
                f"ユニット: {units_str}\n"
                f"アイテム: {items_str}\n"
                "----------------------"
            )
    except Exception as e:
        await ctx.send(f"エラー: {e}")

bot.run(DISCORD_TOKEN)