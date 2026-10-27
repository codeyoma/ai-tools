# AI 구독 툴 스토어 (정적 사이트)

배포 주소: https://ai-tools.yoma.kr (Vercel 프로젝트 `ai-tools`, 팀 `codeyomas-projects`)

## 구성

- `index.html`: 페이지 전체(HTML·CSS·JS 한 파일)
- `data/catalog.json`: 도구 1,067개 데이터
- `img/`: 도구별 미리보기 이미지, `icons/`: 도구별 아이콘
- `og.png`, `favicon.svg`, `vercel.json`(캐시 헤더)
- `_source/`: 원본 데이터(`data-src/*.json`)와 빌드 도구. 배포에서 제외됩니다(`.vercelignore`).

## 다시 만들기

Claude 아티팩트 빌드 폴더(`store/`)에서 정적 사이트를 다시 만들 때:

```bash
python3 -I _source/tools/make_static.py <artifact store 폴더> .
python3 -I _source/tools/make_index.py _source/artifact-index.html index.html "1,067"
```

## 배포

```bash
vercel deploy --prod
```
