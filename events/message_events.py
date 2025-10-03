import discord
import datetime
from utils import load_config, save_config, config_lock

def setup(bot):
    """메시지 관련 이벤트 핸들러를 등록합니다."""

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
