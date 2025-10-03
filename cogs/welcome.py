import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config
from views import WelcomeSettingsView

class WelcomeCog(commands.Cog):
    """환영 메시지 관련 명령어"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="입장", description="새로운 멤버를 위한 환영 메시지를 설정합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_settings(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        config = load_config().get(guild_id, {})
        welcome_config = config.get('welcome_message', {})

        is_enabled = welcome_config.get('enabled', False)
        channel_id = welcome_config.get('channel_id')
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        message = welcome_config.get('message', '미설정')
        use_embed = welcome_config.get('use_embed', False)

        embed = discord.Embed(title="👋 입장 환영 메시지 설정", description="아래 메뉴를 통해 환영 메시지 기능을 설정하세요.", color=discord.Color.green())
        embed.add_field(name="기능 상태", value="**🟢 켜짐**" if is_enabled else "⚫ 꺼짐", inline=True)
        embed.add_field(name="설정된 채널", value=channel.mention if channel else "미설정", inline=True)
        embed.add_field(name="임베드 사용", value="✅ 사용" if use_embed else "❌ 미사용", inline=True)
        embed.add_field(name="설정된 메시지", value=f"```{message}```", inline=False)
        embed.set_footer(text="사용 가능한 변수: $user_mention, $user_name, $user_id, $server_name, $server_id, $member_count")

        await interaction.response.send_message(embed=embed, view=WelcomeSettingsView(interaction), ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
