# ShopMate

WhatsApp + Telegram AI assistant for Ghanaian SMEs. FAQ, photo quotes, leads, and owner alerts from YAML business config.

## Run locally

```powershell
copy .env.example .env   # add OPENAI_API_KEY + TELEGRAM_BOT_TOKEN
.\create_all.ps1
.\start.ps1
```

## Deploy

- [RAILWAY.md](RAILWAY.md) — recommended
- [RENDER.md](RENDER.md)

## Config

- Secrets: `.env` (see `.env.example`)
- Shop data: `businesses/{id}/config.yaml` + `knowledge.yaml`
- Demo: `businesses/techlink_mobile/`

## License

MIT
