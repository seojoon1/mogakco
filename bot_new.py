import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

# 모듈 import
from cogs import setup_all_cogs
from events import setup_all_events

# -------------------- 초기 설정 --------------------

load_dotenv()
BOT_TOKEN = os.environ.get("API_KEY")

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- 봇 이벤트 핸들러 --------------------

@bot.event
async def on_ready():
    print(f'{bot.user} (으)로 로그인 성공!')

    # Cogs 로드
    await setup_all_cogs(bot)

    # 이벤트 핸들러 등록
    setup_all_events(bot)

    # 슬래시 명령어 동기화
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}개의 슬래시 명령어를 동기화했습니다.")
    except Exception as e:
        print(f"명령어 동기화 실패: {e}")

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """전역 슬래시 명령어 에러 핸들러"""
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ 이 명령어를 실행할 권한이 없습니다.", ephemeral=True)
    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ 이 명령어는 봇 소유자만 사용할 수 있습니다.", ephemeral=True)
    else:
        print(f"'{interaction.command.name}' 명령어 처리 중 에러 발생: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("🐛 명령어 실행 중 알 수 없는 오류가 발생했습니다.", ephemeral=True)
        else:
            await interaction.followup.send("🐛 명령어 실행 중 알 수 없는 오류가 발생했습니다.", ephemeral=True)

# -------------------- 봇 실행 --------------------

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("오류: .env 파일에서 BOT_TOKEN을 찾을 수 없습니다.")
