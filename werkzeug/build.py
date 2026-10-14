#!/usr/bin/env python3
"""BCE Vereinsnews: Generator fuer die Versand-, Web- und Vorschau-Version.

Grundsaetze (siehe Style Guide):
* alles inline, keine Abhaengigkeit von <style>, Media Queries oder MSO-Kommentaren
  (Gmail-Compose entfernt beim Einfuegen <head>, <style> und Kommentare)
* feste 600er Breite per Attribut fuer Outlook, max-width:100% fuer Mobil
* Systemschriften zuerst im Stack (Outlook faellt sonst auf Times zurueck)
* ein Token-Satz fuer Abstaende, Typo, Buttons, Kanten

Aufruf:
  python3 build.py [ausgabeordner] [ausgabe ...]
  ohne Ausgabe-Namen werden alle Ausgaben gebaut, z. B. nur die neue:
  python3 build.py out frauen
"""
import base64, pathlib, sys, urllib.parse

HERE = pathlib.Path(__file__).parent
SITE = "https://bcerfurt.de"
ASSETS = f"{SITE}/newsletter"          # Web-Versionen (nur wenn WEB_PAGES)
# Bilder und .ics liegen im GitHub-Repo weblokks/bce_newsletter (oeffentlich, Ordner assets/)
IMG_BASE = "https://raw.githubusercontent.com/weblokks/bce_newsletter/main/assets"
WEB_PAGES = False   # True, sobald die Web-Versionen auf bcerfurt.de/newsletter/ liegen
ICS_URL = f"{IMG_BASE}/mitgliederversammlung-2026.ics"
UE40_ICS_URL = f"{IMG_BASE}/ue40-landesfinale-2026.ics"
SENDER = "vorstand@bcerfurt.de"

# ---------- Ausgaben (je eine E-Mail) ----------
# rewe: (gesammelt, Ziel, Stand) je Ausgabe, damit alte Ausgaben beim Neubau unveraendert bleiben
ISSUES = {
    "einladung": dict(
        slug="2026-10-einladung-mitgliederversammlung",
        file="BCE_2026-10_Einladung-Mitgliederversammlung",
        campaign="2026-10-einladung-mv",
        subject="Einladung zur Mitgliederversammlung am 5. Dezember",
        preheader="Samstag, 10 Uhr im LSB. Wir wählen den 1. und 2. Vorsitzenden und den Sportbeauftragten neu.",
        assets=(),
    ),
    "news": dict(
        slug="2026-10-neues-aus-dem-bcerfurt",
        file="BCE_2026-10_Neues-aus-dem-bcerfurt",
        campaign="2026-10-news",
        subject="Neues aus dem #bcerfurt: Musa geht nach Bamberg",
        preheader="Außerdem: REWE Vereinsscheine nur noch bis 11. Oktober und Gesundheitstage bei pro optik im Dezember.",
        rewe=(478, 2670, "30.09.2026"),
        assets=("2026-10-musa.jpg", "bce-logo-header.png"),
    ),
    "frauen": dict(
        slug="2026-10-neues-aus-dem-bcerfurt-frauenbasketball",
        file="BCE_2026-10_Neues-aus-dem-bcerfurt_Frauenbasketball",
        campaign="2026-10-frauenbasketball",
        subject="Neues aus dem #bcerfurt: Frauen-Basketball",
        preheader="Außerdem: REWE Scheine noch bis 25. Oktober zuordnen und unsere Ü40 im Landesfinale am 21. November.",
        rewe=(1438, 2670, "13.10.2026"),
        assets=("2026-10-frauen.jpg", "2026-10-ue40.jpg", "bce-logo-header.png"),
    ),
}
CUR = {}   # wird in build() gesetzt


def web_url(issue):
    return f"{ASSETS}/{ISSUES[issue]['slug']}.html"

# ---------- Links und Termine, vor Versand pruefen ----------
REWE_URL = "https://scheinefuervereine.rewe.de/verein/10000090358"
PROOPTIK_URL = "https://prooptik-erfurt.de/termin-vereinbaren/"
MUSA_URL = "https://www.instagram.com/p/Dd3830hCJ49/?img_index=19"

# ---------- Tokens ----------
HEAD = "Impact, 'Arial Narrow Bold', 'Arial Narrow', 'Roboto Condensed', 'sans-serif-condensed', Arial, sans-serif"
BODY = "Arial, Helvetica, sans-serif"
PX = 32                 # Seitenrand
GAP_SECTION = 40
GAP_BLOCK = 16
GAP_BOX = 24
ACCENT_W = 4            # Akzentkante

THEMES = {
    "A": dict(name="Nachtspiel", outer="#171717", card="#222222", text="#EBEBEB", muted="#A3A3A3",
              heading="#FFFFFF", line="#3A3A3A", box="#2B2B2B", label="#11AFCC", link="#FFFFFF",
              stripe="#EA2127", scheme="dark"),
    "B": dict(name="Hallenlicht", outer="#EBEBEB", card="#FFFFFF", text="#222222", muted="#525252",
              heading="#171717", line="#E0E0E0", box="#F6F6F6", label="#C8161C", link="#C8161C",
              stripe="#11AFCC", scheme="light"),
}
RED, DARK, BTN_TEXT = "#EA2127", "#171717", "#FFFFFF"


