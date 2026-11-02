ACUTE = "ACUTE"
ELEVATED = "ELEVATED"
NONE = "NONE"

WORSE = "WORSE"
SAME = "SAME"
BETTER = "BETTER"
NA = "NA"


SEVERE_TERMS = [
    "öngyilkos", "ongyilkos", "szuicid", "megölöm magam", "megolom magam",
    "meg akarok halni", "nem akarok élni", "nem akarok elni", "nem akarok tovább élni",
    "nem akarok tovabb elni", "véget akarok vetni", "veget akarok vetni", "végzek magammal",
    "vegzek magammal", "végezni magammal", "vegezni magammal", "bántani akarom magam",
    "bantani akarom magam", "kárt tenni magamban", "kart tenni magamban",
]
SEVERE_COMPACT = ["nemakarokélni", "nemakarokelni", "megakarokhalni"]


_BASE_PREFILTER_TERMS = [

    "meghal", "meghalt", "halál", "halal", "véget", "veget", "végem", "vegem", "vége", "vege",
    "öngyilkos", "ongyilkos", "szuicid", "kinyír", "kinyir", "felakaszt", "kötél", "kotel",
    "kiugr", "leugr", "ablak", "gyógyszer", "gyogyszer", "tabletta", "bevettem",

    "vérz", "verz", "véres", "veres", "nyakam", "levegőt", "levegot", "sérül", "serul",
    "eltör", "eltor", "tűz", "tuz", "felgyújt", "felgyujt", "robban",

    "nem bírom", "nem birom", "nem akarok", "nem tudok tovább", "nem tudok tovabb",
    "bánt", "bant", "értelmetlen", "ertelmetlen", "reménytelen", "remenytelen",
    "kimerült", "kimerult", "pánik", "panik", "szorong", "depressz", "krízis", "krizis",
    "egyedül", "egyedul", "senki nem", "fáradt", "faradt",
]


PREFILTER_TERMS = _BASE_PREFILTER_TERMS + [
    t for t in SEVERE_TERMS if t not in _BASE_PREFILTER_TERMS
]

JUDGE_PROMPT = (
    "Egy mentálhigiénés naplóüzenetet kell minősítened. "
    "Az első sorban KÉT szót írj: a szintet (ACUTE / ELEVATED / NONE) és a trendet "
    "(WORSE / SAME / BETTER / NA), utána legfeljebb 12 szó indoklás.\n"
    "SZINT:\n"
    "ACUTE: a szerző MAGÁRÓL, jelen időben, konkrét önveszélyt ír le (öngyilkossági szándék, "
    "önsértés, halálos szándék, közvetlen életveszély, baleset, vérzés).\n"
    "ELEVATED: súlyos distressz, reménytelenség, de nincs konkrét önveszély.\n"
    "NONE: idézet, könyv vagy film szereplője, tagadás („nem vagyok öngyilkos”), múlt idő, "
    "hipotetikus, másról szól, vagy hétköznapi bosszúság.\n"
    "TREND (az előző állapothoz képest):\n"
    "WORSE: egyértelműen súlyosbodott (konkrétabb szándék, eszköz, közvetlenség, „most”).\n"
    "BETTER: egyértelműen javult, enyhült, segítséget kért, vagy kilép a krízisből.\n"
    "SAME: hasonló, mint korábban.\n"
    "NA: nincs értelmezhető előzmény, vagy az üzenet nem a szerző állapotáról szól.\n"
    "Példák:\n"
    "„Egy regényben azt mondta a főszereplő, hogy meg akarok halni.” -> NONE NA idézet regényből.\n"
    "„kiugrottam az ablakon, eltört a lábam, vérzik a nyakam” -> ACUTE WORSE életveszélyes sérülés.\n"
    "„bevettem a gyógyszereket, itt a levél” -> ACUTE WORSE konkrét szándék és eszköz.\n"
    "„nem akarok élni” -> ACUTE SAME közvetlen önveszély.\n"
    "„kicsit jobban vagyok, felhívtam a barátomat” -> NONE BETTER enyhülés, segítségkérés.\n"
    "„nem bírom tovább ezt a munkát” -> ELEVATED SAME distressz, nincs önveszély.\n"
    "A válasz első két szava legyen a szint és a trend, utána rövid indoklás."
)


ACTION_OPEN = "open"
ACTION_ESCALATE = "escalate"
ACTION_CLOSE = "close"
ACTION_KEEP = "keep"
ACTION_IGNORE = "ignore"


def _normalize(text: str) -> str:
    return (text or "").lower()


def _compact(text: str) -> str:
    import re
    return re.sub(r"\s+", "", text)


def is_severe(text: str) -> bool:
    normalized = _normalize(text)
    compact = _compact(normalized)
    return (
        any(t in normalized for t in SEVERE_TERMS)
        or any(t in compact for t in SEVERE_COMPACT)
    )


def prefilter_hits(text: str) -> list:
    normalized = _normalize(text)
    return [t for t in PREFILTER_TERMS if t in normalized]


def parse_verdict(raw: str):
    text = (raw or "").strip()
    if not text:
        return "", "", "üres modellválasz"
    first = text.splitlines()[0].strip()
    upper = first.upper()

    level = ""
    for candidate in (ACUTE, ELEVATED, NONE):
        if candidate in upper:
            level = candidate
            break
    if not level:
        return "", "", "nem érthető modellválasz: " + text[:60]

    trend = ""
    rest = upper
    for candidate in (WORSE, BETTER, SAME, NA):
        if candidate in rest:
            trend = candidate
            break
    if not trend:
        trend = NA

    reason = " ".join(text.splitlines())
    for token in (level, trend):
        if token:
            reason = reason.replace(token, " ", 1)
            reason = reason.replace(token.lower(), " ", 1)
    return level, trend, reason.strip(" :|-\t")[:140]


class Episode:

    __slots__ = ("opened_at", "last_event_at", "peak", "messages", "escalations", "notified")

    def __init__(self, opened_at: float):
        self.opened_at = opened_at
        self.last_event_at = opened_at
        self.peak = ACUTE
        self.messages = 1
        self.escalations = 0
        self.notified = False


def step(episode, level: str, trend: str, now: float):
    if level == ACUTE:
        if episode is None:
            return ACTION_OPEN, Episode(now)
        episode.messages += 1
        episode.last_event_at = now
        if trend == WORSE:
            episode.escalations += 1
            return ACTION_ESCALATE, episode
        return ACTION_KEEP, episode

    if episode is not None:
        episode.messages += 1
        episode.last_event_at = now
        if trend == BETTER:
            return ACTION_CLOSE, episode
        return ACTION_KEEP, episode

    return ACTION_IGNORE, None


def idle_timeout(episode, now: float, idle_min: int) -> bool:
    if episode is None or idle_min <= 0:
        return False
    return (now - episode.last_event_at) >= idle_min * 60


def summary(episode, now: float) -> str:
    if episode is None:
        return "-"
    minutes = max(0, int((now - episode.opened_at) / 60))
    return (
        f"epizód hossza: {minutes} perc, "
        f"üzenetek: {episode.messages}, "
        f"súlyosbodás: {episode.escalations}"
    )
