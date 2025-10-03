from .member_events import setup as setup_member_events
from .voice_events import setup as setup_voice_events
from .message_events import setup as setup_message_events

def setup_all_events(bot):
    """모든 이벤트 핸들러를 봇에 등록합니다."""
    setup_member_events(bot)
    setup_voice_events(bot)
    setup_message_events(bot)

__all__ = ['setup_all_events']
