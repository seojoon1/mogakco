import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from dotenv import load_dotenv

# -------------------- 초기 설정 --------------------

# .env 파일에서 봇 토큰을 불러옵니다.
load_dotenv()
BOT_TOKEN = os.environ.get("API_KEY")

# 봇이 서버의 정보(멤버, 음성 상태 등)를 제대로 수신하기 위한 권한 설정입니다.
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

# 봇 객체를 생성합니다.
bot = commands.Bot(command_prefix="!", intents=intents)

# 설정값이 저장될 파일의 이름입니다.
CONFIG_FILE = "config.json"


# -------------------- 설정 관리 함수 --------------------

def load_config():
    """서버별 채널 설정이 담긴 config.json 파일을 불러옵니다."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """변경된 설정 내용을 config.json 파일에 저장합니다."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


# -------------------- UI 컴포넌트 (설정 패널) --------------------

class SettingsView(discord.ui.View):
    """채널 설정을 위한 드롭다운 메뉴가 포함된 UI 뷰 클래스입니다."""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=180)  # 180초 후 버튼과 드롭다운이 비활성화됩니다.
        self.guild_id = str(interaction.guild.id)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.voice],
        placeholder="📢 감시할 음성 채널을 선택하세요",
        row=0
    )
    async def voice_channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        """음성 채널 드롭다운에서 채널을 선택했을 때 실행되는 콜백 함수입니다."""
        selected_channel = select.values[0]
        config = load_config()
        
        # 해당 서버의 설정이 없으면 새로 생성합니다.
        if self.guild_id not in config:
            config[self.guild_id] = {}
        
        # 선택된 채널 ID를 설정에 저장합니다.
        config[self.guild_id]["voice_channel_id"] = selected_channel.id
        save_config(config)

        # 사용자에게 피드백을 주기 위해 임베드 메시지를 업데이트합니다.
        await self.update_embed(interaction, f"음성 채널이 {selected_channel.mention}(으)로 설정되었습니다.")

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="✍️ 로그를 남길 텍스트 채널을 선택하세요",
        row=1
    )
    async def text_channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        """텍스트 채널 드롭다운에서 채널을 선택했을 때 실행되는 콜백 함수입니다."""
        selected_channel = select.values[0]
        config = load_config()

        if self.guild_id not in config:
            config[self.guild_id] = {}

        config[self.guild_id]["text_channel_id"] = selected_channel.id
        save_config(config)
        
        await self.update_embed(interaction, f"로그 채널이 {selected_channel.mention}(으)로 설정되었습니다.")
    
    async def update_embed(self, interaction: discord.Interaction, status_message: str):
        """설정 변경 후 임베드 메시지를 최신 상태로 업데이트하는 함수입니다."""
        config = load_config().get(self.guild_id, {})
        voice_channel_id = config.get("voice_channel_id")
        text_channel_id = config.get("text_channel_id")

        vc = interaction.guild.get_channel(voice_channel_id) if voice_channel_id else None
        tc = interaction.guild.get_channel(text_channel_id) if text_channel_id else None

        embed = discord.Embed(title="🎙️ 음성 채널 로그 설정", color=discord.Color.blue())
        embed.description = status_message
        embed.add_field(name="감시 중인 음성 채널", value=vc.mention if vc else "미설정", inline=False)
        embed.add_field(name="로그가 기록될 텍스트 채널", value=tc.mention if tc else "미설정", inline=False)
        
        # interaction.response.edit_message를 사용해 기존 메시지를 수정합니다.
        await interaction.response.edit_message(embed=embed, view=self)


# -------------------- 슬래시 명령어 --------------------

@bot.tree.command(name="설정", description="음성 채널과 로그 채널 설정을 위한 패널을 엽니다.")
@app_commands.checks.has_permissions(administrator=True) # 관리자만 이 명령어를 사용할 수 있습니다.
async def set_command(interaction: discord.Interaction):
    """'/설정' 명령어를 실행하면 현재 설정값을 보여주는 임베드와 설정용 UI를 보냅니다."""
    config = load_config().get(str(interaction.guild.id), {})
    voice_channel_id = config.get("voice_channel_id")
    text_channel_id = config.get("text_channel_id")

    # 저장된 ID를 실제 채널 객체로 변환합니다.
    vc = interaction.guild.get_channel(voice_channel_id) if voice_channel_id else None
    tc = interaction.guild.get_channel(text_channel_id) if text_channel_id else None

    # 현재 설정 상태를 보여주는 임베드를 생성합니다.
    embed = discord.Embed(
        title="🎙️ 음성 채널 로그 설정",
        description="아래 드롭다운 메뉴에서 채널을 선택해 설정을 변경하세요.",
        color=discord.Color.blue()
    )
    embed.add_field(name="감시 중인 음성 채널", value=vc.mention if vc else "미설정", inline=False)
    embed.add_field(name="로그가 기록될 텍스트 채널", value=tc.mention if tc else "미설정", inline=False)
    
    # ephemeral=True 옵션으로 명령어를 실행한 사용자에게만 보이게 합니다.
    await interaction.response.send_message(embed=embed, view=SettingsView(interaction), ephemeral=True)


# -------------------- 봇 이벤트 핸들러 --------------------

@bot.event
async def on_ready():
    """봇이 성공적으로 로그인하고 준비되었을 때 실행됩니다."""
    print(f'{bot.user} (으)로 로그인 성공!')
    try:
        # 슬래시 명령어를 디스코드 서버에 등록(동기화)합니다.
        synced = await bot.tree.sync()
        print(f"{len(synced)}개의 슬래시 명령어를 동기화했습니다.")
    except Exception as e:
        print(f"명령어 동기화 실패: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """서버 내 유저의 음성 상태(채널 입장/퇴장 등)가 변경될 때 실행됩니다."""
    config = load_config()
    server_id = str(member.guild.id)
    
    # 이 서버에 대한 설정이 없으면 아무 작업도 하지 않습니다.
    if server_id not in config: 
        return
    
    server_config = config[server_id]
    target_voice_channel_id = server_config.get("voice_channel_id")
    log_text_channel_id = server_config.get("text_channel_id")
    
    # 필요한 설정값이 없으면 작업을 중단합니다.
    if not target_voice_channel_id or not log_text_channel_id:
        return
    
    log_channel = bot.get_channel(log_text_channel_id)
    if log_channel is None:
        return
    
    # 유저가 설정된 음성 채널에 '입장'했는지 판별합니다.
    is_join = before.channel is None and after.channel is not None and after.channel.id == target_voice_channel_id
    # 유저가 설정된 음성 채널에서 '퇴장'했는지 판별합니다.
    is_leave = before.channel is not None and after.channel is None and before.channel.id == target_voice_channel_id
    
    if is_join:
        embed = discord.Embed(title="🎙️ 음성 채널 입장", description=f"**{member.display_name}** 님이 음성 채널에 입장했습니다.", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)
    elif is_leave:
        embed = discord.Embed(title="🚫 음성 채널 퇴장", description=f"**{member.display_name}** 님이 음성 채널에서 나갔습니다.", color=discord.Color.red())
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)


# -------------------- 봇 실행 --------------------

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("오류: .env 파일에서 BOT_TOKEN을 찾을 수 없습니다.")