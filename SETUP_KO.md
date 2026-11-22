# CMLab 홈페이지 미리보기 및 배포

## 로컬 실행

저장소 루트에서 `python3 -m http.server 8000`을 실행한 뒤 브라우저에서 `http://localhost:8000`을 엽니다. 별도 라이브러리 설치나 빌드는 필요하지 않습니다.

## 검토

데스크톱과 모바일에서 메뉴, 논문 검색과 필터, 연구 이미지와 영상, 링크를 확인합니다. [검토 기록](REVIEW.md)에 남은 논문, 구성원, 협력자, 뉴스의 출처 확인을 완료한 뒤 게시를 결정합니다. People에는 현재 직접 지도 중인 대학원생과 인턴을 기록합니다.

## 승인 후 배포

1. 승인된 변경을 사이트 저장소 `main`에 반영합니다.
2. Pages의 배포 소스를 아직 설정하지 않았다면 사이트 저장소의 **Settings → Pages → Build and deployment**에서 **GitHub Actions**를 선택합니다.
3. `main` 반영으로 시작한 워크플로를 확인합니다. 초기 설정 순서에 따라 다시 실행해야 하는 경우 **Actions → Deploy CMLab website to GitHub Pages**에서 `main`을 선택해 수동 실행합니다.
4. `https://cmlab-korea.github.io/`에서 사이트, 404 페이지와 실시간 통계 표기를 확인합니다.

기존 통계는 `cmlab-web-assets`의 공개 JavaScript를 읽습니다. 기존 통계 워크플로, 대학 DNS, 공식 도메인 및 Google Sites는 별도 승인 범위에 따릅니다. 데이터와 미디어 편집 위치는 [README.md](README.md), 지속 운영 지침은 [AGENTS.md](AGENTS.md)를 참고하세요.