def de(n):
    return f"{n:,}".replace(",", ".")


def utm(url):
    q = f"utm_source=vereinsnews&utm_medium=email&utm_campaign={CUR.get('campaign', 'vereinsnews')}"
    return url + ("&" if "?" in url else "?") + q


def maps(q):
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)


def gcal(text, dates, details, location):
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(
        {"action": "TEMPLATE", "text": text, "dates": dates, "details": details, "location": location})


CAL_URL = gcal("Mitgliederversammlung BC Erfurt", "20261205T090000Z/20261205T110000Z",
               "Mitgliederversammlung 2026 des Basketball Club Erfurt e.V. mit Vorstandswahlen. Seminarraum 129.",
               "Landessportbund Thüringen, Werner-Seelenbinder-Straße 1, 99096 Erfurt")
MAPS_URL = maps("Landessportbund Thüringen, Werner-Seelenbinder-Straße 1, 99096 Erfurt")

# Ue40-Landesfinale: Sa 21.11.2026, 14 Uhr (MEZ = UTC+1), Ende geschaetzt 19:30 Uhr nach dem Finale
UE40_ORT = "Fit-In, Osterlange 13, 99189 Elxleben"
UE40_CAL_URL = gcal("Ü40-Landesfinale mit dem BC Erfurt", "20261121T130000Z/20261121T183000Z",
                    "14:00 Halbfinale SG BC Erfurt / BBC Mühlhausen gegen Culture City Weimar, "
                    "16:00 Halbfinale Science City Jena gegen USV Erfurt, 18:00 Finale.", UE40_ORT)
UE40_MAPS_URL = maps(UE40_ORT)
DOMSPORTHALLE_MAPS_URL = maps("Domsporthalle Erfurt")
FRAUEN_MAIL = f"mailto:{SENDER}?" + urllib.parse.urlencode(
    {"subject": "Probetraining Frauen-Basketball", "body": "Hallo, ich möchte gern beim Frauen-Basketball am Dienstag vorbeikommen."},
    quote_via=urllib.parse.quote)

UNSUB = f"mailto:{SENDER}?" + urllib.parse.urlencode(
    {"subject": "Vereinsnews abbestellen", "body": "Bitte nehmt mich aus dem Verteiler der BCE Vereinsnews."},
    quote_via=urllib.parse.quote)


