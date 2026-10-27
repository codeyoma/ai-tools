import json, re, sys
path, *notes = sys.argv[1:]
d = json.load(open(path))
corpus = "".join(open(n).read() for n in notes)
KEYS = ["id","name","vendor","domain","category","tagline","description","connect","worksWith","aiCost","price","free","official","status","stars","updated","homepage","repo","install","caveats","korea","starter","sources"]
CATS = {"호스트·에이전트","탐색·레지스트리","공통 MCP·스킬","검색·실행 환경","보안"}
CONN = {"remote-mcp","local-mcp","plugin","skills","cli","signin","byok","ide","library","app","connector"}
WW = {"claude","chatgpt","gemini","copilot","cursor","local"}
AIC = {"plan","credits","apikey","none"}
OFF = {"official","community","third-party"}
ST = {"active","beta","preview","experimental","deprecated","archived","shutdown","stale"}
probs = []
ids = [x["id"] for x in d]
assert len(ids) == len(set(ids))
for x in d:
    i = x["id"]
    if list(x.keys()) != KEYS: probs.append((i, "keys", set(KEYS) ^ set(x.keys())))
    if not i.startswith("gen-") or not re.fullmatch(r"[a-z0-9-]+", i): probs.append((i,"id"))
    if x["domain"] != "general": probs.append((i,"domain"))
    if x["category"] not in CATS: probs.append((i,"cat"))
    if len(x["tagline"]) > 40: probs.append((i,"tagline len", len(x["tagline"])))
    n = len(re.findall(r"(?:다|요)\.(?:\s|$)", x["description"]))
    if not 2 <= n <= 4: probs.append((i,"sentences", n))
    if not set(x["connect"]) <= CONN: probs.append((i,"connect"))
    if not set(x["worksWith"]) <= WW: probs.append((i,"ww"))
    if x["aiCost"] not in AIC: probs.append((i,"aic"))
    if x["official"] not in OFF: probs.append((i,"off"))
    if x["status"] not in ST: probs.append((i,"status"))
    if not isinstance(x["free"], bool) or not isinstance(x["starter"], bool): probs.append((i,"bool"))
    if x["stars"] is not None and not isinstance(x["stars"], int): probs.append((i,"stars"))
    if x["updated"] is not None and not re.fullmatch(r"\d{4}-\d{2}", x["updated"]): probs.append((i,"updated"))
    if x["homepage"] is not None and not x["homepage"].startswith("https://"): probs.append((i,"hp"))
    if x["repo"] is not None and not re.fullmatch(r"[\w.-]+/[\w.-]+", x["repo"]): probs.append((i,"repo"))
    if len(x["caveats"]) > 3: probs.append((i,"caveats"))
    if not 1 <= len(x["sources"]) <= 3: probs.append((i,"sources"))
    urls = [s["url"] for s in x["sources"]] + ([x["homepage"]] if x["homepage"] else [])
    for u in urls:
        if u not in corpus and u.rstrip("/") not in corpus: probs.append((i,"url-not-in-notes", u))
    if x["repo"] and ("github.com/"+x["repo"]) not in corpus: probs.append((i,"repo-not-in-notes", x["repo"]))
    if x["install"] and x["install"] not in corpus: probs.append((i,"install-not-in-notes", x["install"]))
    for s in x["sources"]:
        if set(s.keys()) != {"label","url"}: probs.append((i,"srckeys"))
from collections import Counter
print(len(d), Counter(x["category"] for x in d))
print("starter:", [x["id"] for x in d if x["starter"]])
for p in probs: print(p)
