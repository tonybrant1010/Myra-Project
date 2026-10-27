# Myra Project

https://myra-project.hu

Önismereti platform: ESV-modell alapú állapotfelmérés, méréshez kötött chat, naplózott
krízisjelzés.

![Myra Project](assets/readme/login.png)

## Architektúra

```
böngésző → Caddy (TLS, WAF) → FastAPI backend → PostgreSQL + pgvector
                                            → LLM (Gemini API vagy helyi llama-server)
```

- **Backend:** FastAPI, SQLAlchemy async, asyncpg
- **Adatbázis:** PostgreSQL 17 + pgvector (1024 dimenziós embedding)
- **Frontend:** Expo / React Native Web, statikus export
- **Fordított proxy:** Caddy, Coraza WAF-fal (OWASP CRS)
- **Konténerek:** Docker Compose

## Indítás

```bash
cp .env.example .env
# Állítsd be a .env-ben a JWT_SECRET, DATABASE_URL, DB_PASSWORD és MYRA_PROXY_SECRET értékét.
sudo mkdir -p backend/data control backups /var/lib/postgresql/data
sudo chown -R 1000:1000 backend/data control
sudo chown -R 999:999 /var/lib/postgresql/data
docker compose up -d --build
```

A PostgreSQL-konténer helyi adatkönyvtára a `/var/lib/postgresql/data`; ezt a backend nem teszi ki a hálózatra.
A backend a loopbacken figyel, ezért nyilvános telepítésnél helyi fordított proxy szükséges.
Proxy nélküli helyi futtatásnál a `TRUST_PROXY` maradjon `false`. A GDPR tájékoztatóban
(`frontend/src/constants/docs/gdpr.ts`) a telepítés előtt töltsd ki az adatkezelő adatait.

## Konfiguráció

Minden beállítás a `.env`-ben van; a `.env.example` a sablon. Titkot (kulcs, jelszó,
token) **soha** ne commitolj — a `.gitignore` és a `.env.example` ezt hivatott védeni.

## Biztonság

- jelszavas belépés + e-mailes MFA, adminnál kötelező
- rate limit, brute-force védelem, audit napló
- krízisjelzés három rétegben (előszűrő → modell → determinisztikus padló)
- a helyi LLM csak külön engedélyezés és helyi vagy megbízható hálózati végpont megadásával indul

## Licenc

PolyForm Noncommercial 1.0.0 — nem kereskedelmi használat a licenc és a
szerzői megjelölés megtartásával. Kereskedelmi használat kizárólag
írásos engedéllyel: info@myra-project.hu

A teljes licencszöveg: [LICENSE](LICENSE).

## Kapcsolat

info@myra-project.hu
