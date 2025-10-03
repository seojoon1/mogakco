import discord
from utils import load_config, save_config, config_lock

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
