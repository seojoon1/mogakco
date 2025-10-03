import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, format_duration

class VoiceCog(commands.Cog):
    """음성 채널 관련 명령어"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="랭킹", description="음성 채널 체류 시간 랭킹을 표시합니다.")
    async def show_ranking(self, interaction: discord.Interaction):
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

    @app_commands.command(name="명령어", description="봇의 모든 명령어 목록을 보여줍니다.")
    async def help_command(self, interaction: discord.Interaction):
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
        embed.set_footer(text=f"{self.bot.user.name} | 궁금한 점이 있다면 서버 관리자에게 문의해주세요.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
