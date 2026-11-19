# TASK-022. Tailwind CSS 및 shadcn/ui 설정

## 상태
완료

## 날짜
2026-11-04

## 작업 요약
지금까지는 화면에 스타일이 전혀 없는 "맨몸" 상태였습니다. Tailwind CSS는 `bg-blue-500`, `px-4` 같은 짧은 클래스 이름만으로 디자인을 입힐 수 있게 해주는 도구이고, shadcn/ui는 그 위에 "버튼", "카드" 같은 자주 쓰는 UI 부품을 미리 예쁘게 만들어둔 코드 모음입니다. (npm 패키지를 설치하는 보통의 라이브러리와 달리, shadcn/ui는 컴포넌트 소스 코드 자체를 우리 프로젝트 안에 복사해 넣는 방식이라 자유롭게 고쳐 쓸 수 있습니다.)

최종적으로 구성한 것:
1. **`tailwind.config.js`**: 디자인 토큰(색상, 둥근 모서리 반경)을 CSS 변수와 연결하는 설정
2. **`src/index.css`**: 라이트/다크 모드별 색상 값(HSL)을 CSS 변수로 정의
3. **`postcss.config.js`**: Tailwind를 빌드 파이프라인에 연결
4. **`components.json`**: shadcn/ui 관례상의 설정 파일 (어떤 스타일/별칭을 쓰는지 기록)
5. **`src/lib/utils.ts`**: `cn()` 헬퍼 — 여러 클래스 이름을 조건부로 합치고 충돌을 정리해주는 함수
6. **`src/components/ui/button.tsx`**: shadcn/ui의 대표 컴포넌트인 Button (6가지 variant: default/destructive/outline/secondary/ghost/link)

## 변경 파일
- `frontend/tailwind.config.js` (신규 생성, 재작성됨 — 아래 기술 결정 참고)
- `frontend/postcss.config.js` (신규 생성)
- `frontend/src/index.css` (수정: Tailwind 지시문 + 라이트/다크 CSS 변수 추가)
- `frontend/components.json` (신규 생성)
- `frontend/src/lib/utils.ts` (신규 생성)
- `frontend/src/components/ui/button.tsx` (신규 생성)
- `frontend/package.json` (수정: `clsx`, `tailwind-merge`, `@radix-ui/react-slot`, `class-variance-authority`, `lucide-react` 추가)
- `frontend/src/components/_verify_tmp/DevTest.tsx` (수정: Button 시각 검증용 섹션 추가, 유지하기로 결정 — 비고 참고)

## TDD 결과
- Tailwind/shadcn 설정은 "실제로 스타일이 적용되고 빌드가 되는가"가 핵심이라, 설정 파일 작성 후 반드시 빌드와 실제 렌더링으로 검증했습니다.
  - **(1차 시도 실패)** 최신 `shadcn@latest init`(CLI 버전 4.23, "Nova" preset)으로 초기화하자 `border-border` 클래스가 존재하지 않는다는 **빌드 실패**가 발생했습니다. 원인 분석 끝에, 최신 CLI가 Tailwind v4 전용 방식(색상 토큰을 `tailwind.config.js` 없이 CSS만으로 처리)으로 설정을 생성했는데, 이 프로젝트는 quickstart.md에 따라 Tailwind **v3.3.0**(실제 설치 3.4.19)에 고정되어 있어 호환되지 않음을 발견했습니다. 구버전 CLI(`shadcn-ui`)는 완전히 폐기되어 실행 자체가 거부됨을 확인했습니다.
  - 사용자에게 "Tailwind v3 유지 + 수동 구성" vs "Tailwind v4로 업그레이드" 중 방향을 질문했고, **v3 유지**로 결정되어 진행했습니다.
  - **(2차 시도, 수동 구성)** 클래식 shadcn/ui 패턴(HSL CSS 변수 + `tailwind.config.js`의 `theme.extend.colors` 매핑)을 직접 작성
  - `eslint`, `prettier --check` 통과 (단, `button.tsx`에서 `react-refresh/only-export-components` 경고 1건 — 컴포넌트와 `buttonVariants`를 같은 파일에서 내보내는 shadcn/ui 공식 패턴이라 정상적인 경고로 간주)
  - `npm run build` 성공, CSS 산출물이 0.10kB → **7.91kB**로 증가(실제 Tailwind 유틸리티가 생성됨을 확인)
  - 빌드 산출물 CSS를 직접 grep해 `--primary: 221.2 83.2% 53.3%;`, `.bg-primary{background-color:hsl(var(--primary))}` 등 색상 토큰과 유틸리티가 정확히 생성됨을 확인
  - **실제 브라우저(Playwright) 렌더링 검증**: `/dev-test` 페이지에 Button의 7가지 상태(default/destructive/outline/secondary/ghost/link/disabled)를 임시로 렌더링하고 스크린샷으로 직접 확인 — 각 variant가 색상과 모양 모두 의도대로(파란색 채움/빨간색 채움/테두리만/회색/텍스트만/밑줄/반투명 비활성화) 표시됨을 시각적으로 검증
  - 검증 후 서버, 스크린샷 파일, Playwright가 남긴 임시 파일을 정리했습니다.
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (스타일/UI 컴포넌트 설정, 비즈니스 로직 아님)

