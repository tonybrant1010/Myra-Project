# Biztonsági riasztások felülvizsgálata

Felülvizsgálat: 2026-11-02. A megállapítások az alább megnevezett riasztásokra
és csomagverziókra vonatkoznak. Függőség- vagy advisory-változáskor újraértékelendők.

## minimatch — GHSA-g3hv-75wg-m249 / CVE-2026-118764

A Dependabot #55 a `frontend/package-lock.json` örökölt `minimatch@3.1.5`
példányát jelzi a GitHub-adatbázis `<11.0.1` verziótartománya alapján.

A [karbantartó saját advisoryja](https://github.com/isaacs/minimatch/security/advisories/GHSA-g3hv-75wg-m249)
a 10.2.6-os verzió `optimizationLevel >= 2` optimalizálási ágát azonosítja.
A [3.1.5-ös kiadás forrásában](https://github.com/isaacs/minimatch/blob/v3.1.5/minimatch.js)
nincs `optimizationLevel`, `firstPhasePreProcess` vagy `secondPhasePreProcess`;
az ismertetett kódút ebben a kiadásban nem létezik. A lockfájl modern
minimatch-példányai 11.0.4-esek, a javított 11.0.1 fölött.

Elbírálás: téves pozitív jelzés a 3.1.5-ös ágra. Az örökölt, függvényként hívható
API-t igénylő függőségek megmaradnak; az új API-ra történő általános felülírás
kompatibilitási hibát okozna. Más minimatch-advisorykra ez az elbírálás nem vonatkozik.

## deepmerge — GHSA-gcqx-w48m-w2h4 / CVE-2026-93753

A Dependabot #54 a `deepmerge@4.3.1` verziót jelzi. A CVE-t a kibocsátó CNA
2026-11-02 16:33:19 UTC-kor **REJECTED** állapotba helyezte, mert a bejelentés
nem ír le biztonsági sérülékenységet.

Elsődleges bizonyíték: [hivatalos CVE-rekord](https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/2026/93xxx/CVE-2026-93753.json),
[CVE API](https://cveawg.mitre.org/api/cve/CVE-2026-93753).
Az npm legújabb kiadása az ellenőrzéskor 4.3.1, külön javított kiadás nincs.

Elbírálás: visszavont CVE-hez tartozó, elavult riasztás. A függőség a jelenlegi
projektben az Expo konfigurációkezelésében használatos. Csomag-visszaminősítés
vagy egyedi fork bevezetése nem indokolt e visszavont CVE miatt.

## CodeQL — py/path-injection

Az admin PDF-kezelés közös fájlnév-ellenőrzést, feloldott útvonalon végzett
könyvtárhatár-ellenőrzést és symlink-elutasítást kapott. A feltöltés új ideiglenes
fájlt publikál atomi cserével. Törléskor a kérés neve csak a megbízható könyvtárban
létező bejegyzés kiválasztására szolgál; az útvonal ebből a bejegyzésből készül.
A normalizált, könyvtárelválasztóval lezárt prefix ellenőrzése minden,
fájlnévből képzett útvonalon végzett metaadat-lekérdezést megelőz.
A regressziós tesztek a könyvtárból kilépő neveket,
symlinkeket, hibás publikálást és a támogatott Unicode fájlneveket is ellenőrzik.
Ehhez a találathoz nincs scannerelnyomás; az új elemzésnek a javítást kell igazolnia.
