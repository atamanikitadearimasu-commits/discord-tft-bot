import os
import discord
from discord.ext import commands
from discord import app_commands
import requests

# --- 環境変数 ---
DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']
RIOT_API_KEY = os.environ['RIOT_API_KEY']

# --- Intents設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# --- Bot 初期化 ---
bot = commands.Bot(command_prefix="!", intents=intents)

# --- TFT ランク情報取得 ---
@app_commands.command(name="tft_rank", description="指定したサモナーのTFTランク情報を取得")
@app_commands.describe(summoner_name="サモナー名")
async def tft_rank(interaction: discord.Interaction, summoner_name: str):
    try:
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
        headers = {"X-Riot-Token": RIOT_API_KEY}
        summoner = requests.get(url_summoner, headers=headers).json()
        summoner_id = summoner["id"]

        url_rank = f"https://jp1.api.riotgames.com/tft/league/v1/entries/by-summoner/{summoner_id}"
        rank_data = requests.get(url_rank, headers=headers).json()

        if not rank_data:
            await interaction.response.send_message(f"{summoner_name} はまだランク戦をプレイしていません。")
            return

        data = rank_data[0]
        await interaction.response.send_message(
            f"{summoner_name} のランク情報:\n"
            f"{data['tier']} {data['rank']} - {data['leaguePoints']}LP\n"
            f"勝利: {data['wins']} / 敗北: {data['losses']}"
        )

    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}")

# --- TFT マッチ履歴取得 ---
@app_commands.command(name="tft_history", description="指定したサモナーの直近TFTマッチ履歴を取得")
@app_commands.describe(summoner_name="サモナー名", count="直近何試合取得するか（最大10）")
async def tft_history(interaction: discord.Interaction, summoner_name: str, count: int = 3):
    try:
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"
        headers = {"X-Riot-Token": RIOT_API_KEY}
        summoner = requests.get(url_summoner, headers=headers).json()
        puuid = summoner["puuid"]

        url_matches = f"https://asia.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        match_ids = requests.get(url_matches, headers=headers).json()

        if not match_ids:
            await interaction.response.send_message(f"{summoner_name} のマッチ履歴が見つかりません。")
            return

        messages = []
        for match_id in match_ids:
            url_match = f"https://asia.api.riotgames.com/tft/match/v1/matches/{match_id}"
            match_data = requests.get(url_match, headers=headers).json()

            participant = next(p for p in match_data["info"]["participants"] if p["puuid"] == puuid)
            placement = participant["placement"]
            units = ", ".join([u["character_id"] for u in participant.get("units", [])])
            items = []
            for u in participant.get("units", []):
                if u.get("itemNames"):
                    items.extend(u["itemNames"])
            items_str = ", ".join(items) if items else "なし"

            messages.append(
                f"試合ID: {match_id}\n"
                f"順位: {placement}\n"
                f"ユニット: {units}\n"
                f"アイテム: {items_str}\n"
                "----------------------"
            )

        # メッセージ送信（1つにまとめて送る）
        await interaction.response.send_message("\n".join(messages))

    except Exception as e:
        await interaction.response.send_message(f"エラー: {e}")

# --- コマンド登録 ---
@bot.event
async def on_ready():
    await bot.tree.sync()  # スラッシュコマンド登録
    print(f"{bot.user} がオンラインになりました！")

# --- Bot 起動 ---
bot.run(DISCORD_TOKEN)