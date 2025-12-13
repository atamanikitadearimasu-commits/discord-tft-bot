import os
import discord
from discord import app_commands
from discord.ext import commands
import requests

DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']
RIOT_API_KEY = os.environ['RIOT_API_KEY']

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# スラッシュコマンドを Bot に登録
class TFTCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tft_rank", description="指定したサモナーのTFTランクを取得")
    @app_commands.describe(summoner_name="サモナー名（例: Faker）")
    async def tft_rank(self, interaction: discord.Interaction, summoner_name: str):
        headers = {"X-Riot-Token": RIOT_API_KEY}
        url_summoner = f"https://jp1.api.riotgames.com/tft/summoner/v1/summoners/by-name/{summoner_name}"

        try:
            response = requests.get(url_summoner, headers=headers)
            if response.status_code != 200:
                await interaction.response.send_message(
                    f"サモナー `{summoner_name}` が見つかりません。スペルを確認してください。"
                )
                return

            summoner = response.json()
            puuid = summoner.get("puuid")
            if not puuid:
                await interaction.response.send_message(f"PUUID を取得できませんでした。")
                return

            # ランク情報取得
            url_rank = f"https://jp1.api.riotgames.com/tft/league/v1/entries/by-summoner/{summoner['id']}"
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
            await interaction.response.send_message(f"エラーが発生しました: {e}")


bot.add_cog(TFTCommands(bot))

# Bot 起動
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} がオンラインになりました")

bot.run(DISCORD_TOKEN)