# ---------- Bausteine ----------
class B:
    def __init__(self, t, mode="send"):
        self.t = t
        self.mode = mode

    def asset(self, name, mime="image/jpeg"):
        f = HERE / name
        if self.mode == "preview" and f.exists():
            return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
        return f"{IMG_BASE}/{name}"

    def img(self, name, w, h, alt, credit=None):
        t = self.t
        if self.mode == "gmail":
            return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                    f'<td align="center" bgcolor="{t["line"]}" style="background:{t["line"]};padding:28px 16px;font-family:{BODY};'
                    f'font-size:14px;line-height:20px;font-weight:bold;color:{RED};">FOTO HIER EINFÜGEN ({name})</td></tr></table>'
                    '<div style="height:16px;line-height:16px;font-size:1px;">&nbsp;</div>')
        out = (f'<img src="{self.asset(name)}" width="{w}" height="{h}" alt="{alt}" '
               f'style="display:block;width:100%;max-width:{w}px;height:auto;border:0;background:{t["line"]};'
               f'font-family:{BODY};font-size:14px;line-height:20px;color:{t["muted"]};">')
        if credit:
            out += (f'<p style="margin:6px 0 0 0;font-family:{BODY};font-size:11px;line-height:15px;color:{t["muted"]};">{credit}</p>')
        return out + '<div style="height:16px;line-height:16px;font-size:1px;">&nbsp;</div>'

    def a(self, href, label, bold=False, color=None):
        c = color or self.t["link"]
        w = "font-weight:bold;" if bold else ""
        tgt = "" if href.startswith("mailto:") else ' target="_blank"'
        return f'<a href="{href}"{tgt} style="color:{c};{w}text-decoration:underline;">{label}</a>'

    def row(self, inner, top=GAP_BLOCK, bottom=0):
        return f'\n<tr><td style="padding:{top}px {PX}px {bottom}px {PX}px;">{inner}</td></tr>'

    def label(self, txt, color=None):
        return (f'<p style="margin:0 0 8px 0;font-family:{BODY};font-size:12px;line-height:16px;font-weight:bold;'
                f'letter-spacing:1.5px;text-transform:uppercase;color:{color or self.t["label"]};">{txt}</p>')

    def h1(self, txt):
        return (f'<h1 style="margin:0;font-family:{HEAD};font-size:36px;line-height:40px;font-weight:normal;'
                f'text-transform:uppercase;color:{self.t["heading"]};word-break:break-word;">{txt}</h1>')

    def h2(self, txt, top=GAP_SECTION):
        return self.row(f'<h2 style="margin:0;font-family:{HEAD};font-size:28px;line-height:32px;font-weight:normal;'
                        f'text-transform:uppercase;color:{self.t["heading"]};word-break:break-word;">{txt}</h2>', top=top)

    def h3(self, txt, level=3):
        return (f'<h{level} style="margin:0;font-family:{HEAD};font-size:22px;line-height:26px;font-weight:normal;'
                f'text-transform:uppercase;color:{self.t["heading"]};word-break:break-word;">{txt}</h{level}>')

    def ptag(self, html, size=16, color=None, top=0):
        lh = {16: 24, 15: 23, 14: 21, 13: 19, 12: 18}[size]
        return (f'<p style="margin:{top}px 0 0 0;font-family:{BODY};font-size:{size}px;line-height:{lh}px;'
                f'color:{color or self.t["text"]};">{html}</p>')

    def p(self, html, size=16, top=GAP_BLOCK):
        return self.row(self.ptag(html, size), top=top)

    def button(self, href, label):
        return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td bgcolor="{RED}" style="background:{RED};border-radius:4px;padding:14px 22px;">'
                f'<a href="{href}" target="_blank" style="font-family:{BODY};font-size:13px;line-height:16px;'
                f'font-weight:bold;letter-spacing:1px;text-transform:uppercase;color:{BTN_TEXT};text-decoration:none;'
                f'display:inline-block;">{label}</a></td></tr></table>')

    def box(self, inner, top=GAP_BOX):
        return self.row(
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td width="{ACCENT_W}" bgcolor="{RED}" style="background:{RED};width:{ACCENT_W}px;font-size:1px;line-height:1px;">&nbsp;</td>'
            f'<td bgcolor="{self.t["box"]}" style="background:{self.t["box"]};padding:24px;">{inner}</td></tr></table>', top=top)

    def divider(self):
        return self.row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                        f'<td height="1" bgcolor="{self.t["line"]}" style="height:1px;font-size:1px;line-height:1px;background:{self.t["line"]};">&nbsp;</td>'
                        f'</tr></table>', top=GAP_SECTION)

    def kv_table(self, rows, key_w=None, key_strong=False, val_strong=True):
        t = self.t
        out = []
        for i, (k, v) in enumerate(rows):
            b = f"border-top:1px solid {t['line']};" if i else ""
            kw = f' width="{key_w}"' if key_w else ""
            kstyle = f"color:{t['heading']};font-weight:bold;" if key_strong else f"color:{t['muted']};"
            vstyle = "font-weight:bold;" if val_strong else ""
            out.append(f'<tr><td valign="top"{kw} style="{b}padding:10px 12px 10px 0;font-family:{BODY};font-size:14px;line-height:20px;{kstyle}">{k}</td>'
                       f'<td valign="top" style="{b}padding:10px 0;font-family:{BODY};font-size:14px;line-height:20px;color:{t["text"]};{vstyle}">{v}</td></tr>')
        return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{"".join(out)}</table>'


# ---------- Inhalt ----------
def rewe_bar(b, t, prize="eine Anzeigetafel"):
    have, goal, _ = CUR["rewe"]
    pct = max(3, min(100, round(have / goal * 100)))
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:16px;"><tr>'
            f'<td width="{pct}%" height="10" bgcolor="{RED}" style="background:{RED};height:10px;font-size:1px;line-height:1px;">&nbsp;</td>'
            f'<td height="10" bgcolor="{t["line"]}" style="background:{t["line"]};height:10px;font-size:1px;line-height:1px;">&nbsp;</td>'
            f'</tr></table>'
            + b.ptag(f'<strong style="color:{t["text"]};">{de(have)} von {de(goal)} Scheinen</strong> für unsere Wunschprämie, {prize}',
                     size=13, color=t["muted"], top=6))


