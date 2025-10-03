import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, save_config, config_lock
from views import KeywordModal, PunishmentSettingsView

class ModerationCog(commands.Cog):
    """검열 및 처벌 관련 명령어"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="검열추가", description="검열할 키워드를 추가합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_keyword(self, interaction: discord.Interaction):
        await interaction.response.send_modal(KeywordModal(title="검열 키워드 추가", action='add'))

    @app_commands.command(name="검열삭제", description="등록된 검열 키워드를 삭제합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_keyword(self, interaction: discord.Interaction):
        await interaction.response.send_modal(KeywordModal(title="검열 키워드 삭제", action='remove'))

    @app_commands.command(name="검열목록", description="등록된 모든 검열 키워드를 확인합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_keywords(self, interaction: discord.Interaction):
        keywords = load_config().get(str(interaction.guild.id), {}).get("censored_keywords", [])
        if not keywords:
            await interaction.response.send_message("📝 등록된 검열 키워드가 없습니다.", ephemeral=True)
            return
        embed = discord.Embed(title="🚫 검열 키워드 목록", description="\n".join(f"- {word}" for word in keywords), color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="경고초기화", description="특정 사용자의 누적된 경고 횟수를 0으로 초기화합니다.")
    @app_commands.describe(member="경고를 초기화할 서버 멤버를 선택하세요.")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_warnings(self, interaction: discord.Interaction, member: discord.Member):
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
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="ℹ️ 경고 초기화", description=f"관리자 **{interaction.user.display_name}** 님이 **{member.mention}** 님의 경고를 초기화했습니다.", color=discord.Color.light_grey())
                await log_channel.send(embed=embed)

    @app_commands.command(name="처벌설정", description="검열 적발 시 자동 처벌 규칙을 설정합니다.")
    @app_commands.checks.has_permissions(administrator=True)
    async def punishment_settings(self, interaction: discord.Interaction):
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

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
