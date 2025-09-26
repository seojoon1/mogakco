import discord
import os
from dotenv import load_dotenv

load_dotenv()



# 봇 토큰
BOT_TOKEN = os.environ.get("API_KEY") 

# 로그 기록할 채널과 감시할 보이스 채널 id 입력
TARGET_VOICE_CHANNEL_ID = 1420996835476115596
LOG_TEXT_CHANNEL_ID = 1420996774285541438

# 봇 권환 설정
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True 

# 봇 클라이언트를 생성합니다.
client = discord.Client(intents=intents)

# 봇이 성공적으로 로그인했을 때 실행되는 이벤트입니다.
@client.event
async def on_ready():
    print(f'{client.user} (으)로 로그인 성공!')
    print('음성 채널 로그 기록을 시작합니다...')

# 음성 채널 상태가 변경될 때 실행되는 이벤트입니다. (입장, 퇴장, 마이크 끄기 등)
@client.event
async def on_voice_state_update(member, before, after):
    # 로그를 남길 텍스트 채널 객체를 가져옵니다.
    log_channel = client.get_channel(LOG_TEXT_CHANNEL_ID)
    if log_channel is None:
        print("오류: 로그 채널을 찾을 수 없습니다. ID를 확인해주세요.")
        return

    # 1. 특정 음성 채널에 입장했을 때
    if before.channel is None and after.channel is not None and after.channel.id == TARGET_VOICE_CHANNEL_ID:
        embed = discord.Embed(
            title="🎙️ 음성 채널 입장",
            description=f"**{member.display_name}** 님이 음성 채널에 입장했습니다.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)

    # 2. 특정 음성 채널에서 퇴장했을 때
    elif before.channel is not None and after.channel is None and before.channel.id == TARGET_VOICE_CHANNEL_ID:
        embed = discord.Embed(
            title="🚫 음성 채널 퇴장",
            description=f"**{member.display_name}** 님이 음성 채널에서 나갔습니다.",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)

# 봇을 실행합니다.
client.run(BOT_TOKEN)