def parts(b, t):
    fact = b.kv_table([
        ("Wann", "Samstag, 5. Dezember 2026<br><span style=\"font-weight:normal;\">10:00 bis 12:00 Uhr</span>"),
        ("Wo", b.a(MAPS_URL, "Landessportbund Thüringen", bold=True, color=t["text"]) +
               "<br><span style=\"font-weight:normal;\">Seminarraum 129<br>Werner-Seelenbinder-Straße 1, 99096 Erfurt</span>"),
        ("Stimme", "<span style=\"font-weight:normal;\">Jedes Mitglied hat eine Stimme. Für Mitglieder unter 18 Jahren stimmt ein Elternteil ab.</span>"),
    ], key_w=72)

    wahl = "".join(
        f'<tr><td style="{"border-top:1px solid " + t["line"] + ";" if i else ""}padding:{"0" if i == 0 else "12px"} 0 {"0" if i == 2 else "12px"} 0;">'
        f'<p style="margin:0;font-family:{BODY};font-size:16px;line-height:22px;font-weight:bold;color:{t["heading"]};">{amt}</p>'
        f'<p style="margin:2px 0 0 0;font-family:{BODY};font-size:14px;line-height:20px;color:{t["muted"]};">bisher {name}</p></td></tr>'
        for i, (amt, name) in enumerate([("1. Vorsitzender", "Alexander Hüller"), ("2. Vorsitzender", "Marc Reimschüssel"),
                                         ("Sportbeauftragter", "Aaron Rommeley")]))
    wahl = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{wahl}</table>'

    bleibt = b.kv_table([
        ("Kassenwartin", "Theresia Piszczan"),
        ("Schriftführer", "David Bretschneider"),
        ("Schiedsrichterbeauftragter", "Maximilian Paul Reymann"),
        ("Rechnungsprüfer", "Tanja Schäffner, Marko Fliege"),
    ], val_strong=False)

    agenda_items = [
        "Eröffnung der Versammlung",
        "Wahl des Versammlungs- und Wahlleiters",
        "Feststellung der ordnungsgemäßen Einberufung und der Beschlussfähigkeit",
        "Genehmigung der Tagesordnung",
        "Berichte über das Vereinsjahr: 1. Vorsitzender, Sportbeauftragter, Kassenwartin, Rechnungsprüfer",
        "Aussprache zu den Berichten",
        "Entlastung des Vorstandes",
        "Wahlvorschläge",
        "Wahlen: 1. Vorsitzender, 2. Vorsitzender, Sportbeauftragter",
        "Planung der Saison 2026/27",
        "Schlusswort",
    ]
    agenda = "".join(
        f'<tr><td valign="top" width="36" style="padding:6px 0;font-family:{HEAD};font-size:20px;line-height:22px;color:{RED};">{i:02d}</td>'
        f'<td valign="top" style="padding:6px 0;font-family:{BODY};font-size:15px;line-height:22px;color:{t["text"]};">{x}</td></tr>'
        for i, x in enumerate(agenda_items, 1))
    agenda = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{agenda}</table>'

    spacer = '<div style="height:18px;line-height:18px;font-size:1px;">&nbsp;</div>'
    mail = b.a(f"mailto:{SENDER}", SENDER, bold=True)

    sig = lambda closing: "".join([
        b.p(closing, top=GAP_SECTION),
        b.row(b.ptag("Sportliche Grüße") +
              b.ptag("<strong>Alexander Hüller</strong><br>"
                     f"<span style=\"color:{t['muted']};font-size:14px;\">1. Vorsitzender, für den Vorstand des BC Erfurt</span>", top=12),
              top=GAP_BLOCK, bottom=GAP_SECTION)])

    mv_hint = b.row(b.label("Termin vormerken") + b.h3("Mitgliederversammlung am 5. Dezember", level=2) +
                    b.ptag("Samstag, 10:00 bis 12:00 Uhr, im Landessportbund Thüringen. Die Einladung mit Tagesordnung bekommt ihr in einer eigenen E-Mail. "
                           + (b.a(web_url("einladung"), "Einladung online lesen") + "." if WEB_PAGES and b.mode != "gmail" else ""), size=15, top=10), top=GAP_SECTION)
    return dict(fact=fact, wahl=wahl, bleibt=bleibt, agenda=agenda, spacer=spacer, mail=mail, sig=sig, mv_hint=mv_hint)


def content_einladung(b, t):
    c = parts(b, t)
    return "".join([
        b.row(b.label("Mitgliederversammlung 2026") + b.h1("Einladung zur Mitglieder&shy;versammlung"), top=GAP_SECTION),
        f'\n<tr><td style="padding:{GAP_BOX}px 0 0 0;"><img src="https://bcerfurt.de/images/gallery/foto-spiel-10.jpg" width="600" height="400" '
        f'alt="Trainer und Spieler des BC Erfurt bei einer Teambesprechung in der Halle" '
        f'style="display:block;width:100%;max-width:600px;height:auto;border:0;background:{t["box"]};'
        f'font-family:{BODY};font-size:14px;line-height:20px;color:{t["muted"]};"></td></tr>',
        b.p("Liebe Mitglieder, liebe Eltern,", top=GAP_BOX),
        b.p("hiermit lädt der Vorstand euch herzlich zur Mitgliederversammlung 2026 des Basketball Club Erfurt e.V. ein. "
            "Wir blicken auf das Vereinsjahr zurück, die Kassenwartin stellt den Kassenbericht vor, und wir wählen drei Vorstandsämter neu."),
        b.box(c["fact"]),
        b.row(b.button(CAL_URL, "Im Kalender eintragen") +
              b.ptag("Apple Kalender oder Outlook? " + b.a(ICS_URL, "Termin als Datei laden (.ics)"), size=13, color=t["muted"], top=10), top=GAP_BOX),
        b.p("Ihr könnt nicht kommen? Dann kann euch ein anderes Mitglied mit schriftlicher Vollmacht vertreten. "
            "Die unterschriebene Vollmacht gibt euer Vertreter zu Beginn der Versammlung beim Vorstand ab.", size=14, top=GAP_BOX),

        b.divider(),
        b.h2("Tagesordnung"),
        b.row(c["agenda"]),
        b.p(f"Anträge zur Tagesordnung schickt ihr bitte vorab an {b.a('mailto:' + SENDER, SENDER)}.", size=14),

        b.divider(),
        b.h2("Vorstandswahlen 2026"),
        b.p("Unser Vorstand hat sechs Ämter mit einer Amtszeit von jeweils zwei Jahren. Gewählt wird im Wechsel, "
            "damit nie der ganze Vorstand auf einmal neu ist. Am 5. Dezember stehen diese drei Ämter zur Wahl:"),
        b.box(c["wahl"], top=GAP_BLOCK),
        b.row(b.label("Bis 2027 im Amt", color=t["muted"]) + c["bleibt"], top=GAP_BOX),
        b.p(f"Ihr möchtet kandidieren oder jemanden vorschlagen? Schreibt uns an {c['mail']}. "
            "Wahlvorschläge sind auch in der Versammlung selbst noch möglich."),

        c["sig"]("Fragen zur Versammlung oder zu den Wahlen? Antwortet einfach auf diese E-Mail. Wir freuen uns auf euch!"),
    ])


