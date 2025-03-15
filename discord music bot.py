import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="#", intents=intents)

queues = {}  # 음악 대기열 저장

@bot.event
async def on_ready():
    print(f"✅ 로그인: {bot.user.name}")

# 유튜브 검색 함수
async def search_youtube(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "default_search": "ytsearch5",
        "noplaylist": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info["entries"] if "entries" in info else []

# 음악 재생 함수
async def play_music(ctx, url):
    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = []

    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        queues[guild_id].append(url)
        await ctx.send(f"🎵 대기열에 추가됨: {url}")
        return

    ffmpeg_opts = {
        "executable": "C:\\ffmpeg\\bin\\ffmpeg.exe",  # FFmpeg 경로 설정 (Windows의 경우)
        "options": "-vn"
    }
    ydl_opts = {"format": "bestaudio"}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info["url"]

        await ctx.send(f"🎶 **{url}** 를 재생합니다!")  # 디버깅 메시지

        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url2, **ffmpeg_opts),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
    except Exception as e:
        await ctx.send(f"❌ 오류 발생: {str(e)}")

# 다음 노래 재생
async def play_next(ctx):
    guild_id = ctx.guild.id
    if queues[guild_id]:
        next_url = queues[guild_id].pop(0)
        await play_music(ctx, next_url)
    else:
        await asyncio.sleep(300)  # 5분 대기 후 퇴장
        if not ctx.voice_client.is_playing():
            await ctx.voice_client.disconnect()

# 🎵 버튼을 누르면 해당 번호의 노래 재생
class SongSelectionView(discord.ui.View):
    def __init__(self, ctx, results):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.results = results

        # 1~5번 버튼 추가
        for i in range(min(5, len(results))):
            button = discord.ui.Button(label=str(i+1), style=discord.ButtonStyle.primary)
            button.callback = self.create_callback(i)
            self.add_item(button)

    def create_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user == self.ctx.author:
                song_url = self.results[index]["webpage_url"]
                await interaction.response.send_message(f"🎵 **{interaction.user.name}**님이 {index+1}번 노래를 선택했습니다!", ephemeral=True)
                await play_music(self.ctx, song_url)  # 선택한 노래 재생
            else:
                await interaction.response.send_message("❌ 당신이 요청한 검색이 아닙니다!", ephemeral=True)
        return callback

# 🎶 !재생 명령어
@bot.command()
async def 재생(ctx, *, query):
    if not ctx.author.voice:
        await ctx.send("🎤 먼저 음성 채널에 접속하세요.")
        return

    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    results = await search_youtube(query)
    if not results:
        await ctx.send("❌ 검색 결과가 없습니다.")
        return

    embed = discord.Embed(title="🔎 검색 결과", description="🎵 원하는 노래 번호를 선택하세요!", color=discord.Color.blue())
    for i, result in enumerate(results[:5]):  # 최대 5개 표시
        embed.add_field(name=f"{i+1}. {result['title']}", value=result["webpage_url"], inline=False)

    view = SongSelectionView(ctx, results)
    await ctx.send(embed=embed, view=view)
    
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"🎤 {channel.name}에 연결되었습니다!")
    else:
        await ctx.send("❌ 먼저 음성 채널에 접속하세요.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🎶 음성 채널에서 나갔습니다.")
        
# ⏹️ !나가 명령어 (음성 채널 퇴장)
@bot.command()
async def 나가(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 봇이 음성 채널을 떠났습니다.")
    else:
        await ctx.send("❌ 봇이 음성 채널에 없습니다.")


access_token = os.environ["BOT_TOKEN"]
bot.run("assess_token")
