import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, save_config, config_lock
from views import SettingsView

class AdminCog(commands.Cog):
    """관리자 설정 관련 명령어"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="초기설정", description="봇 운영에 필요한 비공개 로그 채널을 생성하고 설정합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def initial_setup(self, interaction: discord.Interaction):
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

    @app_commands.command(name="설정", description="음성 채널과 로그 채널 설정을 위한 패널을 엽니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_command(self, interaction: discord.Interaction):
        config = load_config().get(str(interaction.guild.id), {})
        vc = interaction.guild.get_channel(config.get("voice_channel_id")) if config.get("voice_channel_id") else None
        tc = interaction.guild.get_channel(config.get("text_channel_id")) if config.get("text_channel_id") else None
        embed = discord.Embed(title="🎙️ 음성 채널 로그 설정", description="아래 드롭다운 메뉴에서 채널을 선택해 설정을 변경하세요.", color=discord.Color.blue())
        embed.add_field(name="감시 중인 음성 채널", value=vc.mention if vc else "미설정", inline=False)
        embed.add_field(name="로그가 기록될 텍스트 채널", value=tc.mention if tc else "미설정", inline=False)
        await interaction.response.send_message(embed=embed, view=SettingsView(interaction), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