def prooptik_box(b, t, sp, label="Partner-Aktion · 8. bis 10. Dezember", hint=""):
    return b.box(b.label(label) + b.h3("Gesundheitstage bei pro optik", level=2) +
              b.ptag("Unser Partner pro optik lädt alle BCE-Mitglieder, ihre Familien und Freunde zu den Gesundheitstagen ein. "
                     "Vom <strong>8. bis 10. Dezember</strong>, jeweils 9:00 bis 18:00 Uhr, bekommt ihr in beiden Erfurter Filialen "
                     "einen professionellen Sehtest (ab 10 Jahren), eine Augeninnendruckmessung (ab 18 Jahren) und einen Hörtest.", size=15, top=10) +
              '<div style="height:12px;line-height:12px;font-size:1px;">&nbsp;</div>' +
              b.kv_table([("30 %", "auf alle Brillen mit Sehstärke"), ("10 %", "auf alle Sonnenbrillen ohne Sehstärke")],
                         key_w=64, key_strong=True, val_strong=False) +
              b.ptag("Partner-Vorteile für BCE-Mitglieder, einzelne Produkte sind ausgenommen.", size=13, color=t["muted"], top=6) +
              b.ptag("<strong>Filialen:</strong> Bahnhofstraße 39 und Mainzerhofplatz 14, 99084 Erfurt. "
                     "Damit alles reibungslos läuft, bucht bitte vorab online einen Termin.", size=15, top=12) +
              (b.ptag(hint, size=15, top=10) if hint else "") +
              sp + b.button(PROOPTIK_URL, "Termin buchen"), top=GAP_BLOCK)


def content_news(b, t):
    c = parts(b, t)
    sp = c["spacer"]
    return "".join([
        b.row(b.label("Oktober 2026") + b.h1("Neues aus dem #bcerfurt"), top=GAP_SECTION),
        b.p("Liebe Mitglieder, liebe Eltern,", top=GAP_BOX),
        b.p("hier sind die Neuigkeiten aus unserem Verein. Ganz vorn steht eine Erfolgsgeschichte, die in unserer Halle begonnen hat."),

        b.box(b.img("2026-10-musa.jpg", 484, 484, "Musa als junger Spieler im dunklen Trikot mit der Nummer 4 beim Dribbling in der Halle",
                    credit="Foto: Basketball Löwen Erfurt, Instagram") + b.label("Eigengewächs") + b.h3("Vom BCE nach Bamberg: Musa unterschreibt für drei Jahre", level=2) +
              b.ptag("Mit 9 Jahren hatte Musa beim BC Erfurt seinen ersten Ballkontakt. Heute ist er 20, Junioren-Nationalspieler "
                     "und wechselt von den Basketball Löwen Erfurt zu den Bamberg Baskets. Dort hat er einen Dreijahresvertrag unterschrieben.", size=15, top=10) +
              b.ptag("Musa ist ein Eigengewächs unseres Vereins und zeigt, wie weit man mit Basketball kommen kann, wenn man früh anfängt und dranbleibt. "
                     "Wir sind stolz auf dich, Musa, und drücken dir für den nächsten Schritt die Daumen.", size=15, top=10) +
              b.ptag("Jede Karriere beginnt mit dem ersten Training. Kennt ihr Kinder, die es ausprobieren möchten? "
                     + b.a(utm(SITE + "/training"), "Hier geht es zum Probetraining") + ".", size=15, top=10) +
              sp + b.button(MUSA_URL, "Beitrag ansehen"), top=GAP_BOX),
        b.box(b.label("Nur noch bis 11. Oktober") + b.h3("REWE Scheine für Vereine", level=2) +
              b.ptag("Bei REWE gibt es für je 15 € Einkauf einen Vereinsschein, mit REWE Bonus und gescannter App sogar einen zusätzlichen. "
                     "Die Scheine werden bis zum <strong>11. Oktober</strong> ausgegeben, zuordnen könnt ihr sie bis zum <strong>25. Oktober</strong>. "
                     "Fragt auch Großeltern, Nachbarn und Kollegen nach ihren Scheinen.", size=15, top=10) +
              rewe_bar(b, t) + sp + b.button(REWE_URL, "Scheine zuordnen"), top=GAP_BLOCK),
        prooptik_box(b, t, sp),
        b.box(b.label("@bcerfurt") + b.h3("Wir sind auf TikTok", level=2) +
              b.ptag("Spielszenen, Trainingsmomente und Teamgeist aus Erfurt. Wir stehen kurz vor unseren ersten 100 Followern. "
                     "Folgt dem Kanal und teilt die Videos mit Freunden und Familie, damit noch mehr Kinder in Erfurt Basketball für sich entdecken.", size=15, top=10) +
              sp + b.button("https://www.tiktok.com/@bcerfurt", "@bcerfurt folgen"), top=GAP_BLOCK),

        b.divider(),
        c["mv_hint"],

        c["sig"]("Ihr habt Neuigkeiten aus euren Teams, Fotos oder Ideen für die nächste Ausgabe? Antwortet einfach auf diese E-Mail."),
    ])


