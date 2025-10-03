from .admin import AdminCog
from .moderation import ModerationCog
from .welcome import WelcomeCog
from .voice import VoiceCog

async def setup_all_cogs(bot):
    """모든 Cog를 봇에 등록합니다."""
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(ModerationCog(bot))
    await bot.add_cog(WelcomeCog(bot))
    await bot.add_cog(VoiceCog(bot))

__all__ = ['setup_all_cogs']
