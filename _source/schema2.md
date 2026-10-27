# Catalog entry schema (Korean "AI 구독 툴 스토어" site)

Today is 2026-10-25. The reader is a Korean developer/creator on macOS (Apple Silicon) who pays for Claude Pro/Max (uses Claude Code desktop) and ChatGPT Plus/Pro (uses Codex). They want tools they can drive from AI subscriptions they already pay for, so always state how a tool connects: MCP server (remote or local), Claude connector, ChatGPT app/plugin, Claude Code/Codex plugin or Agent Skills, CLI the agent can run, sign-in with a Claude/ChatGPT/Google/Copilot subscription, or BYOK API key (separate pay-per-token billing). Include tools with no AI hook only when they are major in their field, and say so.

Write a JSON array. Each entry is an object with exactly these keys:
- "id": unique kebab-case string with your section's prefix
- "name": product name as the vendor writes it (Korean services keep their Korean name, e.g. "브루(Vrew)")
- "vendor": company or maintainer
- "domain": your section's domain code
- "category": exactly one of your section's category list
- "tagline": Korean, one line, at most 40 characters, what it does
- "description": Korean, 2–4 plain sentences: what it does, how it connects to the user's AI subscription, what it is good for
- "connect": array of codes from ["remote-mcp","local-mcp","plugin","skills","cli","signin","byok","ide","library","app","connector"] (signin = log in with a Claude/ChatGPT/Google/Copilot subscription; byok = your own API key; app = vendor's own app on its own credits; connector = Claude connector directory or ChatGPT app/plugin; library = the agent writes code or scripts against it)
- "worksWith": array from ["claude","chatgpt","gemini","copilot","cursor","local"] — subscriptions/clients that can drive it with no extra AI billing
- "aiCost": "plan" (runs on the user's AI subscription), "credits" (vendor's own AI credits/plan), "apikey" (pay-per-token API key), or "none" (no AI inside; the agent only drives it)
- "price": Korean short string for the tool's own price/free tier (e.g. "무료", "Pro $20/월", "확인 필요")
- "free": true if usable at no cost on the tool side, else false
- "official": "official", "community", or "third-party"
- "status": one of "active","beta","preview","experimental","deprecated","archived","shutdown","stale"
- "stars": GitHub star count integer if known, else null
- "updated": latest release/push month "YYYY-MM" if known, else null
- "homepage": official product or docs URL (https), or null
- "repo": GitHub "owner/name" if there is a public repo, else null
- "install": one exact copy-paste install/config command or MCP endpoint URL if documented, else null
- "caveats": array of 0–3 short Korean strings (licensing/commercial-use limits, privacy, deprecations, plan gating)
- "korea": Korean note for Korea-specific facts (Korean-language support, KRW pricing, availability in Korea, Korean alternatives), else null
- "starter": true for at most 8 entries in your section that you would recommend first to this user
- "sources": array of 1–3 {"label": short text, "url": source URL you actually read}

Rules:
- Every fact must come from a source you read during this task; never invent prices, stars, endpoints or URLs. Use null or "확인 필요" when unknown.
- Korean text should read naturally; keep product names, commands, model IDs and code in English.
- Skip tools already in the catalog (list: /private/tmp/claude-501/-Users-yoma-Projects-test/c6f5680e-a1d4-4a97-8eb5-70fd904f2382/scratchpad/existing_names.txt) unless your entry is clearly a different product.
- Validate before finishing: python3 -I -c "import json,sys; d=json.load(open(sys.argv[1])); ids=[x['id'] for x in d]; assert len(ids)==len(set(ids)); print(len(d))" <path>
