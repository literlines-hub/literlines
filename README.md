# 인스타그램 자동 게시 설정 가이드 (곧은 한 줄)

페이스북 페이지 없이, 인스타그램 로그인만으로 자동 게시하는 방식이에요.
게시는 GitHub(무료)가 정해진 시간에 대신 올려 줘요. 혜강님이 한 번만 하면 되는 일은 아래 4단계예요.

## 1. GitHub 저장소 만들기 (5분)
1. github.com 에서 가입 또는 로그인
2. 오른쪽 위 + → New repository
3. 이름: 예) gotgeun-hanjul / Public 선택 / Create repository
   - Public이어야 인스타그램이 이미지 주소를 읽을 수 있어요. 올라가는 건 어차피 공개할 슬라이드와 캡션뿐이에요.
4. https://claude.ai/connect-github 에서 GitHub 연결 후, 저장소 이름을 Claude에게 알려 주세요. 파일은 Claude가 올려요.

## 2. Meta 개발자 앱 만들기 (10분)
1. developers.facebook.com 접속 → 로그인 (Meta 계정 필요, 페이스북 페이지는 필요 없음)
2. 내 앱 → 앱 만들기
3. 사용 사례: "Instagram에서 메시지 및 콘텐츠 관리" 선택 → 앱 이름 입력 → 만들기
4. 왼쪽 메뉴 Instagram → "Instagram 로그인을 사용한 API 설정"
5. "액세스 토큰 생성"에서 계정 추가 → 인스타그램 로그인 → 권한 허용
   - 테스터 초대가 뜨면: 인스타그램 앱 → 설정 → 웹사이트 권한 → 앱 및 웹사이트 → 테스터 초대 → 수락
6. "토큰 생성"을 누르면 긴 글자(토큰)가 나와요 → 복사

## 3. 토큰을 GitHub에 안전하게 저장 (2분)
**토큰은 Claude에게 채팅으로 보내지 마세요. 비밀번호도 마찬가지예요.**
1. 만든 GitHub 저장소 → Settings → Secrets and variables → Actions
2. New repository secret
3. Name: IG_TOKEN / Secret: 복사한 토큰 붙여넣기 → Add secret

## 4. 인스타그램 아이디 알려 주기
표지에 @아이디로 표시돼요.

---
### 그다음부터
- 혜강님: 글 보내기 + Claude가 만든 슬라이드 확인 후 "올려도 돼" 하기
- Claude: 슬라이드 제작 → 저장소에 업로드 → 승인된 게시물만 예약 시간에 자동 게시
- 토큰은 60일마다 만료돼요. 50일쯤 됐을 때 2단계의 6번만 다시 해서 3단계처럼 IG_TOKEN을 교체하면 돼요.
