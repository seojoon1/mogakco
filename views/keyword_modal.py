import discord
from utils import load_config, save_config, config_lock

class KeywordModal(discord.ui.Modal):
    def __init__(self, title: str, action: str):
        super().__init__(title=title)
        self.action = action
        self.keyword_input = discord.ui.TextInput(label="키워드", placeholder="등록하거나 삭제할 키워드를 입력하세요.")
        self.add_item(self.keyword_input)

    async def on_submit(self, interaction: discord.Interaction):
        keyword = self.keyword_input.value
        guild_id = str(interaction.guild.id)
        async with config_lock:
            config = load_config()
            if guild_id not in config:
                config[guild_id] = {"censored_keywords": []}
            if "censored_keywords" not in config[guild_id]:
                config[guild_id]["censored_keywords"] = []

            keywords = config[guild_id]["censored_keywords"]

            if self.action == 'add':
                if keyword not in keywords:
                    keywords.append(keyword)
                    save_config(config)
                    await interaction.response.send_message(f"✅ 키워드 '{keyword}' 추가 완료.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"⚠️ 이미 등록된 키워드입니다.", ephemeral=True)

            elif self.action == 'remove':
                if keyword in keywords:
                    keywords.remove(keyword)
                    save_config(config)
                    await interaction.response.send_message(f"🗑️ 키워드 '{keyword}' 삭제 완료.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❓ 등록되지 않은 키워드입니다.", ephemeral=True)
