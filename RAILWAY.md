# Deploy ShopMate on Railway

Repo: [github.com/happuchriley/ShopMate](https://github.com/happuchriley/ShopMate)

Railway is the **recommended** host for ShopMate — usage-based pricing (~$5/mo Hobby) and always-on for Telegram polling.

## Cost (approximate, Ghana)

| Item | USD/mo | GHS/mo (₵12.20/$) |
|------|--------|-------------------|
| Hobby plan | $5 | ₵61 |
| Web + Postgres (light) | $8–12 | ₵98–146 |
| OpenAI API (small shop) | $1–5 | ₵12–61 |
| **Total** | | **₵110–210** |

---

## 1. Create project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Select **happuchriley/ShopMate**
4. Railway reads `railway.toml` + `nixpacks.toml` automatically

## 2. Add PostgreSQL

SQLite does **not** persist on Railway (data lost on redeploy).

1. In your project → **+ New** → **Database** → **PostgreSQL**
2. Open the **web service** → **Variables** → **Add Reference**
3. Select Postgres → `DATABASE_URL`

ShopMate auto-creates tables on startup and normalizes `postgres://` URLs.

## 3. Set secrets (Variables)

| Variable | Required | Notes |
|----------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Yes | From [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | Yes | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `DATABASE_URL` | Yes | Reference from Postgres plugin |
| `WHATSAPP_VERIFY_TOKEN` | If WhatsApp | Random 32+ char string |
| `WHATSAPP_ACCESS_TOKEN` | If WhatsApp | Meta Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | If WhatsApp | Meta dashboard |
| `WHATSAPP_APP_SECRET` | If WhatsApp | For webhook signatures |

Telegram-only? Skip all `WHATSAPP_*` vars.

## 4. Networking

1. Web service → **Settings** → **Networking** → **Generate Domain**
2. Your URL: `https://shopmate-production-xxxx.up.railway.app`
3. Test: `curl https://YOUR-DOMAIN/health` → `{"status":"ok"}`

## 5. Resource settings

| Setting | Value | Why |
|---------|--------|-----|
| **Replicas** | **1** | Telegram polling breaks with 2+ instances |
| **RAM** | 512 MB | Enough for FastAPI + aiogram |
| **Region** | Europe (Amsterdam) | Lower latency to Ghana |

**Do not scale horizontally** — duplicate bots cause Telegram `Conflict` errors.

## 6. WhatsApp webhook (optional)

1. Meta Developer → WhatsApp → Configuration
2. Callback: `https://YOUR-DOMAIN.up.railway.app/webhook`
3. Verify token = `WHATSAPP_VERIFY_TOKEN`
4. Subscribe to **messages**

## 7. Owner alerts & digest

1. Message your bot → `/start`
2. Run locally: `python scripts/get_owner_chat_id.py`
3. Add chat ID to `businesses/techlink_mobile/config.yaml` → `owner_telegram_chat_id`
4. Commit and redeploy (or edit in GitHub — Railway auto-deploys)

---

## How it works on Railway

- **Build:** Nixpacks + Python 3.12 (`nixpacks.toml`)
- **Start:** `uvicorn … --workers 1` (single worker = single Telegram poller)
- **Health:** `/health` every deploy
- **Digest:** APScheduler at 08:00 `Africa/Accra`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails | Check logs; confirm `NIXPACKS_PYTHON_VERSION=3.12` |
| Bot silent | Verify `TELEGRAM_BOT_TOKEN`; check only **1 replica** running |
| `Conflict` errors | Stop duplicate deploys / local `start.ps1` while Railway runs |
| DB errors | Ensure `DATABASE_URL` references Postgres, not SQLite |
| AI errors | Set real `OPENAI_API_KEY` |
| WhatsApp 403 | Set `WHATSAPP_APP_SECRET` + matching verify token |

## Logs

Railway dashboard → your service → **Deployments** → **View Logs**

Look for: `ShopMate v1.3.0 started` and `Starting Telegram polling…`
