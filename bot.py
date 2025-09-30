import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from dotenv import load_dotenv
import datetime
import asyncio

# -------------------- 초기 설정 --------------------

load_dotenv()
BOT_TOKEN = os.environ.get("API_KEY")

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "config.json"
config_lock = asyncio.Lock() # 설정 파일 동시 접근을 막기 위한 Lock

# 사용자의 음성 채널 접속 시간을 기록하는 딕셔너리
voice_connections = {}

# -------------------- 설정 관리 함수 --------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


# -------------------- UI 컴포넌트 (설정 패널, 처벌 설정, 모달) --------------------

class SettingsView(discord.ui.View):
    """채널 설정을 위한 드롭다운 메뉴가 포함된 UI 뷰 클래스입니다."""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.guild_id = str(interaction.guild.id)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.voice],
        placeholder="📢 감시할 음성 채널을 선택하세요",
        row=0
    )
    async def voice_channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        selected_channel = select.values[0]
        async with config_lock:
            config = load_config()
            if self.guild_id not in config:
                config[self.guild_id] = {}
            config[self.guild_id]["voice_channel_id"] = selected_channel.id
            save_config(config)
        await self.update_embed(interaction, f"음성 채널이 {selected_channel.mention}(으)로 설정되었습니다.")

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="✍️ 로그를 남길 텍스트 채널을 선택하세요",
        row=1
    )
    async def text_channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        selected_channel = select.values[0]
        async with config_lock:
            config = load_config()
            if self.guild_id not in config:
                config[self.guild_id] = {}
            config[self.guild_id]["text_channel_id"] = selected_channel.id
            save_config(config)
        await self.update_embed(interaction, f"로그 채널이 {selected_channel.mention}(으)로 설정되었습니다.")
    
    async def update_embed(self, interaction: discord.Interaction, status_message: str):
        config = load_config().get(self.guild_id, {})
        voice_channel_id = config.get("voice_channel_id")
        text_channel_id = config.get("text_channel_id")
        vc = interaction.guild.get_channel(voice_channel_id) if voice_channel_id else None
        tc = interaction.guild.get_channel(text_channel_id) if text_channel_id else None

        embed = discord.Embed(title="🎙️ 음성 채널 로그 설정", color=discord.Color.blue())
        embed.description = status_message
        embed.add_field(name="감시 중인 음성 채널", value=vc.mention if vc else "미설정", inline=False)
        embed.add_field(name="로그가 기록될 텍스트 채널", value=tc.mention if tc else "미설정", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class KeywordModal(discord.ui.Modal):
    def __init__(self, title: str, action: str):
        super().__init__(title=title)
        self.action = action
        self.keyword_input = discord.ui.TextInput(label="키워드", placeholder="등록하거나 삭제할 키워드를 입력하세요.")
        self.add_item(self.keyword_input)

    async def on_submit(self, interaction: discord.Interaction):
        keyword = self.keyword_input.value
        guild_id = str(interaction.guild.id)
        async with config_lock:
            config = load_config()
            if guild_id not in config:
                config[guild_id] = {"censored_keywords": []}
            if "censored_keywords" not in config[guild_id]:
                config[guild_id]["censored_keywords"] = []
            
            keywords = config[guild_id]["censored_keywords"]
            
            if self.action == 'add':
                if keyword not in keywords:
                    keywords.append(keyword)
                    save_config(config)
                    await interaction.response.send_message(f"✅ 키워드 '{keyword}' 추가 완료.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"⚠️ 이미 등록된 키워드입니다.", ephemeral=True)
            
            elif self.action == 'remove':
                if keyword in keywords:
                    keywords.remove(keyword)
                    save_config(config)
                    await interaction.response.send_message(f"🗑️ 키워드 '{keyword}' 삭제 완료.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❓ 등록되지 않은 키워드입니다.", ephemeral=True)

class PunishmentConfigModal(discord.ui.Modal):
    """처벌 임계값과 타임아웃 시간을 설정하는 모달"""
    def __init__(self, punishment_type: str):
        super().__init__(title="처벌 세부 설정")
        self.punishment_type = punishment_type

        self.threshold_input = discord.ui.TextInput(label="경고 횟수 (처벌 임계값)", placeholder="예: 3 (3번 적발 시 처벌)", required=True)
        self.add_item(self.threshold_input)

        if self.punishment_type == "timeout":
            self.duration_input = discord.ui.TextInput(label="타임아웃 시간 (분)", placeholder="예: 10 (10분간 타임아웃)", required=True)
            self.add_item(self.duration_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        try:
            threshold = int(self.threshold_input.value)
            if threshold <= 0: raise ValueError
        except ValueError:
            await interaction.response.send_message("경고 횟수는 0보다 큰 숫자로 입력해주세요.", ephemeral=True)
            return

        duration = 0
        if self.punishment_type == "timeout":
            try:
                duration = int(self.duration_input.value)
                if duration <= 0: raise ValueError
            except ValueError:
                await interaction.response.send_message("타임아웃 시간은 0보다 큰 숫자로 입력해주세요.", ephemeral=True)
                return

        async with config_lock:
            config = load_config()
            if guild_id not in config:
                config[guild_id] = {}
            
            config[guild_id]['punishment'] = {
                "type": self.punishment_type,
                "threshold": threshold,
                "timeout_duration_minutes": duration
            }
            save_config(config)
        await interaction.response.send_message(f"✅ 처벌 설정이 저장되었습니다.", ephemeral=True)


class PunishmentSettingsView(discord.ui.View):
    """처벌 종류를 선택하는 드롭다운 UI"""
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.select(
        placeholder="처벌 종류를 선택하세요",
        options=[
            discord.SelectOption(label="타임아웃", value="timeout", description="일정 시간 동안 채팅과 통화를 금지합니다."),
            discord.SelectOption(label="추방", value="kick", description="서버에서 내보냅니다. (재입장 가능)"),
            discord.SelectOption(label="차단", value="ban", description="서버에서 영구적으로 차단합니다."),
            discord.SelectOption(label="설정 안함", value="none", description="자동 처벌을 사용하지 않습니다."),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        punishment_type = select.values[0]
        
        if punishment_type == "none":
            async with config_lock:
                config = load_config()
                guild_id = str(interaction.guild.id)
                if guild_id not in config:
                    config[guild_id] = {}
                config[guild_id]['punishment'] = {"type": "none", "threshold": 0, "timeout_duration_minutes": 0}
                save_config(config)
            await interaction.response.send_message("✅ 자동 처벌을 사용하지 않도록 설정했습니다.", ephemeral=True)
        else:
            await interaction.response.send_modal(PunishmentConfigModal(punishment_type))

class WelcomeMessageModal(discord.ui.Modal, title="환영 메시지 편집"):
    """환영 메시지 내용을 편집하는 모달"""
    def __init__(self, current_message: str):
        super().__init__()
        self.message_input = discord.ui.TextInput(
            label="환영 메시지 (변수 사용 가능)",
            style=discord.TextStyle.paragraph,
            placeholder="예: {user_mention}님, {server_name}에 오신 것을 환영합니다!",
            default=current_message,
            max_length=1000
        )
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        async with config_lock:
            config = load_config()
            if guild_id not in config: config[guild_id] = {}
            if 'welcome_message' not in config[guild_id]: config[guild_id]['welcome_message'] = {}
            
            config[guild_id]['welcome_message']['message'] = self.message_input.value
            save_config(config)
        
        await interaction.response.send_message("✅ 환영 메시지가 성공적으로 저장되었습니다.", ephemeral=True)


class WelcomeSettingsView(discord.ui.View):
    """입장 환영 메시지 설정을 위한 UI 뷰"""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.guild_id = str(interaction.guild.id)

    @discord.ui.select(
        placeholder="환영 메시지 기능을 켜거나 끕니다.",
        options=[
            discord.SelectOption(label="켜기", value="true", description="새로운 멤버 입장 시 환영 메시지를 보냅니다."),
            discord.SelectOption(label="끄기", value="false", description="환영 메시지를 보내지 않습니다."),
        ],
        row=0
    )
    async def toggle_welcome(self, interaction: discord.Interaction, select: discord.ui.Select):
        enabled = select.values[0] == "true"
        async with config_lock:
            config = load_config()
            if self.guild_id not in config: config[self.guild_id] = {}
            if 'welcome_message' not in config[self.guild_id]: config[self.guild_id]['welcome_message'] = {}

            config[self.guild_id]['welcome_message']['enabled'] = enabled
            save_config(config)

        await self.update_and_respond(interaction, f"환영 메시지 기능이 {'✅ 켜졌습니다' if enabled else '❌ 꺼졌습니다'}.")

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="환영 메시지를 보낼 채널을 선택하세요.",
        row=1
    )
    async def channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        async with config_lock:
            config = load_config()
            if self.guild_id not in config: config[self.guild_id] = {}
            if 'welcome_message' not in config[self.guild_id]: config[self.guild_id]['welcome_message'] = {}

            config[self.guild_id]['welcome_message']['channel_id'] = channel.id
            save_config(config)

        await self.update_and_respond(interaction, f"환영 메시지 채널이 {channel.mention}(으)로 설정되었습니다.")

    @discord.ui.button(label="환영 메시지 편집", style=discord.ButtonStyle.primary, row=2)
    async def edit_message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config().get(self.guild_id, {})
        current_message = config.get('welcome_message', {}).get('message', "")
        await interaction.response.send_modal(WelcomeMessageModal(current_message))
    
    async def update_and_respond(self, interaction: discord.Interaction, status: str):
        # 응답 후 embed를 업데이트하기 위한 헬퍼 함수
        await interaction.response.defer(ephemeral=True)
        config = load_config().get(self.guild_id, {})
        welcome_config = config.get('welcome_message', {})

        is_enabled = welcome_config.get('enabled', False)
        channel_id = welcome_config.get('channel_id')
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        message = welcome_config.get('message', '미설정')

        embed = discord.Embed(title="👋 입장 환영 메시지 설정", description=status, color=discord.Color.green())
        embed.add_field(name="기능 상태", value="**🟢 켜짐**" if is_enabled else "⚫ 꺼짐", inline=True)
        embed.add_field(name="설정된 채널", value=channel.mention if channel else "미설정", inline=True)
        embed.add_field(name="설정된 메시지", value=f"```{message}```", inline=False)
        embed.set_footer(text="메시지에는 변수를 사용할 수 있습니다. (예: {user_mention})")
        
        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)


# -------------------- 슬래시 명령어 --------------------

@bot.tree.command(name="초기설정", description="봇 운영에 필요한 비공개 로그 채널을 생성하고 설정합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def initial_setup(interaction: discord.Interaction):
    guild = interaction.guild
    guild_id = str(guild.id)
    log_channel_name = "로그"
    existing_channel = discord.utils.get(guild.text_channels, name=log_channel_name)
    
    if existing_channel:
        log_channel = existing_channel
        await interaction.response.send_message(f"이미 '{log_channel_name}' 채널이 있어 해당 채널을 사용합니다.", ephemeral=True)
    else:
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), guild.me: discord.PermissionOverwrite(read_messages=True)}
        try:
            log_channel = await guild.create_text_channel(log_channel_name, overwrites=overwrites)
            await interaction.response.send_message(f"✅ 비공개 '{log_channel_name}' 채널을 생성했습니다.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 채널 생성 권한이 없습니다.", ephemeral=True)
            return
            
    async with config_lock:
        config = load_config()
        if guild_id not in config:
            config[guild_id] = {}
        config[guild_id]['text_channel_id'] = log_channel.id
        save_config(config)

@bot.tree.command(name="설정", description="음성 채널과 로그 채널 설정을 위한 패널을 엽니다.")
@app_commands.checks.has_permissions(administrator=True)
async def set_command(interaction: discord.Interaction):    
    config = load_config().get(str(interaction.guild.id), {})
    vc = interaction.guild.get_channel(config.get("voice_channel_id")) if config.get("voice_channel_id") else None
    tc = interaction.guild.get_channel(config.get("text_channel_id")) if config.get("text_channel_id") else None
    embed = discord.Embed(title="🎙️ 음성 채널 로그 설정", description="아래 드롭다운 메뉴에서 채널을 선택해 설정을 변경하세요.", color=discord.Color.blue())
    embed.add_field(name="감시 중인 음성 채널", value=vc.mention if vc else "미설정", inline=False)
    embed.add_field(name="로그가 기록될 텍스트 채널", value=tc.mention if tc else "미설정", inline=False)
    await interaction.response.send_message(embed=embed, view=SettingsView(interaction), ephemeral=True)

@bot.tree.command(name="입장", description="새로운 멤버를 위한 환영 메시지를 설정합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_settings(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    config = load_config().get(guild_id, {})
    welcome_config = config.get('welcome_message', {})

    is_enabled = welcome_config.get('enabled', False)
    channel_id = welcome_config.get('channel_id')
    channel = interaction.guild.get_channel(channel_id) if channel_id else None
    message = welcome_config.get('message', '미설정')

    embed = discord.Embed(title="👋 입장 환영 메시지 설정", description="아래 메뉴를 통해 환영 메시지 기능을 설정하세요.", color=discord.Color.green())
    embed.add_field(name="기능 상태", value="**🟢 켜짐**" if is_enabled else "⚫ 꺼짐", inline=True)
    embed.add_field(name="설정된 채널", value=channel.mention if channel else "미설정", inline=True)
    embed.add_field(name="설정된 메시지", value=f"```{message}```", inline=False)
    embed.set_footer(text="메시지에는 변수를 사용할 수 있습니다. (예: {user_mention})")

    await interaction.response.send_message(embed=embed, view=WelcomeSettingsView(interaction), ephemeral=True)

@bot.tree.command(name="검열추가", description="검열할 키워드를 추가합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def add_keyword(interaction: discord.Interaction):
    await interaction.response.send_modal(KeywordModal(title="검열 키워드 추가", action='add'))

@bot.tree.command(name="검열삭제", description="등록된 검열 키워드를 삭제합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def remove_keyword(interaction: discord.Interaction):
    await interaction.response.send_modal(KeywordModal(title="검열 키워드 삭제", action='remove'))

@bot.tree.command(name="검열목록", description="등록된 모든 검열 키워드를 확인합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def list_keywords(interaction: discord.Interaction):
    keywords = load_config().get(str(interaction.guild.id), {}).get("censored_keywords", [])
    if not keywords:
        await interaction.response.send_message("📝 등록된 검열 키워드가 없습니다.", ephemeral=True)
        return
    embed = discord.Embed(title="🚫 검열 키워드 목록", description="\n".join(f"- {word}" for word in keywords), color=discord.Color.orange())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="경고초기화", description="특정 사용자의 누적된 경고 횟수를 0으로 초기화합니다.")
@app_commands.describe(member="경고를 초기화할 서버 멤버를 선택하세요.")
@app_commands.checks.has_permissions(administrator=True)
async def reset_warnings(interaction: discord.Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    async with config_lock:
        config = load_config()
        if guild_id not in config or 'warning_counts' not in config[guild_id] or user_id not in config[guild_id]['warning_counts']:
            await interaction.response.send_message(f"✅ **{member.display_name}** 님은 초기화할 경고 기록이 없습니다.", ephemeral=True)
            return

        del config[guild_id]['warning_counts'][user_id]
        save_config(config)

    await interaction.response.send_message(f"✅ **{member.display_name}** 님의 경고 횟수를 성공적으로 초기화했습니다.", ephemeral=True)

    log_channel_id = load_config()[guild_id].get("text_channel_id")
    if log_channel_id:
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(title="ℹ️ 경고 초기화", description=f"관리자 **{interaction.user.display_name}** 님이 **{member.mention}** 님의 경고를 초기화했습니다.", color=discord.Color.light_grey())
            await log_channel.send(embed=embed)

@bot.tree.command(name="처벌설정", description="검열 적발 시 자동 처벌 규칙을 설정합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def punishment_settings(interaction: discord.Interaction):
    config = load_config().get(str(interaction.guild.id), {})
    punishment_config = config.get('punishment', {})
    
    ptype = punishment_config.get('type', 'none')
    threshold = punishment_config.get('threshold', 0)
    duration = punishment_config.get('timeout_duration_minutes', 0)

    type_map = {"none": "사용 안함", "timeout": "타임아웃", "kick": "추방", "ban": "차단"}
    
    embed = discord.Embed(title="⚔️ 자동 처벌 설정", description="현재 서버의 자동 처벌 규칙입니다.", color=discord.Color.red())
    embed.add_field(name="처벌 종류", value=type_map.get(ptype, "미설정"), inline=False)
    embed.add_field(name="적발 횟수", value=f"{threshold}회" if ptype != 'none' else "미설정", inline=True)
    if ptype == 'timeout':
        embed.add_field(name="타임아웃 시간", value=f"{duration}분" if ptype == 'timeout' else "미설정", inline=True)

    await interaction.response.send_message(embed=embed, view=PunishmentSettingsView(), ephemeral=True)

def format_duration(seconds):
    """초를 '시, 분, 초' 형태로 변환하는 함수 (소수점 둘째 자리까지)"""
    if seconds < 60:
        return f"{seconds:.2f}초"
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{int(hours)}시간 {int(minutes)}분 {seconds:.2f}초"
    else:
        return f"{int(minutes)}분 {seconds:.2f}초"

@bot.tree.command(name="랭킹", description="음성 채널 체류 시간 랭킹을 표시합니다.")
async def show_ranking(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    voice_time_data = load_config().get(guild_id, {}).get("voice_time_tracking", {})

    if not voice_time_data:
        await interaction.response.send_message("아직 음성 채널 체류 시간 기록이 없습니다.", ephemeral=True)
        return

    sorted_users = sorted(voice_time_data.items(), key=lambda item: item[1], reverse=True)
    embed = discord.Embed(title="🏆 음성 채널 활동 랭킹", color=discord.Color.gold())
    medals = ["🥇", "🥈", "🥉"]
    rank_description = []
    
    for i, (user_id, total_seconds) in enumerate(sorted_users[:10]):
        try:
            member = await interaction.guild.fetch_member(int(user_id))
            user_display_name = member.display_name
        except discord.NotFound:
            user_display_name = f"알 수 없는 유저 (ID: {user_id})"
        except Exception:
            user_display_name = f"유저 정보 로드 실패"

        formatted_time = format_duration(total_seconds)
        rank_entry = f"{medals[i] if i < len(medals) else f'**{i+1}위.**'} {user_display_name} - `{formatted_time}`"
        rank_description.append(rank_entry)

    embed.description = "\n".join(rank_description)
    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="명령어", description="봇의 모든 명령어 목록을 보여줍니다.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 봇 명령어", description="서버 운영을 돕는 봇의 명령어 목록입니다.", color=discord.Color.blurple())
    user_commands = (
        "`/명령어` : 봇의 명령어 목록을 확인합니다.\n"
        "`/랭킹` : 음성 채널 체류 시간 랭킹을 확인합니다."
    )
    embed.add_field(name="🙋‍♂️ 모든 사용자 명령어", value=user_commands, inline=False)
    admin_commands = (
        "**[ 채널 설정 ]**\n"
        "`/초기설정` : 봇 운영에 필요한 비공개 로그 채널을 생성합니다.\n"
        "`/설정` : 음성 채널 및 로그 채널을 설정하는 패널을 엽니다.\n"
        "`/입장` : 새로운 멤버를 위한 환영 메시지를 설정합니다.\n\n"
        "**[ 검열 및 처벌 ]**\n"
        "`/검열추가` : 검열할 키워드를 추가합니다.\n"
        "`/검열삭제` : 등록된 검열 키워드를 삭제합니다.\n"
        "`/검열목록` : 등록된 모든 검열 키워드를 확인합니다.\n"
        "`/처벌설정` : 검열 적발 시 자동 처벌 규칙을 설정합니다.\n"
        "`/경고초기화 [멤버]` : 특정 사용자의 경고 횟수를 초기화합니다."
    )
    embed.add_field(name="🛠️ 관리자 명령어", value=admin_commands, inline=False)
    embed.set_footer(text=f"{bot.user.name} | 궁금한 점이 있다면 서버 관리자에게 문의해주세요.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# -------------------- 봇 이벤트 핸들러 --------------------
@bot.event
async def on_ready():
    print(f'{bot.user} (으)로 로그인 성공!')
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

@bot.event
async def on_member_join(member: discord.Member):
    guild_id = str(member.guild.id)
    config = load_config().get(guild_id, {})
    welcome_config = config.get('welcome_message', {})

    if not welcome_config.get('enabled', False):
        return

    channel_id = welcome_config.get('channel_id')
    message_template = welcome_config.get('message')

    if not channel_id or not message_template:
        return

    channel = member.guild.get_channel(channel_id)
    if not channel:
        return

    # 변수들을 실제 값으로 치환
    formatted_message = message_template.format(
        user=member,
        server=member.guild,
        user_mention=member.mention,
        user_name=member.display_name,
        server_name=member.guild.name,
        member_count=member.guild.member_count
    )

    try:
        await channel.send(formatted_message)
    except discord.Forbidden:
        print(f"오류: '{member.guild.name}' 서버의 '{channel.name}' 채널에 메시지를 보낼 권한이 없습니다.")


@bot.event
async def on_voice_state_update(member, before, after):
    server_id = str(member.guild.id)
    config = load_config()
    server_config = config.get(server_id, {})
    
    target_voice_channel_id = server_config.get("voice_channel_id")
    if not target_voice_channel_id:
        return

    log_text_channel_id = server_config.get("text_channel_id")
    log_channel = bot.get_channel(log_text_channel_id) if log_text_channel_id else None

    is_join = not before.channel and after.channel and after.channel.id == target_voice_channel_id
    is_leave = before.channel and not after.channel and before.channel.id == target_voice_channel_id

    if is_join:
        voice_connections[member.id] = datetime.datetime.now()
        if log_channel:
            embed = discord.Embed(title="🎙️ 음성 채널 입장", description=f"**{member.display_name}** 님이 입장했습니다.", color=discord.Color.green())
            await log_channel.send(embed=embed)
    
    elif is_leave:
        if member.id in voice_connections:
            join_time = voice_connections.pop(member.id)
            duration = datetime.datetime.now() - join_time
            duration_seconds = duration.total_seconds()
            
            async with config_lock:
                config = load_config() 
                server_config = config.get(server_id, {})
                
                user_id = str(member.id)
                if 'voice_time_tracking' not in server_config:
                    server_config['voice_time_tracking'] = {}
                
                current_total_time = server_config['voice_time_tracking'].get(user_id, 0)
                server_config['voice_time_tracking'][user_id] = current_total_time + duration_seconds
                
                config[server_id] = server_config
                save_config(config)

            if log_channel:
                formatted_duration = format_duration(duration_seconds)
                embed = discord.Embed(title="🚫 음성 채널 퇴장", description=f"**{member.display_name}** 님이 퇴장했습니다.", color=discord.Color.red())
                embed.add_field(name="체류 시간", value=formatted_duration, inline=False)
                await log_channel.send(embed=embed)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    guild_id = str(message.guild.id)
    server_config = load_config().get(guild_id, {})
    
    keywords = server_config.get("censored_keywords", [])
    if not keywords:
        return

    for keyword in keywords:
        if keyword in message.content:
            log_channel_id = server_config.get("text_channel_id")
            log_channel = bot.get_channel(log_channel_id) if log_channel_id else None

            try:
                await message.delete()
            except discord.Forbidden:
                if log_channel: await log_channel.send(f"⚠️ **권한 오류:** {message.channel.mention}에서 메시지를 삭제할 수 없습니다.")
                return
            except discord.NotFound:
                return

            if log_channel:
                embed = discord.Embed(title="🚫 메시지 검열됨", color=discord.Color.gold(), timestamp=datetime.datetime.now())
                embed.description=f"**작성자:** {message.author.mention}\n**채널:** {message.channel.mention}"
                embed.add_field(name="삭제된 메시지", value=f"```{message.content}```", inline=False)
                embed.add_field(name="감지된 키워드", value=f"`{keyword}`", inline=False)
                await log_channel.send(embed=embed)

            punishment_config = server_config.get("punishment", {})
            if punishment_config.get("type", "none") != "none":
                async with config_lock:
                    config = load_config()
                    server_config = config.get(guild_id, {})
                    punishment_config = server_config.get("punishment", {})
                    threshold = punishment_config.get("threshold", 0)

                    if threshold > 0:
                        user_id = str(message.author.id)
                        if 'warning_counts' not in server_config:
                            server_config['warning_counts'] = {}
                        
                        current_warnings = server_config['warning_counts'].get(user_id, 0) + 1
                        server_config['warning_counts'][user_id] = current_warnings
                        
                        save_config(config)
                        
                        if current_warnings >= threshold:
                            server_config['warning_counts'][user_id] = 0
                            save_config(config)

                            reason = f"검열 규칙 위반 (경고 {threshold}회 누적)"
                            punishment_type = punishment_config.get("type")
                            
                            try:
                                action_log = ""
                                if punishment_type == "timeout":
                                    duration_minutes = punishment_config.get("timeout_duration_minutes", 10)
                                    duration = datetime.timedelta(minutes=duration_minutes)
                                    await message.author.timeout(duration, reason=reason)
                                    action_log = f"**{message.author.mention}** 님을 `{duration_minutes}`분 동안 타임아웃 처리했습니다."
                                
                                elif punishment_type == "kick":
                                    await message.author.kick(reason=reason)
                                    action_log = f"**{message.author.mention}** 님을 서버에서 추방했습니다."
                                    
                                elif punishment_type == "ban":
                                    await message.author.ban(reason=reason)
                                    action_log = f"**{message.author.mention}** 님을 서버에서 차단했습니다."

                                if log_channel and action_log:
                                    punishment_embed = discord.Embed(title="⚔️ 자동 처벌 실행", description=action_log, color=discord.Color.dark_red())
                                    punishment_embed.add_field(name="사유", value=reason)
                                    await log_channel.send(embed=punishment_embed)

                            except discord.Forbidden:
                                if log_channel: await log_channel.send(f"⚠️ **권한 오류:** {message.author.mention}님에게 처벌을 실행할 수 없습니다. 봇의 역할 순위나 권한을 확인해주세요.")
                        
                        else:
                            try:
                                await message.author.send(f"**[ {message.guild.name} ]** 서버에서 검열 키워드 사용이 감지되었습니다.\n> 현재 경고 횟수: **{current_warnings}/{threshold}**\n> 횟수 초과 시 처벌이 적용될 수 있습니다.")
                            except discord.Forbidden:
                                if log_channel: await log_channel.send(f"ℹ️ {message.author.mention}님에게 DM을 보낼 수 없어 경고를 전달하지 못했습니다.")
            
            break

# -------------------- 봇 실행 --------------------
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("오류: .env 파일에서 BOT_TOKEN을 찾을 수 없습니다.")