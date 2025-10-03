# Discord 마모키 모각코 봇

마모키 모각코 감시를 위해 만들었지만 디스코드 봇 공부를 위해 다양한 기능을 추가하고 있습니다.

## ✨ 주요 기능

-   **입장/퇴장 알림**: 지정된 음성 채널의 유저 활동을 실시간으로 추적합니다.
-   **채널 설정**: 슬래시 명령어 `/설정`을 통해 감시할 음성 채널과 로그를 남길 텍스트 채널을 쉽게 설정할 수 있습니다.
-   **초기 설정**: 슬래시 명령어 `/초기설정`을 통해 검열된 내용의 로그를 남길 텍스트 채널을 자동으로 설정합니다.
-   **검열**: 슬래시 명령어 `/검열추가, /검열삭제, /검열목록` 을 통해 검열 텍스트 추가, 삭제, 목록을 확인할 수 있습니다.
-   **처벌**: 슬래시 명령어 `/처벌설정` 을 통해 처벌 강도를 설정 가능합니다.
-   **경고 초기화**: 슬래시 명령어 `/경고초기화` 을 통해 해당 사용자의 경고를 초기화합니다.
-   **랭킹**: 슬래시 명령어 `/랭킹` 을 통해 설정을 통해 지정한 감시 음성 채널의 채류 랭킹을 확인 가능합니다 .
-   **명령어**: 슬래시 명령어 `/명령어` 를 사용가능한 명령어를 확인 가능합니다.
-   **입장**: 슬래시 명령어 `/입장` 을 사용하여 사용자가 입장시 환영메세지 출력 on/off, 환영인사 메세지 채널, 메세지 내용 설정이 가능합니다.



---

## ⚙️ 설치 및 설정 방법

이 봇을 직접 실행하기 위해선 아래의 과정이 필요합니다.

**1. 프로젝트 복제**
```bash
git clone [https://github.com/seojoon1/mogakco.git](https://github.com/seojoon1/mogakco.git)
cd mogakco
```

**2. 필요 라이브러리 설치**
봇을 실행하는 데 필요한 라이브러리들을 설치합니다.
```bash
pip install -r requirements.txt
```
> **Note**: `requirements.txt` 파일이 없다면, 터미널에서 `pip install discord.py python-dotenv`를 실행해주세요.

**3. `.env` 파일 생성**
프로젝트 폴더 최상단에 `.env` 파일을 만들고, 아래 내용과 같이 봇 토큰을 입력합니다. **이 파일은 절대로 깃허브에 올리면 안 됩니다!**
```
API_KEY="여기에_디스코드_개발자포털에서_받은_봇_토큰을_입력하세요"
```

**4. 봇 초대하기**
[Discord 개발자 포털](https://discord.com/developers/applications)에서 봇을 서버에 초대합니다.
-   **Scopes**: `bot`, `application.commands`
-   **필요 권한**: `Manage Channels`, `Manage Messages`, `Moderate Members`, `Kick Members`, `Ban Members`, `Send Messages`, `Read Message History` 등 봇 기능에 필요한 권한

---

## ▶️ 봇 실행 방법

아래 명령어를 터미널에 입력하여 봇을 실행합니다.
```bash
python bot_new.py
```

---

## 📄 설정 파일

-   `config.json`: `/설정` 명령어로 설정된 채널 ID가 이 파일에 자동으로 저장됩니다. 이 파일은 봇이 재시작되어도 설정을 기억하게 해줍니다.

---

## 🏗️ 프로젝트 구조

이 봇은 모듈화된 구조로 되어 있어 유지보수와 확장이 쉽습니다.

```
discordbotstudy/
├── bot_new.py              # 메인 실행 파일
├── config.json             # 설정 저장 파일
├── .env                    # 봇 토큰 (비공개)
├── requirements.txt        # 필요한 패키지 목록
├── utils/                  # 유틸리티 함수
│   ├── config_manager.py   # 설정 파일 관리
│   └── formatters.py       # 시간 포맷팅
├── views/                  # Discord UI 컴포넌트
│   ├── settings_view.py    # 채널 설정 UI
│   ├── welcome_view.py     # 환영 메시지 UI
│   ├── punishment_view.py  # 처벌 설정 UI
│   └── keyword_modal.py    # 키워드 모달
├── events/                 # 이벤트 핸들러
│   ├── member_events.py    # 멤버 입장 이벤트
│   ├── voice_events.py     # 음성 채널 이벤트
│   └── message_events.py   # 메시지 검열 이벤트
└── cogs/                   # 명령어 그룹 (Cogs)
    ├── admin.py            # 관리자 명령어
    ├── moderation.py       # 검열/처벌 명령어
    ├── welcome.py          # 환영 메시지 명령어
    └── voice.py            # 음성/일반 명령어
```

---

## 🔧 새로운 기능 추가하는 방법

### 1️⃣ 새로운 명령어 추가하기

**예시: `/인사` 명령어 추가**

#### Step 1: Cog 파일 생성 또는 기존 파일 수정

기존 Cog에 추가하거나 새 파일을 만듭니다.

**방법 A) 기존 파일에 추가** (`cogs/voice.py`)
```python
@app_commands.command(name="인사", description="봇이 인사합니다.")
async def greet(self, interaction: discord.Interaction):
    await interaction.response.send_message(f"안녕하세요 {interaction.user.mention}님! 👋")
```

