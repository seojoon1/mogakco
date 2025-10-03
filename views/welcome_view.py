import discord
import datetime
from string import Template
from utils import load_config, save_config, config_lock

class WelcomeMessageModal(discord.ui.Modal, title="환영 메시지 편집"):
    """환영 메시지 내용을 편집하는 모달"""
    def __init__(self, current_message: str, current_embed_enabled: bool = False):
        super().__init__()
        self.message_input = discord.ui.TextInput(
            label="환영 메시지 (변수 사용 가능)",
            style=discord.TextStyle.paragraph,
            placeholder="예: $user_mention님, $server_name에 오신 것을 환영합니다!\n현재 멤버 수: $member_count명",
            default=current_message,
            max_length=1000
        )
        self.add_item(self.message_input)

        self.embed_toggle = discord.ui.TextInput(
            label="임베드 사용 (true 또는 false)",
            placeholder="true 또는 false 입력",
            default="true" if current_embed_enabled else "false",
            max_length=5,
            required=False
        )
        self.add_item(self.embed_toggle)

        # 변수 도움말 추가
        self.variable_help = discord.ui.TextInput(
            label="📌 사용 가능한 변수 (입력 불필요)",
            style=discord.TextStyle.paragraph,
            placeholder="$user_mention: 멘션\n$user_name: 닉네임\n$user_id: ID\n$server_name: 서버명\n$server_id: 서버ID\n$member_count: 멤버수",
            default="$user_mention: 사용자 멘션 (@사용자)\n$user_name: 사용자 닉네임\n$user_id: 사용자 ID\n$server_name: 서버 이름\n$server_id: 서버 ID\n$member_count: 현재 멤버 수",
            required=False
        )
        self.add_item(self.variable_help)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        embed_enabled = self.embed_toggle.value.lower() == "true"

        async with config_lock:
            config = load_config()
            if guild_id not in config: config[guild_id] = {}
            if 'welcome_message' not in config[guild_id]: config[guild_id]['welcome_message'] = {}

            config[guild_id]['welcome_message']['message'] = self.message_input.value
            config[guild_id]['welcome_message']['use_embed'] = embed_enabled
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
        welcome_config = config.get('welcome_message', {})
        current_message = welcome_config.get('message', "")
        current_embed_enabled = welcome_config.get('use_embed', False)
        await interaction.response.send_modal(WelcomeMessageModal(current_message, current_embed_enabled))

    @discord.ui.button(label="미리보기", style=discord.ButtonStyle.secondary, row=2)
    async def preview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config().get(self.guild_id, {})
        welcome_config = config.get('welcome_message', {})
        message_template = welcome_config.get('message', '')
        use_embed = welcome_config.get('use_embed', False)

        if not message_template:
            await interaction.response.send_message("⚠️ 설정된 환영 메시지가 없습니다. 먼저 메시지를 작성해주세요.", ephemeral=True)
            return

        # 미리보기용 변수 치환
        try:
            formatted_message = Template(message_template).safe_substitute(
                user_mention=interaction.user.mention,
                user_name=interaction.user.display_name,
                user_id=interaction.user.id,
                server_name=interaction.guild.name,
                server_id=interaction.guild.id,
                member_count=interaction.guild.member_count,
                user=str(interaction.user),
                server=str(interaction.guild)
            )
        except Exception as e:
            await interaction.response.send_message(f"⚠️ 메시지 형식 오류: {e}", ephemeral=True)
            return

        if use_embed:
            embed = discord.Embed(
                description=formatted_message,
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            embed.set_author(name=f"{interaction.guild.name}에 오신 것을 환영합니다!", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await interaction.response.send_message("📬 **미리보기:**", embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"📬 **미리보기:**\n{formatted_message}", ephemeral=True)

    async def update_and_respond(self, interaction: discord.Interaction, status: str):
        # 응답 후 embed를 업데이트하기 위한 헬퍼 함수
        await interaction.response.defer(ephemeral=True)
        config = load_config().get(self.guild_id, {})
        welcome_config = config.get('welcome_message', {})

        is_enabled = welcome_config.get('enabled', False)
        channel_id = welcome_config.get('channel_id')
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        message = welcome_config.get('message', '미설정')
        use_embed = welcome_config.get('use_embed', False)

        embed = discord.Embed(title="👋 입장 환영 메시지 설정", description=status, color=discord.Color.green())
        embed.add_field(name="기능 상태", value="**🟢 켜짐**" if is_enabled else "⚫ 꺼짐", inline=True)
        embed.add_field(name="설정된 채널", value=channel.mention if channel else "미설정", inline=True)
        embed.add_field(name="임베드 사용", value="✅ 사용" if use_embed else "❌ 미사용", inline=True)
        embed.add_field(name="설정된 메시지", value=f"```{message}```", inline=False)
        embed.set_footer(text="사용 가능한 변수: $user_mention, $user_name, $user_id, $server_name, $server_id, $member_count")

        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
