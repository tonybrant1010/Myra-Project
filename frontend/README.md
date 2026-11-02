# Myra Frontend Client

Ez a Myra önismereti alkalmazás Expo / React Native frontendje. A webes exportot a saját szerveren Caddy szolgálja ki a `/srv/frontend/dist` könyvtárból.

## Fő Technológiai Stack

- **Expo (SDK 54)** és **React Native Web**: közös webes és mobil forráskód.
- **Expo Router**: Fájlrendszer-alapú navigáció és útvonalkezelés.
- **TypeScript**: Tiszta, típusbiztos kódbázis.
- **Metro / statikus export / Caddy**: a `/api` útvonalat a szerver Caddy-konfigurációja továbbítja a backendnek.

## Mappa Struktúra

- `/app`: A navigációs képernyők és útvonalak helye (pl. `chat.tsx`, `quiz.tsx`, `welcome.tsx`).
- `/src/components`: Közös UI komponensek (pl. `SideMenu.tsx`, `TopBar.tsx`, `PasswordInput.tsx`).
- `/src/auth`: Bejelentkezési folyamatok és munkamenet-érvényesség kezelése (`AuthContext.tsx`).
- `/assets`: Képek, betűtípusok és dizájn-assetek.
- `/scripts`: ellenőrzött release-build, statikus erőforrások és SSH-alapú telepítés.

## Fejlesztési Folyamat

### Lokális futtatás

1. Telepítsd a függőségeket:
   ```bash
   npm ci
   ```

2. Állítsd be a backend elérését környezeti változóban, majd indítsd el a dev szervert:
   ```bash
   set EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
   set EXPO_PUBLIC_CONTROLLER_NAME=Az adatkezelő neve
   npx expo start --web
   ```

   `EXPO_PUBLIC_CONTROLLER_NAME`: az adatkezelő neve, ami a GDPR-szövegben jelenik meg.
   A repóban szándékosan placeholder szerepel (személyes adat nem kerül a forrásba);
   **Release-buildnél kötelező kitölteni**: hiányzó vagy helykitöltő értékkel a build leáll.

## Release és telepítés

A helyi build a `frontend` könyvtárban készíthető el, éles szerverkapcsolat nélkül:
```bash
npm run release:web
```
Kötelező környezet: `EXPO_PUBLIC_CONTROLLER_NAME`; saját szerveren az
`EXPO_PUBLIC_BACKEND_URL` üres (azonos eredetű `/api`). Külső backendcímet a
release csak HTTPS-sel fogad el. A build `dist/build-info.json` fájlt is készít.

Az `npm run deploy` már szerverre ír: ellenőrzött release-t épít, majd az
`MYRA_DEPLOY_HOST` SSH-célra publikál. A cél alapértelmezése `/srv/frontend/dist`,
felülírása `MYRA_DEPLOY_DIR`. A telepítő csak érvényes build-információval indul,
és az `ops/publish_frontend.py` segítségével cseréli a frontend könyvtárát.
Az API-továbbítást a szerver Caddyfile-ja kezeli; Vercel-konfiguráció nem része a telepítésnek.
