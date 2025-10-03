import discord
import datetime
from string import Template
from utils import load_config

def setup(bot):
    """멤버 관련 이벤트 핸들러를 등록합니다."""

    @bot.event
    async def on_member_join(member: discord.Member):
        guild_id = str(member.guild.id)
        config = load_config().get(guild_id, {})
        welcome_config = config.get('welcome_message', {})

        if not welcome_config.get('enabled', False):
            return

        channel_id = welcome_config.get('channel_id')
        message_template = welcome_config.get('message')
        use_embed = welcome_config.get('use_embed', False)

        if not channel_id or not message_template:
            return

        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        # 변수 치환 (safe_substitute 사용하여 오류 방지)
        try:
            formatted_message = Template(message_template).safe_substitute(
                user_mention=member.mention,
                user_name=member.display_name,
                user_id=member.id,
                server_name=member.guild.name,
                server_id=member.guild.id,
                member_count=member.guild.member_count,
                user=str(member),
                server=str(member.guild)
            )
        except Exception as e:
            print(f"환영 메시지 변수 치환 오류: {e}")
            return

        # 로그 채널 가져오기
        log_channel_id = config.get('text_channel_id')
        log_channel = member.guild.get_channel(log_channel_id) if log_channel_id else None

        try:
            if use_embed:
                # 임베드 메시지 전송
                embed = discord.Embed(
                    description=formatted_message,
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_author(
                    name=f"{member.guild.name}에 오신 것을 환영합니다!",
                    icon_url=member.guild.icon.url if member.guild.icon else None
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=embed)
            else:
                # 일반 텍스트 메시지 전송
                await channel.send(formatted_message)

            # 로그 채널에 기록
            if log_channel:
                log_embed = discord.Embed(
                    title="👋 환영 메시지 전송됨",
                    description=f"**멤버:** {member.mention} ({member.id})\n**채널:** {channel.mention}",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                log_embed.add_field(name="전송된 메시지", value=f"```{formatted_message[:1000]}```", inline=False)
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            print(f"오류: '{member.guild.name}' 서버의 '{channel.name}' 채널에 메시지를 보낼 권한이 없습니다.")
            # 로그 채널에 오류 기록
            if log_channel:
                error_embed = discord.Embed(
                    title="⚠️ 환영 메시지 전송 실패",
                    description=f"**멤버:** {member.mention}\n**사유:** 권한 부족",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                await log_channel.send(embed=error_embed)
        except Exception as e:
            print(f"환영 메시지 전송 중 오류: {e}")
            # 로그 채널에 오류 기록
            if log_channel:
                error_embed = discord.Embed(
                    title="⚠️ 환영 메시지 전송 실패",
                    description=f"**멤버:** {member.mention}\n**사유:** {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                await log_channel.send(embed=error_embed)
