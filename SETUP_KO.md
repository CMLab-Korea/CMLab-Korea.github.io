# CMLab 신규 GitHub 홈페이지 v1 설치 안내

## 1. 현재 상태

- **구현 완료:** 독립 실행형 GitHub Pages 홈페이지 1차 버전입니다.
- **미배포:** 기존 `https://cmlab.cau.ac.kr` 주소는 전혀 변경하지 않았습니다.
- **GitHub 접근 확인:** 연결된 계정으로 `CMLab-Korea/cmlab-web-assets`를 읽을 수 있었지만, `CMLab-Korea` 조직에 해당 GitHub 앱 설치가 없고 새 브랜치 생성이 GitHub 403 오류로 거부되었습니다.
- **새 저장소 생성:** 현재 GitHub 연동 작업에는 저장소 생성 기능이 없으므로 소유자가 먼저 저장소를 생성해야 합니다.

## 2. GitHub 조직 권한 확인

1. GitHub에서 `CMLab-Korea` 조직의 Settings를 엽니다.
2. `GitHub Apps / Installed GitHub Apps`에서 ChatGPT와 연결한 GitHub 앱을 조직에도 설치하거나 접근 대상 저장소를 지정합니다.
3. 연결된 앱에 Contents 쓰기 및 브랜치 생성에 필요한 저장소 접근이 부여되어 있는지 확인합니다.
4. 작업을 요청한 ChatGPT 대화로 돌아와 **조직 권한을 추가했으니 계속 업로드해 달라**고 요청할 수 있습니다. 연결에 따라 재인증이 필요할 수도 있습니다.

*중요*: 개인 계정에 연결하는 것과 GitHub 조직에 앱을 설치하는 것은 별개의 절차일 수 있습니다. 조직 관리자의 권한이 필요할 수 있습니다.

## 3. 새 저장소로 배포

1. `CMLab-Korea` GitHub 조직에 **public** 저장소 `CMLab-Korea.github.io`를 생성합니다.
2. 이 압축파일을 풀어 **폴더 안 파일들을 저장소 최상위**로 업로드합니다. `index.html`과 `.github/workflows/deploy.yml`이 저장소 루트에 있어야 합니다.
3. `Settings → Pages → Build and deployment → GitHub Actions`를 선택합니다.
4. `Actions → Deploy CMLab website to GitHub Pages → Run workflow`를 실행합니다.
5. 배포 결과와 `https://cmlab-korea.github.io/`에서 확인합니다.

**기존** `cmlab-web-assets` 저장소의 논문·Scholar 통계 자동화는 수정하지 마세요. 신규 사이트가 기존 공개 JS 파일을 참조하도록 구성되어 있습니다.

## 4. 배포 전 점검

- [ ] 전체 논문 28편 + 프리프린트 10편 제목과 연도, 링크 검수
- [ ] People 8+11+3명 현황과 표기 정확성 검수
- [ ] Recruitment 문구, 메일 주소 및 연락 방식 승인
- [ ] Research Vision 이미지의 최신본 여부 확인
- [ ] PC/모바일에서 로고, 이미지, 필터 동작 확인
- [ ] Google Scholar 및 논문 통계 숫자 정상 동작 확인
- [ ] 새로운 홈페이지 공개 주소 결정
- [ ] CAU 도메인은 DNS 관리자와 협의 전까지 변경하지 않기

## 5. 운영 방식

| 수정 항목 | 수정 파일 |
|---|---|
| 논문 | `data/publications.json` |
| 대학원생, 공동지도, 인턴 | `data/people.json` |
| 최근 소식 | `data/news.json` |
| 메인 내용 | `index.html` |
| 디자인 색상 | `assets/css/style.css` |
| 동작·필터 | `assets/js/site.js` |

GitHub Pages 기본 브랜치 `main`에 Commit하면 배포 워크플로가 자동 실행되도록 설정했습니다.

## 6. 현재 Google Sites에서 연결하기

새 주소를 먼저 배포·검증한 다음, 기존 Hero의 버튼 하나를 `Visit Main Website ↗`로 변경하여 새 GitHub 주소에 연결하세요. 최종적으로 중앙대학교가 허용하면 기존 `cmlab.cau.ac.kr` 도메인의 DNS를 신규 GitHub Pages 사이트로 전환할 수도 있습니다. 기존 `/publications`와 `/contact` 같은 하위 경로까지 검토하기 전에는 무작정 DNS를 바꾸지 마세요.