**방법 B) 새 Cog 파일 생성** (`cogs/greeting.py`)
```python
import discord
from discord import app_commands
from discord.ext import commands

class GreetingCog(commands.Cog):
    """인사 관련 명령어"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="인사", description="봇이 인사합니다.")
    async def greet(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"안녕하세요 {interaction.user.mention}님! 👋")

async def setup(bot):
    await bot.add_cog(GreetingCog(bot))
```

#### Step 2: Cog 등록 (`cogs/__init__.py`)

새 파일을 만들었다면 `__init__.py`에 추가:
```python
from .greeting import GreetingCog

async def setup_all_cogs(bot):
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(ModerationCog(bot))
    await bot.add_cog(WelcomeCog(bot))
    await bot.add_cog(VoiceCog(bot))
    await bot.add_cog(GreetingCog(bot))  # 추가
```

### 2️⃣ 새로운 이벤트 핸들러 추가하기

**예시: 메시지 수정 감지**

#### Step 1: 이벤트 파일 생성 (`events/message_edit_events.py`)
```python
import discord
from utils import load_config

def setup(bot):
    @bot.event
    async def on_message_edit(before, after):
        if before.author.bot:
            return

        guild_id = str(before.guild.id)
        config = load_config().get(guild_id, {})
        log_channel_id = config.get('text_channel_id')

        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="✏️ 메시지 수정됨", color=discord.Color.blue())
                embed.add_field(name="이전", value=before.content[:1000], inline=False)
                embed.add_field(name="이후", value=after.content[:1000], inline=False)
                await log_channel.send(embed=embed)
```

#### Step 2: 이벤트 등록 (`events/__init__.py`)
```python
from .message_edit_events import setup as setup_message_edit_events

def setup_all_events(bot):
    setup_member_events(bot)
    setup_voice_events(bot)
    setup_message_events(bot)
    setup_message_edit_events(bot)  # 추가
```

### 3️⃣ 새로운 UI 컴포넌트 추가하기

**예시: 역할 선택 드롭다운**

#### Step 1: View 파일 생성 (`views/role_view.py`)
```python
import discord
from utils import load_config, save_config, config_lock

class RoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="역할을 선택하세요",
        min_values=1,
        max_values=1
    )
    async def role_select(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        role = select.values[0]
        await interaction.response.send_message(f"선택한 역할: {role.mention}", ephemeral=True)
```

#### Step 2: View 등록 (`views/__init__.py`)
```python
from .role_view import RoleSelectView

__all__ = [
    'SettingsView',
    'WelcomeSettingsView',
    'RoleSelectView',  # 추가
    # ...
]
```

### 4️⃣ 새로운 유틸리티 함수 추가하기

**예시: 날짜 포맷팅 함수**

#### Step 1: 유틸리티 파일 수정 (`utils/formatters.py`)
```python
from datetime import datetime

def format_date(dt: datetime):
    """날짜를 한국어 형식으로 포맷팅"""
    return dt.strftime("%Y년 %m월 %d일 %H:%M:%S")
```

#### Step 2: Export 추가 (`utils/__init__.py`)
```python
from .formatters import format_duration, format_date

__all__ = ['load_config', 'save_config', 'config_lock', 'CONFIG_FILE', 'format_duration', 'format_date']
```

---

## 💡 개발 팁

### ✅ 권장 사항
- 각 Cog는 하나의 기능 그룹만 담당하도록 설계
- 복잡한 UI는 별도의 View 클래스로 분리
- 공통 로직은 `utils/`에 함수로 추출
- 이벤트 핸들러는 `events/`에 분리

### 🔍 디버깅
- `print()` 대신 `logging` 모듈 사용 권장
- 에러 발생 시 로그 채널에 기록하는 습관

### 🚀 성능 최적화
- `config.json` 읽기는 최소화 (캐싱 고려)
- 무거운 작업은 `asyncio.create_task()` 사용

---

seojoon1