def content_frauen(b, t):
    c = parts(b, t)
    sp = c["spacer"]
    s = t["text"]
    return "".join([
        b.row(b.label("Oktober 2026") + b.h1("Neues aus dem #bcerfurt"), top=GAP_SECTION),
        b.p("Liebe Mitglieder, liebe Eltern,", top=GAP_BOX),
        b.p("wir haben gute Nachrichten: Der BC Erfurt bekommt eine neue Trainingsgruppe. Außerdem geht es um den Endspurt "
            "bei REWE, um ein Landesfinale, bei dem wir eure Unterstützung von der Tribüne brauchen, und um die Gesundheitstage bei pro optik."),

        b.box(b.img("2026-10-frauen.jpg", 484, 363, "Basketballerin im weißen Trikot hält den Ball wurfbereit über dem Kopf in einer hellen Sporthalle") + b.label("Neu ab sofort") + b.h3("Basketball für Mädchen und Frauen", level=2) +
              b.ptag("Ab sofort gibt es beim BC Erfurt ein Angebot, das sich speziell an Mädchen ab 16 Jahren und Frauen richtet. "
                     "Dafür haben wir mit <strong>Elena Faytelson</strong> eine neue Trainerin gewonnen.", size=15, top=10) +
              b.ptag("Das Freizeitangebot ist für alle gedacht, die bisher wenig mit Basketball zu tun hatten und sich gern einmal "
                     "ausprobieren möchten. Vorkenntnisse braucht ihr keine.", size=15, top=10) +
              '<div style="height:12px;line-height:12px;font-size:1px;">&nbsp;</div>' +
              b.kv_table([
                  ("Wann", "dienstags<br><span style=\"font-weight:normal;\">19:15 bis 20:30 Uhr</span>"),
                  ("Wo", b.a(DOMSPORTHALLE_MAPS_URL, "Domsporthalle Erfurt", bold=True, color=s)),
                  ("Für", "Mädchen ab 16 Jahren und Frauen"),
                  ("Trainerin", "Elena Faytelson"),
              ], key_w=72) +
              b.ptag("Sagt es gern weiter an Freundinnen, Mütter, Töchter und Kolleginnen. "
                     "Schreibt uns kurz, wenn ihr vorbeikommen möchtet.", size=15, top=12) +
              sp + b.button(FRAUEN_MAIL, "Probetraining anfragen"), top=GAP_BOX),

        b.box(b.label("Endspurt bis 25. Oktober") + b.h3("REWE Scheine für Vereine", level=2) +
              b.ptag("Mehr als die Hälfte ist geschafft. Danke an alle, die schon gesammelt haben. "
                     "Damit wir die <strong>mobile Anzeigetafel</strong> sicher bekommen, brauchen wir weiter eure Unterstützung.", size=15, top=10) +
              b.ptag("Die Ausgabe an der Kasse endete am 11. Oktober, zuordnen könnt ihr eure Scheine aber noch bis zum "
                     "<strong>25. Oktober</strong>. Schaut in Geldbörse, Handschuhfach und Küchenschublade und fragt Großeltern, "
                     "Nachbarn und Kollegen nach ihren Scheinen.", size=15, top=10) +
              rewe_bar(b, t, "die mobile Anzeigetafel") + sp + b.button(REWE_URL, "Scheine zuordnen"), top=GAP_BLOCK),

        b.box(b.img("2026-10-ue40.jpg", 484, 363, "Die Ü40 des BC Erfurt in schwarzen Erfurt-Trikots als Teamfoto unter dem Basketballkorb in der Halle") +
              b.label("Samstag, 21. November") + b.h3("Unsere Ü40 im Landesfinale", level=2) +
              b.ptag("Unsere Ü40 spielt als Spielgemeinschaft <strong>SG BC Erfurt / BBC Mühlhausen</strong> im Landesfinale "
                     "und trifft im Halbfinale auf Culture City Weimar. Kommt vorbei und feuert unser Team an.", size=15, top=10) +
              '<div style="height:12px;line-height:12px;font-size:1px;">&nbsp;</div>' +
              b.kv_table([
                  ("14:00", "Halbfinale 1<br><span style=\"font-weight:normal;\">SG BC Erfurt / BBC Mühlhausen gegen Culture City Weimar</span>"),
                  ("16:00", "Halbfinale 2<br><span style=\"font-weight:normal;\">Science City Jena e.V. gegen USV Erfurt</span>"),
                  ("18:00", "Finale"),
              ], key_w=64, key_strong=True) +
              b.ptag("<strong>Ort:</strong> " + b.a(UE40_MAPS_URL, "Fit-In, Osterlange 13, 99189 Elxleben") +
                     ". Für Catering und ausreichend Sitzplätze ist gesorgt.", size=15, top=12) +
              sp + b.button(UE40_CAL_URL, "Im Kalender eintragen") +
              ("" if b.mode == "gmail" or not WEB_PAGES else b.ptag("Apple Kalender oder Outlook? " + b.a(UE40_ICS_URL, "Termin als Datei laden (.ics)"), size=13, color=t["muted"], top=10)),
              top=GAP_BLOCK),

        prooptik_box(b, t, sp, label="Erinnerung · Termin bis Anfang November buchen",
                     hint="Damit pro optik das Personal planen kann, bucht euren Termin bitte möglichst <strong>bis Anfang November</strong>. "
                          "Spätere Buchungen sind natürlich trotzdem möglich."),

        b.divider(),
        c["mv_hint"],

        c["sig"]("Ihr habt Neuigkeiten aus euren Teams, Fotos oder Ideen für die nächste Ausgabe? Antwortet einfach auf diese E-Mail."),
    ])


