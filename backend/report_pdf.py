from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from esv import NORM_VERSION, _build_interpretation, measurement_value, has_measurement
from models import QuizSubmission, StateCode, User
from timeutil import _now

ROOT_DIR = Path(__file__).parent
FPDF_AVAILABLE = True


REPORT_FONT_DIR = ROOT_DIR / "assets" / "fonts"


REPORT_MAX_SESSIONS = 24


def _report_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "-"
    value = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        value = value.astimezone(ZoneInfo("Europe/Budapest"))
    except Exception:
        pass
    return value.strftime("%Y.%m.%d.")


_R_NAVY = (10, 35, 64)


_R_NAVY_DARK = (5, 17, 31)


_R_CYAN = (87, 199, 255)


_R_BLUE = (29, 142, 216)


_R_VIOLET = (139, 143, 232)


_R_TEXT = (13, 31, 53)


_R_TEXT_SOFT = (74, 93, 115)


_R_BG_SOFT = (234, 247, 255)


_R_ROW_ALT = (244, 249, 252)


_R_RULE = (206, 228, 242)


class _EsvReportPDF(FPDF):

    def footer(self):
        try:
            self.set_font("Manrope", "", 7)
        except Exception:
            return
        self.set_y(-13)
        self.set_text_color(122, 138, 154)
        half = (self.w - self.l_margin - self.r_margin) / 2
        self.set_x(self.l_margin)
        self.cell(half, 5, "Myra Project · ESV25 Inventory")
        self.cell(half, 5, f"{self.page_no()}/{{nb}}", align="R")


