# Összehasonlító tábla — nyilvános információk alapján

**Fontos:** ez **nem validált benchmark**, hanem egy átlátható összevetés. A Myra pontjai a
repó és a működés alapján készült **önértékelés**; a versenytársak pontjai a **nyilvános**
termékoldalakból, sajtóanyagokból és publikációkból becsültek, ezért **ellenőrizendők**.
Ahol nincs nyilvános adat, ott `?` szerepel.

Skála: 1 = hiányzik, 3 = részben, 5 = kiemelkedő.

| Szempont | Myra | Wysa | Kintsugi | Thymia | Dr. Riya |
|---|---|---|---|---|---|
| Krízis- és biztonságkezelés | **5** | 4 | 3 | 3 | 2 |
| Adatvédelem | **4** | 4 | 3 | 3 | ? |
| Klinikai megalapozottság | **3** | 4 | 4 | 4 | 2 |
| Klinikai bizonyíték | **2** | 4 | 3 | 4 | 1 |
| Funkciók szélessége | **5** | 4 | 3 | 3 | 2 |
| UX / akadálymentesség | **4** | 4 | 3 | 3 | 3 |
| Infrastruktúra-biztonság | **5** | ? | ? | ? | ? |
| Átláthatóság | **4** | 4 | 3 | 4 | 2 |

## Jegyzetek

**Myra** — a pontok a repó alapján: háromrétegű krízis-pipeline (`backend/crisis.py`),
GDPR-szöveg a külső LLM-szolgáltatók kimondásával, 69 PDF-es tudásbázis + RAG,
előregisztrált 30 napos pilot (Zenodo, DOI: 10.5281/zenodo.23099560, N=2 pre-post,
27 kitöltés, α = 0,90–0,96), WAF + CrowdSec + UFW + hardening, MFA, audit.

**Wysa** — strukturált CBT/DBT, klinikai publikációk (pl. stressz/szorongás-csökkenés
nemzetközi hallgatóknál, 2026). Forrás: a Wysa termékoldala és a vonatkozó szakirodalom.

**Kintsugi** — hangalapú biomarkerek, nyilvánosan elérhetővé tett voice-biomarker AI;
a klinikai bizonyíték a hangdiagnosztikára vonatkozik, nem kríziskezelésre.

**Thymia** — regisztrált orvostechnikai eszköz (Class 1), multimodális mérés; erős
szabályozási alap, de nem beszélgetős társ.

**Dr. Riya (Mindtalk)** — generatív tanácsadó; nyilvános klinikai validáció nem ismert.

## Hogyan lesz ebből hivatalos állítás

1. Rögzíteni kell a kritériumokat és a pontozási szinteket (ez a tábla).
2. A versenytársak pontjait **forrással** kell alátámasztani (termékoldal, publikáció, audit).
3. A Myra pontjait ugyanígy, bizonyítékkal (repó, teszt, publikáció).
4. A végleges, publikálható verzióhoz független értékelő vagy a szempontrendszert
   elfogadó szakmai fórum kell — a saját tábla önmagában nem ranglista-helyezés.
