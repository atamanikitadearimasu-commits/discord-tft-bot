import os
import discord
from discord import app_commands
from discord.ext import commands
import requests

# 環境変数
DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']
RIOT_API_KEY = os.environ['RIOT_API_KEY']

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# --- Data Dragon 日本語データ ---
ddragon_version = "13.23.1"
ddragon_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/ja_JP/tft.json"
ddragon_data = requests.get(ddragon_url).json()
champion_names = {c["id"]: c["name"] for c in ddragon_data["units"]}
trait_names = {t["apiName"]: t["name"] for t in ddragon_data["traits"]}

item_data_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/ja_JP/item.json"
item_data = requests.get(item_data_url).json()
item_names = {item_id: item_info["name"] for item_id, item_info in item_data["data"].items()}


# --- TFTランク取得 ---
@tree.command(name="tft_rank", description="サモナーのTFTランク情報を取得します")
@app_commands.describe(summoner_name="サモナー名")
async def tft_rank(interaction: discord.Interaction, summoner_name: str):
    await interaction.response.defer()
    try:
        headers = {"X-Riot-Token": RIOT_API_KEY}
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
        summoner = requests.get(url_summoner, headers=headers).json()
        summoner_id = summoner["id"]

        url_rank = f"https://jp1.api.riotgames.com/tft/league/v1/entries/by-summoner/{summoner_id}"
        rank_data = requests.get(url_rank, headers=headers).json()

        if not rank_data:
            await interaction.followup.send(f"{summoner_name} はまだランク戦をプレイしていません。")
            return

        data = rank_data[0]
        msg = (
            f"{summoner_name} のランク情報:\n"
            f"{data['tier']} {data['rank']} - {data['leaguePoints']}LP\n"
            f"勝利: {data['wins']} / 敗北: {data['losses']}"
        )
        await interaction.followup.send(msg)

    except Exception as e:
        await interaction.followup.send(f"エラー: {e}")


# --- TFTマッチ履歴取得 ---
@tree.command(name="tft_history", description="サモナーの直近マッチ履歴を取得します")
@app_commands.describe(summoner_name="サモナー名", count="直近何試合取得するか（最大10）")
async def tft_history(interaction: discord.Interaction, summoner_name: str, count: int = 3):
    await interaction.response.defer()
    try:
        headers = {"X-Riot-Token": RIOT_API_KEY}
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
        summoner = requests.get(url_summoner, headers=headers).json()
        puuid = summoner["puuid"]

        url_matches = f"https://asia.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        match_ids = requests.get(url_matches, headers=headers).json()
        if not match_ids:
            await interaction.followup.send(f"{summoner_name} のマッチ履歴が見つかりません。")
            return

        for match_id in match_ids:
            url_match = f"https://asia.api.riotgames.com/tft/match/v1/matches/{match_id}"
            match_data = requests.get(url_match, headers=headers).json()

            participant = next(p for p in match_data["info"]["participants"] if p["puuid"] == puuid)
            placement = participant["placement"]

            # ユニット・星ランク
            units_str = ", ".join([champion_names.get(u["character_id"], u["character_id"]) for u in participant.get("units", [])]) or "なし"
            star_units_str = ", ".join([f"{champion_names.get(u['character_id'], u['character_id'])} ★{u['tier']}" for u in participant.get("units", [])]) or "なし"

            # アイテム
            items = []
            for u in participant.get("units", []):
                if u.get("itemNames"):
                    for item_id in u["itemNames"]:
                        items.append(item_names.get(item_id, item_id))
            items_str = ", ".join(items) or "なし"

            # シナジー
            traits = []
            for t in participant.get("traits", []):
                trait_name = trait_names.get(t["name"], t["name"])
                tier_current = t.get("tier_current", 0)
                if tier_current > 0:
                    traits.append(f"{trait_name} {tier_current}")
            traits_str = ", ".join(traits) or "なし"

            embed = discord.Embed(title=f"{summoner_name} の試合情報", description=f"試合ID: {match_id}\n順位: {placement}", color=0x00ff00)
            embed.add_field(name="ユニット", value=units_str, inline=False)
            embed.add_field(name="ユニット星ランク", value=star_units_str, inline=False)
            embed.add_field(name="アイテム", value=items_str, inline=False)
            embed.add_field(name="シナジー", value=traits_str, inline=False)

            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"エラー: {e}")


# --- Riot APIキー確認 ---
@tree.command(name="riot_token_status", description="現在のRiot APIキーの状態を確認します")
async def riot_token_status(interaction: discord.Interaction):
    try:
        headers = {"X-Riot-Token": RIOT_API_KEY}
        # 簡単に1回API叩いて200なら有効
        url_summoner = "https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/test"
        r = requests.get(url_summoner, headers=headers)
        if r.status_code == 401:
            await interaction.response.send_message("Riot APIキーは無効または期限切れです。")
        else:
            await interaction.response.send_message("Riot APIキーは有効です。")
    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}")


# --- Bot起動時 ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user} and slash commands synced.")

bot.run(DISCORD_TOKEN)