## 기술 결정
- **Tailwind v3 유지, 최신 shadcn CLI 대신 수동 구성 (사용자 결정)**: 최신 `shadcn` 패키지(v4.23)는 Tailwind v4를 전제로 설계되어 있어, 이 프로젝트가 고정한 v3.3.0과 근본적으로 호환되지 않았습니다. 가장 안전한 선택은 CLI를 포기하고 수동으로 v3 호환 설정을 작성하는 것이었고, 실제로 사용자가 이 방향을 선택했습니다. 장점: quickstart.md의 명시적 버전 고정을 그대로 지키고, 지금까지 쌓아온 React 18/Vite 5/TS 5.3 스택과 완전히 호환됩니다.
- **`class-variance-authority`, `lucide-react`는 유지**: 두 패키지는 최신 CLI가 설치했지만, 클래식(v3) shadcn/ui 패턴에서도 그대로 쓰이는 표준 라이브러리라 재사용했습니다. 반면 `shadcn`(CLI 패키지 자체가 런타임 의존성으로 잘못 들어가 있었음), `cn`(Tailwind v4 전용 신생 패키지, Node ≥22 요구), `radix-ui`(통합 메타패키지, v4 preset 전용 구성), `tw-animate-css`, `@fontsource-variable/geist`는 전부 제거했습니다.
- **`@radix-ui/react-slot`만 개별 설치**: 통합 `radix-ui` 메타패키지 대신, 현재 필요한 Button의 `asChild` 기능에 필요한 `@radix-ui/react-slot`만 설치했습니다. 앞으로 다른 shadcn 컴포넌트(Dialog, DropdownMenu 등)가 필요해지면 그때 해당 Radix 패키지를 개별적으로 추가하는 방식으로, 불필요한 설치를 피했습니다(YAGNI).
- **`baseColor: "slate"`, 기본 라디우스 `0.5rem`**: shadcn/ui 클래식 기본값을 그대로 사용했습니다. 디자인 커스터마이징이 필요해지면 `src/index.css`의 CSS 변수 값만 바꾸면 됩니다.
- **Button 컴포넌트를 공식 shadcn/ui 클래식 소스와 동일하게 작성**: `forwardRef` + `cva` + `Slot`(asChild 패턴) 구조를 그대로 따라, 향후 공식 shadcn 레지스트리에서 다른 컴포넌트(Card, Dialog 등)를 추가할 때 동일한 관례를 유지할 수 있게 했습니다.

## 비고
- `/dev-test` 페이지(T020, T021에서도 사용된 임시 개발 도구 페이지)에 Button 시각 검증용 섹션을 **남겨두기로 결정**했습니다. 앞으로 다른 shadcn 컴포넌트를 추가할 때도 여기서 빠르게 렌더링을 확인할 수 있어 유용하다고 판단했습니다. 이 페이지 전체(`_verify_tmp/`)를 계속 개발용 도구로 쓸지, 나중에 정리할지는 아직 사용자와 최종 결정이 나지 않은 상태입니다.
- CLI 없이 수동으로 구성했기 때문에, 앞으로 새 shadcn 컴포넌트가 필요할 때(`npx shadcn add card` 등)도 CLI가 Tailwind v4 전용 코드를 생성할 가능성이 있습니다. 그때마다 이번처럼 Tailwind v3 문법(`has-*`, `in-*`, `color-mix()` 등 v4 전용 유틸리티 금지)으로 수동 변환이 필요할 수 있다는 점을 다음 작업자가 알아야 합니다.
- `npm audit` 기준 취약점 경고가 누적되고 있습니다(현재 25건, 대부분 오래된 pin 버전에서 기인). Polish 단계(T195 이후)에서 전체 재검토가 필요합니다.
