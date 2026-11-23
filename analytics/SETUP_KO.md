# CMLab 홈페이지 방문 통계 연결하기

홈페이지 하단에 누적 방문자와 오늘 방문자 수를 표시합니다. **Visitor statistics**를 펼치면 국가별·페이지별 방문자 수도 볼 수 있습니다. GitHub Pages는 홈페이지 파일을 보여주고, 방문 횟수는 CMLab이 관리하는 Cloudflare 계정에 저장합니다.

- **D1**은 방문 기록을 넣어 두는 표입니다.
- **Worker**는 홈페이지에서 방문 신호를 받아 그 표를 업데이트하고 숫자를 돌려주는 작은 프로그램입니다.
- **DB 연결**은 Worker가 어떤 D1 표를 사용할지 지정하는 설정입니다.

## 1. Cloudflare에서 방문 기록 표 만들기

1. [Cloudflare 대시보드](https://dash.cloudflare.com/)에 로그인합니다. CMLab이 관리할 계정을 선택합니다.
2. 왼쪽에서 **Storage & databases → D1**을 열고 **Create database**를 누릅니다. 메뉴가 달라 보이면 대시보드에서 `D1`을 검색합니다.
3. 이름을 `cmlab-visitors`로 정해 만듭니다. 목록에서 새 데이터베이스를 열고 **Console** 탭으로 이동합니다.
4. [schema.sql](schema.sql)을 열어 내용을 전부 복사합니다. Console에 붙여넣고 **Execute**를 누릅니다. 완료되면 `visitors`와 `visits` 표가 생깁니다.

## 2. 방문 숫자를 보내주는 Worker 만들기

1. [Cloudflare 대시보드](https://dash.cloudflare.com/)의 **Workers & Pages**에서 **Create application → Start with Hello World!**를 선택합니다. Worker 이름은 `cmlab-visitor-counter`처럼 지정하고 **Deploy**를 누릅니다.
2. 만든 Worker를 열고 **Edit code**를 누릅니다. 예제 코드 전체를 지우고 [worker.js](worker.js) 내용을 그대로 붙인 뒤 **Deploy**를 누릅니다.
3. Worker의 **Bindings** 탭 또는 **Settings → Bindings**에서 **Add binding → D1 database**를 선택합니다. **Variable name**에는 정확히 `DB`를 입력하고, **D1 database**에는 1단계에서 만든 `cmlab-visitors`를 고릅니다. **Add binding** 또는 **Save and deploy**를 눌러 적용합니다.
4. Worker 화면에서 `https://…workers.dev` 주소를 복사합니다. 처음 생성하는 계정은 Cloudflare가 `workers.dev` 하위 주소를 정하라고 안내할 수 있습니다.

## 3. Worker 주소를 GitHub에 연결하기

복사한 주소 뒤에 `/visitors`를 붙여 [data/visitor-settings.json](../data/visitor-settings.json)의 `endpoint`에 넣습니다.

```json
{
  "endpoint": "https://cmlab-visitor-counter.계정하위주소.workers.dev/visitors"
}
```

위 예시의 `계정하위주소` 부분까지 실제 Cloudflare 주소로 바꿉니다. Worker 주소를 Codex에 알려주면 이 파일과 PR을 준비할 수 있습니다. Cloudflare 비밀번호나 토큰은 필요 없습니다. PR을 병합한 뒤 GitHub Pages 배포가 완료되면 사이트 하단에서 확인합니다.

## 4. 화면에서 확인하기

1. [CMLab 홈](https://cmlab-korea.github.io/) 하단에 **Total visitors**와 **Today** 숫자가 표시되는지 확인합니다.
2. 같은 브라우저에서 Publications 또는 Projects도 방문하고 하단의 **Visitor statistics**를 엽니다. 방문한 각 페이지가 **Pages**에 표시되고, 브라우저는 사이트 전체에서 한 번 집계됩니다.
3. 숫자 대신 대시가 계속 보이면 Worker 주소 끝의 `/visitors`와 **DB** 연결 이름을 확인합니다. Worker 주소는 사이트에서 호출할 때 동작하므로 주소창에 직접 붙이면 404가 표시됩니다.

집계는 연결 이후부터 시작합니다. **Today**는 서울 기준 자정에 바뀝니다. 같은 브라우저는 임의 ID로 구분하며, 사이트의 집계 코드는 개인 IP 주소를 읽거나 저장하지 않습니다.

외부 서비스로 바꾸고 싶다면 [VisitorBadge.io](https://visitorbadge.io/)나 [MapMyVisitors](https://mapmyvisitors.com/)에서 **CMLab 홈페이지용 집계 주소**를 따로 만들 수 있습니다. VisitorBadge는 작은 숫자 배지에, MapMyVisitors는 국가별 방문 지도에 적합합니다. 현재 하단의 누적·오늘·국가·페이지 집계를 모두 활용하려면 위 Cloudflare 연결이 맞습니다.
