const CONTROLLER_NAME =
  (process.env.EXPO_PUBLIC_CONTROLLER_NAME || "").trim() ||
  "[Az adatkezelő neve a telepítés előtt kitöltendő]";

export const gdprText = `ADATKEZELÉSI TÁJÉKOZTATÓ

Hatályos: 2026. november 2.

1. Az adatkezelő
Név: ${CONTROLLER_NAME}
Email: info@myra-project.hu
Tevékenység jellege: magánszemélyként végzett, nem kereskedelmi célú kutatási és fejlesztési projekt

2. A szolgáltatás és az adatkezelés célja
A Myra egy mérésvezérelt, reflektív mentálhigiénés önismereti alkalmazás. Az adatkezelés célja:
- felhasználói fiók létrehozása és azonosítása,
- az alkalmazás biztonságos működtetése,
- kérdőíves állapotfelmérés rögzítése,
- belső állapotkód képzése és megjelenítése,
- személyre szabott chatbot-beszélgetés biztosítása,
- korábbi mérési és beszélgetési adatok visszanézhetősége,
- a felhasználó által önkéntesen vállalt apró önismereti célok (mikro-célok) rögzítése és követése,
- néhány nap kihagyás után a beszélgetés Myra általi, támogató visszakérdezéssel történő újranyitása,
- a felhasználó kérésére szakembernek szánt, letölthető mérési összefoglaló (PDF) előállítása,
- visszaélések, túlterhelés és jogosulatlan hozzáférés megelőzése,
- hibakeresés, biztonsági ellenőrzés és működésfenntartás,
- adatvesztés elleni biztonsági mentések készítése.

3. Kezelt adatok köre
Az alkalmazás az alábbi adatokat kezelheti:
- név,
- email cím,
- jelszó titkosított, visszafejthetetlen formában,
- regisztráció és bejelentkezés időpontja,
- kérdőívre adott válaszok,
- belső állapotkód és mérési eredmények,
- a felhasználó által vállalt mikro-célok szövege és állapota (aktív/teljesített),
- chat üzenetek tartalma,
- a mikrofonnal diktált üzenet hangfelvétele, kizárólag a szöveggé alakítás idejére (lásd 7. pont),
- a felhasználó külön, önkéntes hozzájárulása esetén a korábbi méréseiből és beszélgetéseiből képzett összefoglaló ("Myra memóriája"),
- chatbot-válaszok,
- a fórumban és a ranglistán használt becenév és avatar, a fórumba írt hozzászólások,
- a játékok eredményei és a ranglistához szükséges ellenőrző játékadatok,
- a kétlépcsős azonosítás beállításai (hitelesítőalkalmazás titkos kulcsa titkosítva, megbízható eszközök),
- a felhasználó által az alkalmazásból küldött visszajelzés szövege és a válaszadáshoz szükséges e-mail cím,
- a beszélgetéshez kapcsolódó, az alkalmazás által visszakeresett tudásanyag-részletek technikai felhasználása,
- felhasználói aktivitási adatok az alkalmazás működtetéséhez szükséges mértékben,
- technikai naplóadatok, például hibák, hozzáférési próbálkozások, IP-cím vagy eszköz-/böngészőinformáció, ha ez biztonsági vagy működtetési okból szükséges.

Más felhasználók által látható adatok. A fórumba írt hozzászólások a becenévvel és az avatarral együtt a többi bejelentkezett felhasználó számára láthatók. A játékok ranglistáján a legjobb eredmények a becenévvel jelennek meg; becenév nélkül "Névtelen játékos" felirattal. A felhasználó nevét és e-mail címét más felhasználó nem látja. A fórumban ezért ne ossz meg olyan adatot, amelyből azonosítható vagy amelyet nem szeretnél mások elé tárni.

4. Különleges adatok és kifejezett hozzájárulás
A Myra használata során a felhasználó mentális állapotára, érzelmi terhelésére, stressz-szintjére vagy egészségi állapotára utaló információk is megjelenhetnek. Ezek az adatok a GDPR 9. cikke alapján különleges kategóriájú személyes adatnak minősülhetnek.

Az ilyen adatok kezelése a felhasználó kifejezett, önkéntes hozzájárulásán alapul a GDPR 9. cikk (2) bekezdés a) pontja szerint. A regisztrációval és a tájékoztató elfogadásával a felhasználó kifejezetten hozzájárul ahhoz, hogy a Myra az alkalmazás működéséhez szükséges mértékben ilyen adatokat kezeljen.

A "Myra memóriája" funkció külön, önálló hozzájáruláson alapul. Alapértelmezés szerint ki van kapcsolva; a felhasználó a Beállítások menüben maga kapcsolja be, és ugyanott bármikor kikapcsolja. A kivonat a felhasználó saját méréseiből és beszélgetéseiből készül, és ugyanolyan különleges kategóriájú adatot tartalmazhat, mint a forrás, amelyből származik. A kivonat a bekapcsoláskor a felhasználó addigi méréseiből és beszélgetéseiből azonnal elkészül, majd új mérés vagy újabb beszélgetések után automatikusan frissül. Az összefoglalót ugyanaz a nyelvi modell készíti, amely a chatbot válaszait is adja (lásd 7. pont): bekapcsolt helyi mód esetén az adatkezelő saját szerverén, egyébként a beállított AI-szolgáltatónál. Ehhez a forrásadatok a modellnek átadásra kerülnek. Ha a felhasználó egy beszélgetést töröl, a kivonat érvénytelenné válik, és a megmaradt adatokból képződik újra. Bekapcsolt memória mellett Myra a korábbi beszélgetésekből is visszakereshet néhány, a mostanihoz hasonló rövid részletet – akkor is, ha a felhasználó más szavakkal írt róla –, és ha illik a beszélgetésbe, maga is visszautalhat rájuk. Ehhez az adatkezelő saját szerverén futó nyelvi modell a felhasználó üzeneteiből technikai keresővektort képez, amelyet az adatbázis tárol; ebből az üzenet szövege nem állítható vissza, és harmadik félhez nem kerül. Az adatkezelő a kivonatot az üzemeltetés és a minőségbiztosítás körében megtekintheti, újraképezheti vagy törölheti. A hozzájárulás visszavonása (kikapcsolás) esetén a már elkészült kivonat azonnal törlődik, a korábbi beszélgetésekből történő visszakeresés megszűnik, és a keresővektorok is törlődnek.

Krízisjelzés. A rendszer a beérkező üzeneteket automatikusan értékeli abból a szempontból, hogy súlyos krízisre utalnak-e. Az értékelést a chatbot által használt nyelvi modell végzi (bekapcsolt helyi mód esetén a saját szerveren, egyébként a beállított AI-szolgáltatónál). Ha a felhasználó üzenete súlyos krízisre – öngyilkossági vagy önsértési szándékra – utal, a rendszer az adatkezelőnek e-mail-értesítést küld, amely tartalmazza a felhasználó nevét, e-mail-címét, az időpontot és a jelzést kiváltó üzenet szövegét. Egy krízishelyzethez legfeljebb három értesítés tartozik: a kezdetéről, szükség esetén a súlyosbodásáról, valamint a lezárulásáról. Ha a levél átmeneti hiba miatt nem küldhető el, a rendszer titkosítva, a kézbesítésig tárolja, és automatikusan újrapróbálja; a fiók törlésekor a még el nem küldött értesítés is törlődik. Az értesítés célja, hogy az adatkezelő tudomást szerezzen a helyzetről, és szükség esetén – élet vagy testi épség közvetlen veszélye esetén – megtehesse a Felhasználási feltételekben leírt lépéseket. Ez nem folyamatos felügyelet és nem sürgősségi szolgáltatás: az értesítés nem garantál azonnali beavatkozást. Az értesítés az adatkezelő Proton Mail-postaládájába érkezik (Proton AG, Svájc), ahol a levelek titkosítva tárolódnak. Az értesítő e-maileket az adatkezelő az ügy lezárása után, legkésőbb 30 napon belül törli. Ennek jogalapja a kifejezett hozzájárulás mellett az érintett létfontosságú érdeke (GDPR 6. cikk (1) bekezdés d) pont, 9. cikk (2) bekezdés c) pont).

5. Az adatkezelés jogalapja
Az adatkezelés fő jogalapja a felhasználó önkéntes hozzájárulása:
- GDPR 6. cikk (1) bekezdés a) pont: hozzájárulás,
- GDPR 9. cikk (2) bekezdés a) pont: különleges adatok kezeléséhez adott kifejezett hozzájárulás.

Biztonsági, visszaélés-megelőzési és működésfenntartási célú technikai adatkezelés esetén az adatkezelő jogos érdeke is felmerülhet a GDPR 6. cikk (1) bekezdés f) pontja alapján. Ez nem terjed ki a szükséges mértéken túlmutató mentálhigiénés tartalomelemzésre.

6. Adattárolás helye és adatbiztonság
A felhasználói adatbázis az adatkezelő saját szerverén működik.

Az alkalmazás szerveroldali része (backend) az adatkezelő által üzemeltetett, Magyarországon elhelyezett szerveren fut. A szerver kívülről közvetlenül nem érhető el: a titkosított (HTTPS) forgalmat a szerveren futó saját fordított proxy fogadja, amely saját, automatikusan megújított tanúsítvánnyal dolgozik, és az alkalmazásszerver kizárólag ettől a proxytól fogad kéréseket. Az adatbázishoz kizárólag ez a szerver kapcsolódhat.

A webes felület ugyanerről a szerverről, ugyanazon a domainen érhető el (azonos eredet), így a felület és a kéréseket kiszolgáló réteg között nincs külső szolgáltató. A rendszer külső tartalomkiszolgálót (CDN-t), harmadik féltől származó szkriptet, valamint hirdetési vagy analitikai követőkódot nem használ.

Biztonsági mentések. Az adatkezelő a felhasználói adatbázisról óránként biztonsági mentést készít, amelyet saját, Magyarországon elhelyezett eszközein, korlátozott hozzáféréssel tárol; külső tárhelyszolgáltatót ehhez nem vesz igénybe. A megőrzött mentések száma korlátozott: óránkénti hat és napi hét példány marad meg, a régebbiek automatikusan törlődnek.

A rendszer kialakítása törekszik arra, hogy a backend és az adatbázis elkülönítetten működjön, és a kliensoldali felület ne tartalmazzon AI API-kulcsot vagy közvetlen adatbázis-hozzáférést. A jelszavak egyirányú hash formában kerülnek tárolásra. Az adatkezelő törekszik a hozzáférések korlátozására, az érzékeny adatok védelmére, a technikai naplók és admin funkciók ésszerű korlátozására, valamint arra, hogy az adatokhoz csak indokolt esetben legyen hozzáférés.

A PDF alapú tudásanyag indexelése technikai keresési célt szolgál. A rendszer a tudásanyagból vektoros kereséshez szükséges embeddingeket a saját szerveren futó adatbázisban tárolja. Ezek a felhasználói beszélgetésektől elkülönített technikai keresési adatok.

A beszélgetés TXT exportja a felhasználó kifejezett műveletére, a böngészőben készül el a már betöltött üzenetekből. Az alkalmazás külön szerveroldali exportfájlt nem hoz létre és nem tárol.

7. Külső szolgáltatók és adattovábbítás
Ha az adminisztrátor külső mesterséges intelligencia szolgáltatót választ, a felhasználó üzeneteinek válaszgeneráláshoz szükséges tartalma a beállított szolgáltatóhoz továbbítódik. Helyi modell választásakor a chatbot a saját szerveren dolgozza fel a tartalmat. Élő hangalapú asszisztens a szolgáltatásban nem működik, és hanganyag külső szolgáltatóhoz nem kerül. A felolvasás az adatkezelő saját szerverén, helyi beszédszintézissel történik. A mikrofonnal diktált üzenetet az adatkezelő saját szerverén futó beszédfelismerő alakítja szöveggé; a hangfelvétel csak a feldolgozás idejére, ideiglenesen létezik, utána azonnal törlődik.

A chatbot modelljét az adminisztrátor választja ki. Bekapcsolt helyi mód esetén a chatbot a saját szerveren futó modellt használja, hiba esetén sem vált automatikusan külső szolgáltatóra. Kikapcsolt helyi mód esetén a beállított AI-szolgáltató dolgozza fel a válaszhoz szükséges tartalmat. Ugyanez a modell végzi a krízisértékelést, a "Myra memóriája" összefoglaló elkészítését és a néhány nap kihagyás utáni visszakérdezést, így ezekhez is a fenti módon kerülnek adatok a helyi vagy a külső modellhez.

A chatbot-válasz generálásakor az aktuális üzenet mellett a beszélgetés korábbi, az alkalmazás működéséhez szükséges részletei, a felhasználó aktuális állapotkódjához kapcsolódó információk, valamint a PDF alapú tudásanyagból visszakeresett releváns részletek is bekerülhetnek a mesterséges intelligencia szolgáltatónak küldött kontextusba. Ez a beszélgetés folytonosságát és a válasz szakmai illeszkedését szolgálja.

Ez az adattovábbítás kizárólag a szolgáltatás működéséhez szükséges mértékben történik. A továbbítás az adott szolgáltatók hivatalos fejlesztői (API) felületein keresztül zajlik. Az adatkezelő olyan szolgáltatót és beállítást választ, amelynek szerződéses feltételei szerint a beküldött adatokat a szolgáltató nem használja fel saját modelljei tanítására; a feldolgozás részleteire az adott szolgáltató mindenkori API-feltételei irányadók.

A szolgáltatás működéséhez igénybe vett külső szolgáltatók lehetnek különösen:
- mesterséges intelligencia szolgáltatók – ha az adminisztrátor külső szolgáltatót választott, egyszerre mindig csak az egyik: Google (Gemini, alapbeállítás), OpenAI, Anthropic, Mistral AI, Groq, Cerebras, OpenRouter vagy Alibaba Cloud (DashScope),
- e-mail-szolgáltató (Proton AG, Svájc): a belépési kódok, a jelszó-visszaállítási kódok és a rendszerértesítések továbbítása és fogadása,
- domain- és névszerver-szolgáltató (magyar szolgáltató; a névfeloldás technikai adatai),
- biztonsági, naplózási vagy üzemeltetési szolgáltatások.
A tárhelyet és a webes felületet nem külső szolgáltató, hanem az adatkezelő saját, Magyarországon elhelyezett szervere biztosítja.

Rendszerüzenetek. Az alkalmazás a felhasználónak kizárólag a működéshez szükséges tranzakciós levelet küld: a regisztrációhoz és a bejelentkezéshez szükséges biztonsági kódot, valamint a jelszó-visszaállítási kódot. Ezek a levelek a saját domainről (info@myra-project.hu) mennek ki, a Proton Mail szolgáltatásán keresztül. Az alkalmazásból küldött visszajelzés e-mailben, ugyanezen a szolgáltatón keresztül érkezik az adatkezelőhöz. Az alkalmazás hírlevelet, marketing- vagy reklámcélú e-mailt nem küld.

Harmadik országba történő adattovábbítás. A tárhely és a felhasználói adatbázis az Európai Unión belül, illetve az adatkezelő magyarországi szerverén marad. Az e-mail-forgalmat a Proton AG svájci szolgáltató kezeli; Svájc az Európai Bizottság megfelelőségi határozata alapján megfelelő szintű adatvédelmet biztosít, ezért ez nem minősül olyan harmadik országba történő továbbításnak, amely kiegészítő garanciát igényelne. A felsorolt szolgáltatók egy része (különösen a mesterséges intelligencia szolgáltatók) az Európai Gazdasági Térségen kívül, elsősorban az Amerikai Egyesült Államokban, az Alibaba Cloud esetében Szingapúrban is végezhet adatfeldolgozást. Az ilyen továbbítás jogalapja az Európai Bizottság 2023. július 10-i, az EU–USA adatvédelmi keretre (Data Privacy Framework) vonatkozó megfelelőségi határozata azon szolgáltatók esetében, amelyek a keret tanúsított résztvevői, egyéb esetben az Európai Bizottság által elfogadott általános szerződési feltételek (GDPR 46. cikk (2) bekezdés c) pont). Az adatkezelő a szolgáltatóválasztásnál törekszik arra, hogy a tartós adattárolás (felhasználói adatbázis) az Európai Unión belül maradjon; a harmadik országba irányuló továbbítás a válaszgeneráláshoz szükséges átmeneti feldolgozásra korlátozódik.

8. Adatmegőrzési idő
Az adatok a felhasználói fiók aktív fennállásáig kerülnek megőrzésre. Mivel a Myra egy nonprofit kutatási és önismereti projekt, jogszabály nem írja elő az adatok kötelező megőrzési idejét.

A "Myra memóriája" kivonat a funkció kikapcsolásakor azonnal és véglegesen törlődik, a fiók megszüntetése nélkül is. A kivonat mindig teljes egészében újraképződik a forrásadatokból, nem őrzi meg a korábbi változatait.

A felhasználó bármikor kezdeményezheti fiókja és kapcsolódó adatainak azonnali és végleges törlését a Beállítások menüben a "Fiók törlése" gombbal, vagy e-mailben: info@myra-project.hu. A törlés során a felhasználói profil, a mérési eredmények (kérdőívek), a vállalt mikro-célok, a "Myra memóriája" kivonat, a megbízható eszközök, a fórum-hozzászólások, a játékeredmények és ranglista-bejegyzések, a még el nem küldött értesítések és az összes chat beszélgetés előzménye véglegesen törlődik a futó adatbázisból. A törölt adatok a biztonsági mentésekből a mentések megőrzési idejének lejártával (napi hét, óránkénti hat példány marad meg, így legfeljebb néhány napon belül) kerülnek ki; addig a mentésekhez kizárólag adatvesztés esetén, a rendszer helyreállítása céljából nyúl az adatkezelő. A hozzájárulás visszavonása a fiók és az adatok törlésének kérésével történhet. A hozzájárulás visszavonása nem érinti a visszavonás előtti adatkezelés jogszerűségét.

9. A felhasználó jogai
A felhasználó a GDPR alapján jogosult:
- tájékoztatást kérni az adatkezelésről,
- hozzáférni a róla kezelt adatokhoz,
- kérni az adatok helyesbítését,
- kérni az adatok törlését (a Beállítások menüben közvetlenül és azonnal végrehajtható),
- kérni az adathordozhatóságot (a GDPR 20. cikke alapján a Beállítások -> 'Adatok letöltése' menüpontban közvetlenül letölthető a teljes profil, a mérési előzmények, a vállalt mikro-célok és a chat előzmény gépileg olvasható JSON formátumban),
- kérni az adatkezelés korlátozását,
- tiltakozni a jogos érdeken alapuló adatkezelés ellen,
- hozzájárulását visszavonni,
- panaszt tenni a Nemzeti Adatvédelmi és Információszabadság Hatóságnál.

NAIH elérhetőség:
Nemzeti Adatvédelmi és Információszabadság Hatóság
Web: https://www.naih.hu

10. Automatizált döntéshozatal és mesterséges intelligencia
A felhasználó a chatben mesterséges intelligencia rendszerrel áll kapcsolatban, nem emberi beszélgetőpartnerrel; erről az alkalmazás a beszélgetési felületen is tájékoztat (az (EU) 2024/1689 rendelet 50. cikk (1) bekezdése).

A "Myra memóriája" kivonatot szintén mesterséges intelligencia állítja elő, kizárólag a felhasználó saját adataiból. A kivonat leíró jellegű, nem diagnózis, nem minősítés, és nem szolgál automatizált döntés alapjául. A felhasználó az adatexportban (GDPR 20. cikk) megtekintheti a róla tárolt kivonat pontos szövegét.

A Myra nem hoz hivatalos joghatással járó vagy a felhasználót hasonlóan jelentős mértékben érintő automatizált döntést. Az állapotkódok, kategóriák és chatbot-válaszok tájékoztató, önismereti és reflektív célú visszajelzések, nem hivatalos diagnózisok és nem egészségügyi döntések.

11. Kiskorúak
Az alkalmazás 18 éven aluli személyek számára nem elérhető. A regisztrációval a felhasználó kijelenti, hogy betöltötte a 18. életévét.

12. Cookie-k és helyi tárolás
Az alkalmazás a biztonságos működéshez szükséges munkamenet-azonosító (JWT) tokent tárolja a felhasználó készülékén. A hozzáférési token adminisztrátorok esetében a kiállítástól számított 1 óra után, normál felhasználóknál alapbeállítás szerint 7 nap után jár le. A lejárat nem a legutóbbi aktivitástól számított tétlenségi idő. A normál token érvényességét az üzemeltető konfigurálhatja. Kijelentkezéskor a szerver a fiók összes munkamenetét visszavonja, így a felhasználó minden eszközén kijelentkezik. Marketing vagy hirdetési célú nyomkövető cookie használata nem célja a rendszernek.

13. Adatvédelmi incidens
Adatvédelmi incidens gyanúja esetén az adatkezelő megteszi a szükséges technikai és szervezési lépéseket, és ha a GDPR alapján indokolt, értesíti az illetékes hatóságot és az érintetteket.

14. A tájékoztató módosítása
Az adatkezelő jogosult a tájékoztatót módosítani, különösen technikai, adatvédelmi, jogszabályi vagy működésbeli változás esetén. A lényeges változásokról a felhasználók az alkalmazáson keresztül vagy más megfelelő módon tájékoztatást kaphatnak.`;