def _build_professional_report_pdf(user: User, sessions: list[QuizSubmission], titles: dict[str, StateCode]) -> bytes:
    pdf = _EsvReportPDF(format="A4")
    pdf.pdf_version = "1.7"
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("Manrope", "", str(REPORT_FONT_DIR / "Manrope_400Regular.ttf"))
    pdf.add_font("Manrope", "B", str(REPORT_FONT_DIR / "Manrope_700Bold.ttf"))
    pdf.add_font("ManropeSB", "", str(REPORT_FONT_DIR / "Manrope_600SemiBold.ttf"))
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    epw = pdf.w - pdf.l_margin - pdf.r_margin

    def section(title_txt: str) -> None:
        pdf.ln(2.5)
        y = pdf.get_y()
        pdf.set_fill_color(*_R_CYAN)
        pdf.rect(pdf.l_margin, y + 1.2, 2.4, 3.6, style="F")
        pdf.set_x(pdf.l_margin + 5.2)
        pdf.set_font("ManropeSB", "", 10.5)
        pdf.set_text_color(*_R_NAVY)
        pdf.cell(epw - 5.2, 6, title_txt, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(*_R_RULE)
        pdf.line(pdf.l_margin, pdf.get_y() + 0.6, pdf.l_margin + epw, pdf.get_y() + 0.6)
        pdf.ln(3.2)

    band_h = 40.0
    pdf.set_fill_color(*_R_NAVY_DARK)
    pdf.rect(0, 0, pdf.w, band_h, style="F")
    pdf.set_fill_color(*_R_NAVY)
    pdf.rect(0, 0, pdf.w, band_h - 3.0, style="F")
    try:
        with pdf.local_context(fill_opacity=0.16):
            pdf.set_fill_color(*_R_CYAN)
            pdf.ellipse(pdf.w - 78, -14, 84, 34, style="F")
        with pdf.local_context(fill_opacity=0.10):
            pdf.set_fill_color(*_R_VIOLET)
            pdf.ellipse(-20, 16, 90, 32, style="F")
        with pdf.local_context(fill_opacity=0.22):
            pdf.set_fill_color(*_R_CYAN)
            pdf.ellipse(pdf.w - 40, 6, 46, 22, style="F")
    except Exception:
        pass
    pdf.set_fill_color(*_R_CYAN)
    pdf.rect(0, band_h, pdf.w, 1.1, style="F")

    pdf.set_xy(pdf.l_margin, 8.5)
    pdf.set_font("Manrope", "B", 8)
    pdf.set_text_color(*_R_CYAN)
    try:
        pdf.set_char_spacing(1.6)
    except Exception:
        pass
    pdf.cell(epw, 5, "MYRA PROJECT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    try:
        pdf.set_char_spacing(0)
    except Exception:
        pass
    pdf.set_font("Manrope", "B", 19)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(epw, 10, "ESV25 Inventory — mérési kivonat", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("ManropeSB", "", 9)
    pdf.set_text_color(200, 226, 245)
    pdf.cell(epw, 6, "Szakember részére készült kivonat · Érzelem–Stressz–Viselkedés (ESV) modell",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(band_h + 8)
    warn_y0 = pdf.get_y()
    warn_bar_w = 1.6
    warn_pad_left = warn_bar_w + 4.0
    warn_pad_right = 3.0
    warn_pad_v = 3.2
    warn_text_w = epw - warn_pad_left - warn_pad_right
    warn_header = "FONTOS FIGYELMEZTETÉS"
    warn_paragraphs = [
        "Nem diagnózis, nem orvostechnikai eszköz. Az ESV25 Inventory a Myra Project önismereti, "
        "edukációs célú önbecslő kérdőíve.",
        "Nem helyettesíti a klinikai vizsgálatot vagy a szakemberrel való konzultációt, és nem alkalmas "
        "betegség vagy állapot megállapítására, kizárására, monitorozására vagy kezelésére.",
        "Minden érték kizárólag önbeszámolón alapul; az eredmények értelmezése képzett szakember feladata, "
        "a kliens tágabb kontextusának ismeretében.",
        "A kivonat a felhasználó saját kezdeményezésére készült.",
    ]

    pdf.set_xy(pdf.l_margin + warn_pad_left, warn_y0 + warn_pad_v)
    pdf.set_font("Manrope", "B", 9)
    warn_header_h = pdf.multi_cell(warn_text_w, 6.0, warn_header, dry_run=True, output="HEIGHT")
    pdf.set_font("Manrope", "", 8.6)
    warn_body_h = sum(
        pdf.multi_cell(warn_text_w, 4.9, p, dry_run=True, output="HEIGHT") for p in warn_paragraphs
    )
    warn_total_h = warn_pad_v * 2 + warn_header_h + 1.6 + warn_body_h

    pdf.set_fill_color(*_R_BG_SOFT)
    pdf.rect(pdf.l_margin, warn_y0, epw, warn_total_h, style="F")

    pdf.set_xy(pdf.l_margin + warn_pad_left, warn_y0 + warn_pad_v)
    pdf.set_font("Manrope", "B", 9)
    pdf.set_text_color(*_R_NAVY)
    pdf.multi_cell(warn_text_w, 6.0, warn_header, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1.6)
    pdf.set_font("Manrope", "", 8.6)
    pdf.set_text_color(52, 72, 94)
    for p in warn_paragraphs:
        pdf.set_x(pdf.l_margin + warn_pad_left)
        pdf.multi_cell(warn_text_w, 4.9, p, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_fill_color(*_R_CYAN)
    pdf.rect(pdf.l_margin, warn_y0, warn_bar_w, warn_total_h, style="F")

    pdf.set_y(warn_y0 + warn_total_h)
    pdf.ln(4)

    pdf.set_text_color(*_R_TEXT)
    meta_rows = [
        ("Név:", user.name or "-"),
        ("E-mail:", user.email or "-"),
        ("Kérdőív:", "ESV25 Inventory (21 tételes önkitöltő kérdőív)"),
        ("Mérések száma:", str(sum(has_measurement(s.norms or {}) for s in sessions))),
        ("Kivonat kelte:", _report_date(_now())),
    ]
    for label, value in meta_rows:
        pdf.set_font("ManropeSB", "", 9.5)
        pdf.cell(36, 5.8, label)
        pdf.set_font("Manrope", "", 9.5)
        pdf.set_text_color(*_R_TEXT)
        pdf.cell(epw - 36, 5.8, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    section("Mérési előzmények")

    col_w = {"date": 26, "code": 16, "dim": 15, "title": 0.0}
    col_w["title"] = epw - (col_w["date"] + col_w["code"] + 4 * col_w["dim"])
    pdf.set_font("ManropeSB", "", 8.6)
    pdf.set_fill_color(*_R_NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_w["date"], 7, "Dátum", border=0, align="C", fill=True)
    pdf.cell(col_w["code"], 7, "Kód", border=0, align="C", fill=True)
    for h in ("A", "P", "H", "C"):
        pdf.cell(col_w["dim"], 7, h, border=0, align="C", fill=True)
    pdf.cell(col_w["title"], 7, "Állapot", border=0, align="C", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Manrope", "", 8.6)
    for idx, s in enumerate(sessions):
        norms = s.norms or {}
        fill = idx % 2 == 1
        pdf.set_fill_color(*_R_ROW_ALT)
        pdf.set_text_color(*_R_TEXT)
        sc = titles.get(s.code)
        title_txt = f"{sc.title} ({sc.severity})" if sc and sc.severity else (sc.title if sc else "-")
        if len(title_txt) > 58:
            title_txt = title_txt[:57] + "…"
        pdf.cell(col_w["date"], 6.4, _report_date(s.created_at), border=0, align="C", fill=fill)
        pdf.set_font("ManropeSB", "", 8.6)
        pdf.set_text_color(*_R_BLUE)
        pdf.cell(col_w["code"], 6.4, s.code, border=0, align="C", fill=fill)
        pdf.set_font("Manrope", "", 8.6)
        pdf.set_text_color(*_R_TEXT)
        for key in ("a", "p", "h", "c"):
            measured = measurement_value(norms, key)
            val = f"{measured * 100:.0f}" if measured is not None else "-"
            pdf.cell(col_w["dim"], 6.4, val, border=0, align="C", fill=fill)
        pdf.cell(col_w["title"], 6.4, title_txt, border=0, align="L", fill=fill,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Manrope", "", 7.8)
    pdf.set_text_color(*_R_TEXT_SOFT)
    pdf.multi_cell(
        epw, 5.0,
        "A = Érzelmi állapot · P = Érzelemszabályozás · H = Észlelt stressz · C = Testi tünetek — "
        "az értékek POMP-pontszámok (0–100). A sávhatárok és az állapotkód részletes magyarázata "
        "a következő, Módszertan és pontozás szakaszban olvasható.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    section("Módszertan és pontozás")
    pdf.set_font("Manrope", "", 8.8)
    pdf.set_text_color(52, 72, 94)
    pdf.multi_cell(
        epw, 4.9,
        "Az ESV25 Inventory 21 tételes önkitöltő kérdőív, amely az Érzelem–Stressz–Viselkedés (ESV) modell "
        "négy dimenzióját méri. Minden skálát nemzetközileg validált mérőeszköz inspirált; alább a "
        "tételszám, a válaszskála, a hivatkozott eszköz és a belső megbízhatóság "
        "(n = 100 fős elsődleges validációs minta):",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(1)
    scale_facts = [
        "A – Érzelmi állapot (állapotszorongás): 6 tétel · 1–5 skála · inspiráció: STAI-S · "
        "α = 0,91 (95% CI 0,88–0,93)",
        "P – Érzelemszabályozás: 6 tétel · 1–5 skála, fordított pontozás · inspiráció: DERS · "
        "α = 0,87 (95% CI 0,83–0,91)",
        "H – Észlelt stressz: 4 tétel · 1–5 skála · inspiráció: PSS · α = 0,85 (95% CI 0,79–0,89)",
        "C – Testi tünetek: 5 tétel · 0–2 skála · inspiráció: PHQ-15 · α = 0,66 (95% CI 0,54–0,75)",
    ]
    for line in scale_facts:
        y = pdf.get_y()
        pdf.set_fill_color(*_R_BLUE)
        pdf.rect(pdf.l_margin + 1.2, y + 1.7, 1.5, 1.5, style="F")
        pdf.set_x(pdf.l_margin + 5)
        pdf.set_font("Manrope", "", 8.8)
        pdf.set_text_color(*_R_TEXT)
        pdf.multi_cell(epw - 5, 4.9, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Manrope", "", 8.2)
    pdf.set_text_color(*_R_TEXT_SOFT)
    pdf.multi_cell(
        epw, 4.6,
        "A C skála α-értéke (0,66) a szokásosan elvárt 0,70-es küszöb alatt van, ezért eredményei a többi "
        "skálánál óvatosabban értelmezendők.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(1.5)
    pdf.multi_cell(
        epw, 4.6,
        "A négy skála egymással elméletkonform irányban és mértékben függ össze (Pearson-korreláció, n = 100; "
        "minden érték p < 0,001 szinten szignifikáns): az érzelemszabályozás (P) negatívan korrelál az érzelmi "
        "állapottal, a stresszel és a testi tünetekkel (r = -0,71 / -0,71 / -0,44), míg ez utóbbi három egymással "
        "pozitívan (r = 0,57-0,77). Konvergens és diszkrimináns validitási vizsgálat (referenciaeszközökkel "
        "szemben, külön kutatási protokoll szerint) tervezett; eredménye egyelőre nem áll rendelkezésre.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(2)
    pdf.set_font("ManropeSB", "", 9)
    pdf.set_text_color(*_R_NAVY)
    pdf.cell(epw, 5.4, "Mi az a POMP-pontszám?", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Manrope", "", 8.8)
    pdf.set_text_color(52, 72, 94)
    pdf.multi_cell(
        epw, 4.9,
        "A POMP (Percent of Maximum Possible) a skála nyers összegpontszámát a skála elméleti terjedelmének "
        "százalékában fejezi ki: POMP = (nyers pont − elméleti minimum) / (elméleti maximum − elméleti minimum) × 100. "
        "Így minden skála 0–100 között mozog, a tételszámtól függetlenül összehasonlítható módon. A magasabb érték "
        "az adott jellemző erősebb jelenlétét jelzi; kivétel a P skála, ahol a magasabb érték erősebb, stabilabb "
        "érzelemszabályozást jelent (fordított irány).",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(2)
    pdf.set_font("ManropeSB", "", 9)
    pdf.set_text_color(*_R_NAVY)
    pdf.cell(epw, 5.4, "Sávok és állapotkód", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Manrope", "", 8.8)
    pdf.set_text_color(52, 72, 94)
    pdf.multi_cell(
        epw, 4.9,
        "Minden POMP-érték négy sáv egyikébe kerül: 1 = 0–30 · 2 = 31–60 · 3 = 61–80 · 4 = 81–100. "
        "Az állapotkód négy számjegye rendre az A-P-H-C skála sávértéke. Fontos: a sávhatárok jelenleg elméleti "
        "alapon rögzítettek; empirikus felülvizsgálatuk a folyamatban lévő validitási vizsgálat része. "
        f"Pontozási verzió: ESV v{NORM_VERSION} (POMP-normalizálás).",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    latest = sessions[-1]
    interpretation = _build_interpretation(latest.norms or {}, titles.get(latest.code))
    section(f"A legutóbbi állapotbejegyzés ({_report_date(latest.created_at)})")
    for item in interpretation["scales"]:
        pdf.set_font("ManropeSB", "", 8.9)
        pdf.set_text_color(*_R_BLUE)
        score_label = f" · POMP {item['pomp']}" if item["pomp"] is not None else ""
        pdf.multi_cell(epw, 5, f"{item['label']} — {item['band_label']}{score_label}",
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Manrope", "", 8.8)
        pdf.set_text_color(52, 72, 94)
        pdf.multi_cell(epw, 4.8, item["text"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if item["key"] == "c":
            pdf.set_font("Manrope", "", 7.6)
            pdf.set_text_color(*_R_TEXT_SOFT)
            pdf.multi_cell(
                epw, 4.2,
                "Megjegyzés: ennek a skálának a belső megbízhatósága a többinél alacsonyabb (α = 0,66) — "
                "ld. Módszertan és pontozás.",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
        pdf.ln(1)

    if len(sessions) >= 2:
        prev = sessions[-2]
        parts = []
        for key in ("a", "p", "h", "c"):
            new_value = measurement_value(latest.norms or {}, key)
            old_value = measurement_value(prev.norms or {}, key)
            if new_value is None or old_value is None:
                continue
            new_v, old_v = round(new_value * 100), round(old_value * 100)
            delta = new_v - old_v
            sign = f"+{delta}" if delta > 0 else str(delta)
            parts.append(f"{key.upper()}: {old_v} → {new_v} ({sign})")
        if parts:
            section(f"Változás az előző méréshez képest ({_report_date(prev.created_at)} → {_report_date(latest.created_at)})")
            pdf.set_font("Manrope", "", 8.8)
            pdf.set_text_color(*_R_TEXT)
            pdf.multi_cell(epw, 5, "   ·   ".join(parts), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Manrope", "", 7.8)
            pdf.set_text_color(*_R_TEXT_SOFT)
            pdf.cell(epw, 5, "Az értékek POMP-pontban értendők; a P skálán a növekedés erősödő szabályozást jelent.",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(3)
    pdf.set_draw_color(*_R_RULE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + epw, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Manrope", "", 8.2)
    pdf.set_text_color(52, 72, 94)
    pdf.multi_cell(
        epw, 4.6,
        "A fenti értelmezésre is érvényes a dokumentum elején olvasható figyelmeztetés: önbeszámolón "
        "alapuló tájékoztatás, nem diagnózis, és nem helyettesíti a szakemberi konzultációt.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(2)
    pdf.set_font("Manrope", "", 7.8)
    pdf.set_text_color(122, 138, 154)
    pdf.multi_cell(
        epw, 4.6,
        "Generálta a Myra Project alkalmazás a felhasználó kérésére. A dokumentum a felhasználó személyes adatait "
        "tartalmazza; kezelése a címzett szakember felelőssége.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    return bytes(pdf.output())
