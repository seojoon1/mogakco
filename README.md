# Discord 음성 채널 활동 로그 봇

특정 음성 채널에 사용자가 들어오거나 나갈 때 지정된 텍스트 채널에 로그를 남겨주는 간단한 디스코드 봇입니다.

## ✨ 주요 기능

-   **입장/퇴장 알림**: 지정된 음성 채널의 유저 활동을 실시간으로 추적합니다.
-   **채널 설정**: 슬래시 명령어 `/설정`을 통해 감시할 음성 채널과 로그를 남길 텍스트 채널을 쉽게 설정할 수 있습니다.

---

## ⚙️ 설치 및 설정 방법

이 봇을 직접 실행하기 위해선 아래의 과정이 필요합니다.

**1. 프로젝트 복제**
```bash
git clone [https://github.com/YourUsername/YourRepoName.git](https://github.com/YourUsername/YourRepoName.git)
cd YourRepoName
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
BOT_TOKEN="여기에_디스코드_개발자포털에서_받은_봇_토큰을_입력하세요"
```

**4. 봇 초대하기**
[Discord 개발자 포털](https://discord.com/developers/applications)에서 봇을 서버에 초대합니다.
-   **Scopes**: `bot`, `application.commands`
-   **필요 권한**: `Send Messages`, `Read Message History` 등 봇 기능에 필요한 권한

---

## ▶️ 봇 실행 방법

아래 명령어를 터미널에 입력하여 봇을 실행합니다.
```bash
python bot.py
```

---

## 📄 설정 파일

-   `config.json`: `/set` 명령어로 설정된 채널 ID가 이 파일에 자동으로 저장됩니다. 이 파일은 봇이 재시작되어도 설정을 기억하게 해줍니다.
