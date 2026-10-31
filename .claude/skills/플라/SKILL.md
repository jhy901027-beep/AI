---
description: Playwright MCP로 브라우저를 직접 조작하는 방법. 웹페이지 열기, 클릭·입력, 폼 작성, 스크린샷, 화면 정보 추출, 콘솔·네트워크 확인, 반응형 확인이 필요할 때 사용. "브라우저로 열어봐", "스크린샷 찍어줘", "이 사이트 눌러봐" 같은 요청에 사용.
argument-hint: "[URL 또는 할 일]"
---

# 플라: Playwright MCP 사용법

요청: $ARGUMENTS

## 기본 흐름
1. `browser_navigate`로 URL을 연다.
2. `browser_snapshot`으로 페이지의 접근성 트리를 읽는다. 각 요소의 `ref` 값을 여기서 얻는다.
3. 스냅샷에서 얻은 `ref`로 조작한다. 화면이 바뀌면 스냅샷을 다시 찍는다. 예전 `ref`는 쓰지 않는다.
4. 다 끝나면 `browser_close`로 브라우저를 닫는다.

## 도구 고르기
| 하고 싶은 일 | 도구 |
|---|---|
| 페이지 열기 / 뒤로 가기 | `browser_navigate` / `browser_navigate_back` |
| 구조·텍스트 읽기 | `browser_snapshot` (스크린샷보다 우선) |
| 요소 찾기 | `browser_find` |
| 클릭 / 마우스 올리기 / 드래그 | `browser_click` / `browser_hover` / `browser_drag` |
| 글자 입력 / 키 누르기 | `browser_type` / `browser_press_key` |
| 폼 여러 칸 한 번에 / 드롭다운 | `browser_fill_form` / `browser_select_option` |
| 파일 업로드 | `browser_file_upload` |
| 기다리기 (글자 등장·사라짐, 시간) | `browser_wait_for` |
| 화면 캡처 | `browser_take_screenshot` |
| DOM·JS 값 읽기 | `browser_evaluate` |
| 콘솔 오류 / 네트워크 요청 | `browser_console_messages` / `browser_network_requests`, `browser_network_request` |
| 창 크기 바꾸기 (반응형) | `browser_resize` (모바일 375×812, 데스크톱 1440×900) |
| 탭 열기·전환·닫기 | `browser_tabs` |
| 알림창(alert/confirm) 처리 | `browser_handle_dialog` |

## 규칙
- **읽기는 스냅샷 먼저**: 텍스트·구조는 `browser_snapshot`으로 읽는다. 스크린샷은 눈으로 봐야 할 때(디자인, 레이아웃 확인)만 찍는다.
- **되돌릴 수 없는 동작 금지**: 결제, 회원가입, 로그인, 글쓰기, 댓글, 삭제, 메일 발송처럼 외부에 남는 동작은 사용자가 명확히 시킨 경우에만 한다. 애매하면 먼저 묻는다.
- **봇 차단·캡차는 우회하지 않는다**: 막히면 막힌 사실과 확인한 범위만 알린다.
- **`browser_run_code_unsafe`는 쓰지 않는다**: 필요한 값은 `browser_evaluate`로 읽는다.
- **브라우저는 하나다**: 여러 에이전트가 동시에 Playwright를 쓰면 서로 페이지를 덮어쓴다. 백그라운드 작업은 한 번에 하나씩 순서대로 실행한다.
- **저장**: 스크린샷이나 결과 파일은 프로젝트 안 한글 폴더에 한글 이름으로 저장한다 (예: `스크린샷/나무위키_메인.png`, `웹구조분석/티스토리_구조.md`).

## 자주 쓰는 `browser_evaluate` 예시
```js
// 사용 기술 확인
() => ({ vue: !!window.__VUE__, react: !!document.querySelector('[data-reactroot], #__next'), next: !!window.__NEXT_DATA__, jquery: !!window.jQuery })

// 로드된 스크립트·스타일시트
() => ({ scripts: [...document.scripts].map(s => s.src).filter(Boolean), css: [...document.styleSheets].map(s => s.href).filter(Boolean) })

// 가로 넘침 확인 (반응형)
() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth })
```

## 큰 분석은 에이전트에게
사이트 전체의 구조·기능·코드를 분석해 보고서로 남겨야 하면 `웹구조` 서브에이전트에게 맡긴다. 이 스킬은 메인 대화에서 바로 브라우저를 조작할 때 쓴다.
