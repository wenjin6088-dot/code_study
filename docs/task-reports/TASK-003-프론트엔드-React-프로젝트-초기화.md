# TASK-003. 프론트엔드 React 프로젝트 초기화

## 상태
완료

## 날짜
2026-10-29

## 작업 요약
사용자가 실제로 마주하게 될 화면(프론트엔드)의 뼈대를 세웠습니다. 백엔드를 "주방"이라 하면, 프론트엔드는 손님이 앉아서 음식을 받아보는 "홀"에 해당합니다. 이번 작업으로 그 홀의 기본 테이블과 조명을 설치한 것입니다.

구체적으로:

1. **패키지 목록 작성** (`frontend/package.json`): quickstart.md에 정의된 라이브러리들을 담았습니다. 화면을 그리는 React, 페이지 이동을 담당할 react-router-dom, 서버 데이터를 효율적으로 가져오는 TanStack Query, 가벼운 상태 저장소 Zustand, 코드 에디터 Monaco, API 호출용 axios, 그리고 테스트 도구(Vitest, Testing Library)와 디자인 도구(Tailwind CSS) 등입니다. 이 라이브러리들을 "설치"는 지금 완료했지만, 실제로 코드 안에서 "사용"하는 것은 각각의 후속 Task(T018 라우터, T019 쿼리 클라이언트, T020 API 클라이언트, T021 상태 저장소, T022 Tailwind 설정 등)에서 진행합니다. 이는 T002에서 백엔드 requirements.txt를 한 번에 설치하고, 이후 각 서비스 Task에서 그 라이브러리를 사용한 것과 같은 패턴입니다.
2. **Vite + TypeScript 설정**: `vite.config.ts`(개발 서버/빌드 설정), `tsconfig.json`(타입 검사 규칙), `index.html`(화면의 첫 진입점) 파일을 만들었습니다.
3. **최소 실행 화면**: `src/main.tsx`(React를 화면에 "꽂는" 코드), `src/App.tsx`(지금은 제목만 보여주는 placeholder), `src/index.css`(기본 스타일 초기화)를 만들었습니다. App.tsx의 실제 내용(라우팅, 레이아웃)은 T018에서 채워집니다.
4. **설치 및 검증**: `npm install`로 실제 패키지를 내려받고, `npm run build`(타입 체크 + 프로덕션 빌드)가 에러 없이 끝나는지 확인했습니다.

## 변경 파일
- `frontend/package.json` (신규 생성)
- `frontend/package-lock.json` (신규 생성, npm install 결과)
- `frontend/vite.config.ts` (신규 생성)
- `frontend/tsconfig.json` (신규 생성)
- `frontend/index.html` (신규 생성)
- `frontend/src/main.tsx` (신규 생성)
- `frontend/src/App.tsx` (신규 생성)
- `frontend/src/index.css` (신규 생성)
- `frontend/src/vite-env.d.ts` (신규 생성)
- `frontend/node_modules/` (신규 생성, npm install 결과 — 코드 추적 대상 아님)

## TDD 결과
- 프로젝트 초기화(패키지 설치, 빌드 설정)는 테스트로 검증할 비즈니스 로직이 없어 RED-GREEN-REFACTOR 사이클은 적용하지 않았습니다. 대신 "실제로 빌드가 성공하는가"를 수동으로 검증하는 방식으로 정확성을 확인했습니다 (`npm run build` → 타입 에러 0건, 빌드 성공).
- 저장소가 아직 git으로 초기화되지 않아 관련 커밋은 생성하지 않았습니다.
- 테스트 커버리지: 해당 없음 (비즈니스 로직 코드 없음, 테스트 파일도 아직 없음)

## 기술 결정
- **`tsc -b` (프로젝트 참조 빌드 모드) 대신 `tsc --noEmit` 사용**: 처음에는 최신 Vite 템플릿 스타일로 `tsconfig.json`(src용)과 `tsconfig.node.json`(vite.config.ts용)을 분리하고 `tsc -b`로 빌드하려 했습니다. 하지만 우리가 고정한 TypeScript 5.3 버전에서는 "참조되는 프로젝트는 noEmit을 켤 수 없다"(TS6310)는 제약이 있어, `composite: true`와 `noEmit: true`를 함께 쓴 `tsconfig.node.json`이 에러를 냈습니다. 이를 우회하려고 noEmit을 빼자, 이번엔 tsc가 실제로 `vite.config.js`/`vite.config.d.ts` 같은 빌드 산출물을 프로젝트 폴더에 그대로 남기는 부작용이 발생했습니다. 최종적으로는 `tsconfig.node.json`을 없애고 `tsconfig.json` 하나로 `src`와 `vite.config.ts`를 모두 포함시킨 뒤, 빌드 스크립트를 `tsc --noEmit && vite build`로 바꿔 타입 검사만 하고 파일은 만들지 않도록 단순화했습니다. 더 단순하고, 우리가 고정한 TS 5.3에서도 안정적으로 동작합니다.
- **`@types/node` 추가**: `vite.config.ts`에서 경로 별칭(`@/*` → `src/*`)을 설정하기 위해 Node.js의 `path`, `__dirname`을 사용했는데, 이를 TypeScript가 인식하려면 `@types/node`가 필요했습니다. quickstart.md의 원래 목록에는 없었지만, Vite 설정 파일 자체가 Node.js 환경에서 실행되므로 꼭 필요한 타입 패키지라 추가했습니다.
- **Tailwind CSS는 설치만, 설정은 보류**: `tailwindcss`, `postcss`, `autoprefixer`를 devDependencies에 포함했지만 `tailwind.config.js`나 `postcss.config.js`는 만들지 않았습니다. 이는 tasks.md의 T022("Configure Tailwind CSS and install shadcn/ui components")가 명시적으로 이 설정을 담당하는 별도 Task이기 때문입니다.
- **shadcn/ui, ESLint 설정 보류**: quickstart.md는 `"shadcn-ui": "latest"`를 패키지로 명시했지만, shadcn/ui는 npm 의존성이 아니라 CLI로 컴포넌트를 복사해오는 도구라 지금 단계에서 설치하지 않았습니다(T022에서 `npx shadcn init` 방식으로 처리 예정). 마찬가지로 ESLint는 devDependency로만 추가했고, 실제 `.eslintrc`/`eslint.config.js` 작성은 T006 범위라 보류했습니다.

## 비고
- `npm audit`에서 9건(critical 1, high 1 등)의 취약점 경고가 나왔습니다. 모두 quickstart.md에 고정된 비교적 오래된 버전(vite 5.0, vitest 1.0 등)에서 비롯된 간접 의존성 문제로 보이며, 지금 당장 애플리케이션 동작에 영향을 주지는 않습니다. 추후 Polish 단계(T195 이후, 성능/보안 관련 Task)에서 버전 업그레이드 검토가 필요합니다.
- `npx vitest run`을 실행해 테스트 러너 자체가 정상 동작하는지 확인했습니다(아직 테스트 파일이 없어 "No test files found"로 종료되는 것은 정상입니다).
- `frontend/node_modules/`는 추후 git 저장소 초기화 시(.gitignore 작업, T007) 반드시 제외 패턴에 포함되어야 합니다.
- 별개로, 이전 Task 002 작업 중 사용자 요청으로 `backend/.venv`가 추가 생성되어 `backend/venv`와 `backend/.venv`가 함께 존재하는 상태입니다. 어느 쪽을 표준으로 쓸지는 아직 결정되지 않았습니다.
