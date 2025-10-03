import discord
import datetime
from utils import load_config, save_config, config_lock, format_duration

# 사용자의 음성 채널 접속 시간을 기록하는 딕셔너리
voice_connections = {}

def setup(bot):
    """음성 채널 관련 이벤트 핸들러를 등록합니다."""

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
