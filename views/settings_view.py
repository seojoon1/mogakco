import discord
from utils import load_config, save_config, config_lock

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
