# Deploy ShopMate on Render

Repo: [github.com/happuchriley/ShopMate](https://github.com/happuchriley/ShopMate)

## Important: plan choice

ShopMate uses **Telegram polling** and a **morning digest scheduler** — it must stay running 24/7.

| Plan | Works for ShopMate? |
|------|---------------------|
| **Free** web | No — service sleeps after ~15 min idle; bot stops responding |
| **Starter** ($7/mo) | Yes — always on |

`render.yaml` uses **Starter** for the web service. You can switch to Free in the dashboard only for testing (expect downtime).

---

## Option A — Blueprint (recommended)

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Blueprint**
3. Connect GitHub → select **happuchriley/ShopMate**
4. Render reads `render.yaml` and creates:
   - Web service `shopmate`
   - Postgres database `shopmate-db`
5. When prompted, set these **secret** env vars:

| Variable | Where to get it |
|----------|-----------------|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `WHATSAPP_VERIFY_TOKEN` | Any long random string (32+ chars) |
| `WHATSAPP_ACCESS_TOKEN` | Meta WhatsApp Cloud API (optional if Telegram-only) |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta developer dashboard (optional) |
| `WHATSAPP_APP_SECRET` | Meta app settings → Basic (required for WhatsApp in prod) |

6. Click **Apply** and wait for the first deploy (~3–5 min).
7. Your URL will be like: `https://shopmate-xxxx.onrender.com`

---

## Option B — Manual web service

1. **New** → **Web Service** → connect the GitHub repo
2. Settings:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health check path:** `/health`
   - **Plan:** Starter
3. Add env vars from `.env.example` (same table above).
4. Optional: create a **PostgreSQL** database and set `DATABASE_URL` to its **Internal** connection string.

---

## After deploy

### 1. Verify health

```bash
curl https://YOUR-SERVICE.onrender.com/health
```

Expected: `{"status":"ok"}`

### 2. Telegram

No extra setup — polling starts automatically. Message your bot with `/start`.

### 3. WhatsApp (when ready)

1. Meta Developer → WhatsApp → Configuration
2. **Callback URL:** `https://YOUR-SERVICE.onrender.com/webhook`
3. **Verify token:** same as `WHATSAPP_VERIFY_TOKEN` in Render env
4. Subscribe to **messages**

### 4. Owner alerts & digest

1. Message your bot on Telegram with `/start`
2. Run locally: `python scripts/get_owner_chat_id.py`
3. Add the chat ID to `businesses/techlink_mobile/config.yaml` → `owner_telegram_chat_id`
4. Commit and push (or edit via Render shell — YAML is in the image)

---

## Database

The blueprint attaches **Render Postgres** (free tier). ShopMate auto-creates tables on startup.

SQLite is not used on Render — data persists in Postgres across deploys.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Deploy fails on `pip install` | Check build logs; ensure `PYTHON_VERSION=3.12.0` |
| Bot silent on Telegram | Confirm Starter plan; check logs for `TELEGRAM_BOT_TOKEN` errors |
| Only one instance | Do not scale to multiple instances (Telegram polling conflict) |
| WhatsApp 403 on webhook | Set `WHATSAPP_APP_SECRET` and correct verify token |
| AI errors | Set a real `OPENAI_API_KEY` (not placeholder) |

---

## Logs

Render dashboard → **shopmate** → **Logs**

Look for: `ShopMate v1.3.0 started`