CONTENT = {"einladung": content_einladung, "news": content_news, "frauen": content_frauen}


def build(key, issue, mode="send"):
    """mode: send (Gmail-Versand, Bilder von bcerfurt.de), web (Browser-Version auf bcerfurt.de), preview (Bilder eingebettet),
    gmail (Kopiervorlage ohne gehostete Dateien: Logo als Schriftzug, Fotos werden in Gmail eingefuegt)."""
    CUR.clear(); CUR.update(ISSUES[issue])
    t = THEMES[key]
    b = B(t, mode)
    logo = b.asset("bce-logo-header.png", "image/png")
    logo_html = (f'<span style="font-family:{HEAD};font-size:24px;line-height:28px;text-transform:uppercase;color:#FFFFFF;">'
                 f'Basketball <span style="color:{RED};">Club</span> Erfurt</span>' if mode == "gmail" else
                 f'<img src="{logo}" width="220" height="42" alt="Basketball Club Erfurt" style="display:block;width:220px;max-width:100%;height:auto;border:0;font-family:{HEAD};font-size:16px;line-height:20px;color:#FFFFFF;">')
    fl = lambda href, label: b.a(href, label, color="#BDBDBD")
    filler = "&#8199;&#65279;&#847; " * 60  # verhindert, dass Gmail nach dem Preheader Fliesstext anzeigt

    view_link = "" if mode in ("web", "gmail") or not WEB_PAGES else (
        f'<tr><td align="right" style="padding:0 {PX}px 10px {PX}px;font-family:{BODY};font-size:12px;line-height:16px;color:{t["muted"]};">'
        f'{b.a(web_url(issue), "Im Browser ansehen", color=t["muted"])}</td></tr>')

    return _esc_amp(f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="{t['scheme']}">
<meta name="supported-color-schemes" content="{t['scheme']}">
<title>{CUR["subject"]}</title>
</head>
<body style="margin:0;padding:0;background:{t['outer']};">
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;">{CUR["preheader"]}{filler}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{t['outer']}" style="background:{t['outer']};">
<tr><td align="center" style="padding:16px 0 32px 0;">
<!--[if mso]><table role="presentation" align="center" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
<table role="presentation" align="center" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
{view_link}
<tr><td height="6" bgcolor="{t['stripe']}" style="height:6px;font-size:1px;line-height:1px;background:{t['stripe']};">&nbsp;</td></tr>
<tr><td bgcolor="{DARK}" style="background:{DARK};padding:22px {PX}px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td valign="middle"><a href="{utm(SITE)}" target="_blank" style="text-decoration:none;">{logo_html}</a></td>
    <td valign="middle" align="right" width="90" style="font-family:{BODY};font-size:11px;line-height:14px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:#A3A3A3;">Ehrlich.<br>Sportlich.<br>Cool.</td>
  </tr></table>
</td></tr>
<tr><td bgcolor="{t['card']}" style="background:{t['card']};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{CONTENT[issue](b, t)}
</table>
</td></tr>
<tr><td bgcolor="{DARK}" style="background:{DARK};padding:28px {PX}px;font-family:{BODY};font-size:12px;line-height:18px;color:#BDBDBD;">
  <p style="margin:0 0 10px 0;font-family:{HEAD};font-size:18px;line-height:22px;text-transform:uppercase;color:#FFFFFF;">Basketball Club Erfurt e.V.</p>
  <p style="margin:0 0 12px 0;font-family:{BODY};font-size:12px;line-height:18px;color:#BDBDBD;">{fl(utm(SITE), "bcerfurt.de")} &nbsp;·&nbsp; {fl("https://www.instagram.com/bcerfurt/", "Instagram")} &nbsp;·&nbsp; {fl("https://www.tiktok.com/@bcerfurt", "TikTok")} &nbsp;·&nbsp; {fl("mailto:" + SENDER, SENDER)}</p>
  <p style="margin:0 0 12px 0;font-family:{BODY};font-size:12px;line-height:18px;color:#BDBDBD;">Ihr bekommt diese E-Mail, weil ihr Mitglied im BC Erfurt seid oder euer Kind bei uns spielt. {fl(UNSUB, "Vereinsnews abbestellen")}</p>
  <p style="margin:0;font-family:{BODY};font-size:12px;line-height:18px;color:#BDBDBD;">Basketball Club Erfurt e.V. · Leipziger Straße 71 · 99085 Erfurt<br>{fl(SITE + "/impressum", "Impressum")} &nbsp;·&nbsp; {fl(SITE + "/datenschutz", "Datenschutz")}</p>
</td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr>
</table>
</body>
</html>
""")


def _typo(txt):
    import re
    months = "Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"
    txt = re.sub(rf"(\d{{1,2}}\.) ({months})", r"\1&nbsp;\2", txt)
    txt = re.sub(r"(\d{5}) ([A-ZÄÖÜ][a-zäöüß]+)", r"\1&nbsp;\2", txt)
    txt = re.sub(r"\b([12]\.) (Vorsitz)", r"\1&nbsp;\2", txt)
    txt = re.sub(r"(\d) (€|%|Uhr|Jahren)", r"\1&nbsp;\2", txt)
    txt = txt.replace("Seminarraum 129", "Seminarraum&nbsp;129").replace("E-Mail", "E&#8209;Mail")
    return txt


def _esc_amp(h):
    import re
    h = re.sub(r">([^<]+)<", lambda m: ">" + _typo(m.group(1)) + "<", h)
    return re.sub(r'href="([^"]*)"', lambda m: 'href="' + m.group(1).replace("&amp;", "&").replace("&", "&amp;") + '"', h)


def ics(uid, start, end, summary, location, description):
    esc = lambda s: s.replace(",", "\\,").replace(";", "\\;")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Basketball Club Erfurt e.V.//Vereinsnews//DE",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "BEGIN:VEVENT", f"UID:{uid}", "DTSTAMP:20261013T080000Z",
             f"DTSTART:{start}", f"DTEND:{end}", f"SUMMARY:{esc(summary)}", f"LOCATION:{esc(location)}",
             f"DESCRIPTION:{esc(description)}", f"ORGANIZER;CN=Basketball Club Erfurt e.V.:mailto:{SENDER}",
             "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


ICS_FILES = {
    "mitgliederversammlung-2026.ics": ics(
        "mv-2026@bcerfurt.de", "20261205T090000Z", "20261205T110000Z", "Mitgliederversammlung BC Erfurt",
        "Landessportbund Thüringen, Seminarraum 129, Werner-Seelenbinder-Straße 1, 99096 Erfurt",
        "Mitgliederversammlung 2026 des Basketball Club Erfurt e.V. mit Vorstandswahlen."),
    "ue40-landesfinale-2026.ics": ics(
        "ue40-landesfinale-2026@bcerfurt.de", "20261121T130000Z", "20261121T183000Z", "Ü40-Landesfinale mit dem BC Erfurt",
        UE40_ORT, "14:00 Halbfinale SG BC Erfurt / BBC Mühlhausen gegen Culture City Weimar. "
                  "16:00 Halbfinale Science City Jena gegen USV Erfurt. 18:00 Finale."),
}

if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "out")
    only = sys.argv[2:] or list(ISSUES)
    key = "B"   # festgelegt: Hallenlicht
    up = out / "upload" / "newsletter"
    for d in (out / "versand", out / "vorschau", up):
        d.mkdir(parents=True, exist_ok=True)
    for issue in only:
        meta = ISSUES[issue]
        (out / "versand" / f"{meta['file']}.html").write_text(build(key, issue, "send"), encoding="utf-8")
        (out / "vorschau" / f"{meta['file']}_Vorschau.html").write_text(build(key, issue, "preview"), encoding="utf-8")
        (up / f"{meta['slug']}.html").write_text(build(key, issue, "web"), encoding="utf-8")
        (out / "versand" / f"{meta['file']}_Gmail-Kopiervorlage.html").write_text(build(key, issue, "gmail"), encoding="utf-8")
        for asset in meta["assets"]:
            (up / asset).write_bytes((HERE / asset).read_bytes())
    for name, data in ICS_FILES.items():
        (up / name).write_bytes(data)
    print("ok", out, only)
