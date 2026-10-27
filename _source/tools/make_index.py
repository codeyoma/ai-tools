"""Wrap the artifact page (no <html>/<head>/<body>) into a standalone static index.html.

Usage: python3 -I make_index.py <artifact index.html> <site index.html> <tool count>
"""
import re
import sys

src, dst, count = sys.argv[1], sys.argv[2], sys.argv[3]
SITE = "https://ai-tools.yoma.kr"
DESC = (f"Claude·ChatGPT·Gemini 등 내가 구독하는 AI에 MCP·플러그인·로그인으로 연결해 쓰는 "
        f"개발·디자인·음악·영상·기획·창업 도구 {count}개를 앱스토어처럼 둘러보는 한국어 카탈로그.")

with open(src) as f:
    page = f.read()

# Drop the artifact-only lines that the publish skeleton used to provide or read.
page = re.sub(r'<meta charset="utf-8">\n', "", page, count=1)
page = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\n', "", page, count=1)
page = re.sub(r"<title>[^<]*</title>\n", "", page, count=1)

head = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI 구독 툴 스토어</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{SITE}/">
<meta property="og:type" content="website">
<meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="AI 구독 툴 스토어">
<meta property="og:title" content="AI 구독 툴 스토어">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{SITE}/">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#151b24" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
"""

# The artifact skeleton supplied this small reset; a standalone page needs it inline.
reset = """/* Standalone reset (the artifact viewer used to provide it) */
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
.site-foot { border-top: 1px solid var(--line); color: var(--muted); font-size: 12.5px; padding-block: 20px 32px; }
.site-foot p { margin: 0 0 6px; max-width: 90ch; }
"""
page = page.replace("<style>\n", "<style>\n" + reset, 1)
# A live site shows the visitor's date; deadlines then flip to "past" on their own.
page = page.replace("const TODAY = new Date('2026-10-25T12:00:00+09:00');", "const TODAY = new Date();", 1)
page = page.replace("조사 기준일 2026-10-24", "조사 기준일 2026-10-27", 1)
page = page.replace("</style>\n", "</style>\n</head>\n<body>\n", 1)

footer = """<footer class="wrap site-foot">
  <p>조사 기준일 2026-10-27. 각 도구의 정보는 카드에 적힌 출처를 기준으로 정리했고, 가격·정책은 바뀔 수 있습니다.</p>
  <p>아이콘·미리보기 이미지·상표의 권리는 각 회사와 제작자에게 있습니다. 금융·법률·세무 관련 내용은 도구 정리이며 조언이 아닙니다.</p>
</footer>
"""
page = page.replace('<dialog class="sheet"', footer + '\n<dialog class="sheet"', 1)

with open(dst, "w") as f:
    f.write(head + page.rstrip() + "\n</body>\n</html>\n")
print("wrote", dst)
