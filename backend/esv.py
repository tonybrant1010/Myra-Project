from typing import Optional

from models import StateCode

NORM_VERSION = 2


def _bucket(norm: float) -> int:
    if norm <= 0.3:
        return 1
    if norm <= 0.6:
        return 2
    if norm <= 0.8:
        return 3
    return 4


SCALE_INTERPRETATION: dict[str, dict] = {
    "a": {
        "label": "A – Érzelmi állapot",
        "bands": {
            1: ("alacsony szorongás", "Az érzelmi állapot kiegyensúlyozottnak tűnik; a szorongásos élmények ritkák vagy enyhék."),
            2: ("enyhe szorongás", "Enyhe szorongásos jelzések látszanak; ezek a mindennapokban általában még jól kezelhetők."),
            3: ("emelkedett szorongás", "Emelkedett szorongásszintre utal; érdemes megfigyelni, mely helyzetek erősítik fel."),
            4: ("magas szorongás", "Kifejezett szorongásos terhelésre utal; ha tartósan fennáll, indokolt lehet szakemberrel átbeszélni."),
        },
    },
    "p": {
        "label": "P – Érzelemszabályozás",
        "bands": {
            1: ("gyenge érzelemszabályozás", "Az érzelmek szabályozása jelenleg nehezített lehet; az érzelmi hullámok könnyen elsodorhatnak."),
            2: ("ingadozó érzelemszabályozás", "Az érzelemszabályozás ingadozó; nyugodt időszakban jól működik, terhelés alatt gyengülhet."),
            3: ("stabil érzelemszabályozás", "Az érzelemszabályozás összességében stabil; a nehezebb érzésekkel való megküzdés többnyire működik."),
            4: ("erős érzelemszabályozás", "Erős, megbízható érzelemszabályozásra utal; ez fontos védőfaktor a terheléssel szemben."),
        },
    },
    "h": {
        "label": "H – Észlelt stressz",
        "bands": {
            1: ("alacsony stressz", "Az észlelt stresszterhelés alacsony; a mindennapi terhek jelenleg jól viselhetők."),
            2: ("enyhe stressz", "Mérsékelt stresszterhelést jelez; időnkénti feszültség mellett az egyensúly többnyire megvan."),
            3: ("emelkedett stressz", "Emelkedett stresszterhelésre utal; a pihenés és a határok tudatosabb védelme segíthet."),
            4: ("magas stressz", "Magas észlelt stresszt jelez; a tartós túlterhelés kimerüléshez vezethet, érdemes tehermentesíteni."),
        },
    },
    "c": {
        "label": "C – Testi tünetek",
        "bands": {
            1: ("kevés testi tünet", "A kérdőívben alig jelent meg testi tünet; a feszültség kevéssé mutatkozik testi szinten."),
            2: ("enyhe testi tünetek", "Enyhe testi jelzések (pl. feszülés, fáradtság) jelentek meg; érdemes figyelni rájuk."),
            3: ("fokozott testi tünetek", "Fokozott testi tünetterhelésre utal; a tartós feszültség gyakran a testen keresztül jelez."),
            4: ("kifejezett testi tünetek", "Kifejezett testi tünetterhelésre utal; tartós panaszok esetén orvosi kivizsgálás is indokolt lehet."),
        },
    },
}


INTERPRETATION_DISCLAIMER = (
    "Az értelmezés önbeszámolós kérdőíven alapuló tájékoztatás, nem diagnózis, "
    "és nem helyettesíti a szakemberrel való konzultációt."
)


def measurement_value(norms: dict, key: str) -> Optional[float]:
    import math
    if (norms or {}).get("source") == "manual_code":
        return None
    try:
        value = float(norms[key])
    except (KeyError, TypeError, ValueError):
        return None
    return max(0.0, min(1.0, value)) if math.isfinite(value) else None


def has_measurement(norms: dict) -> bool:
    return all(measurement_value(norms, key) is not None for key in ("a", "p", "h", "c"))


def _build_interpretation(norms: dict, sc: Optional[StateCode] = None) -> dict:
    scales = []
    for key in ("a", "p", "h", "c"):
        val = measurement_value(norms, key)
        if val is None:
            scales.append({"key": key, "label": SCALE_INTERPRETATION[key]["label"],
                           "pomp": None, "band": None, "band_label": "Nincs mérési adat",
                           "text": "Ehhez a skálához nem áll rendelkezésre kérdőíves mérési adat."})
            continue
        band = _bucket(val)
        band_label, text = SCALE_INTERPRETATION[key]["bands"][band]
        scales.append({
            "key": key,
            "label": SCALE_INTERPRETATION[key]["label"],
            "pomp": round(val * 100),
            "band": band,
            "band_label": band_label,
            "text": text,
        })
    overall = None
    if sc is not None:
        overall = {"code": sc.code, "title": sc.title, "severity": sc.severity}
    return {"scales": scales, "overall": overall, "has_measurement": has_measurement(norms),
            "disclaimer": INTERPRETATION_DISCLAIMER}
