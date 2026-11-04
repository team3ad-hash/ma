# -*- coding: utf-8 -*-
"""Builds the campaign brief (xlsx) and Google Ads Editor CSV files for the
Search campaigns promoting the two armed-guard jobs in the Negev (Team 3).

Run:  python build.py   (writes into ./output)
"""
import csv
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
EDITOR = os.path.join(OUT, "editor-csv")
os.makedirs(EDITOR, exist_ok=True)

# ---------------------------------------------------------------- URLs
URL_SODA = ("https://www.team3.co.il/jobs/%d7%9e%d7%90%d7%91%d7%98%d7%97-%d7%a2%d7%9d-%d7%a0%d7%a9%d7%a7/"
            "%d7%9c%d7%a1%d7%95%d7%93%d7%94-%d7%a1%d7%98%d7%a8%d7%99%d7%9d-%d7%a2%d7%99%d7%93%d7%9f-"
            "%d7%94%d7%a0%d7%92%d7%91-%d7%93%d7%a8%d7%95%d7%a9%d7%99%d7%9d-%d7%95%d7%aa-%d7%9e%d7%90"
            "%d7%91%d7%98%d7%97%d7%99/")
URL_ADAMA = ("https://www.team3.co.il/jobs/security/%d7%94%d7%a6%d7%98%d7%a8%d7%a4%d7%95-%d7%9c%d7%a6"
             "%d7%95%d7%95%d7%aa-%d7%94%d7%97%d7%9e%d7%95%d7%a9%d7%99%d7%9d-%d7%97%d7%9e%d7%95%d7%a9"
             "%d7%95%d7%aa-%d7%a9%d7%9c-%d7%90%d7%93%d7%9e%d7%94-%d7%9e%d7%9b/")
URL_ARMED_CAT = "https://www.team3.co.il/jobs/%d7%9e%d7%90%d7%91%d7%98%d7%97-%d7%a2%d7%9d-%d7%a0%d7%a9%d7%a7/"
URL_SECURITY_CAT = "https://www.team3.co.il/jobs/security/"

URL_SUFFIX = ("utm_source=google&utm_medium=cpc&utm_campaign={campaignid}"
              "&utm_content={adgroupid}&utm_term={keyword}")

# ---------------------------------------------------------------- campaigns
C1 = "SRC | אבטחה נגב | High Intent"
C2 = "SRC | דרושים נגב | Geo Broad"

CAMPAIGNS = [
    # name, daily budget ILS, max CPC limit ILS, role
    (C1, 80, 6.0, "ביטויי כוונה גבוהה: מאבטחים, אבטחה, עבודה מועדפת, מיקומי המשרות"),
    (C2, 25, 3.0, "ביטויי עבודה גיאוגרפיים רחבים (דרושים באר שבע / רהט / להבים…) — תקציב מוגבל, CPC נמוך"),
]

# ---------------------------------------------------------------- ad groups & keywords
# volumes: Ahrefs, Israel, monthly (None = no data / too low)
AD_GROUPS = [
    {
        "campaign": C1, "name": "מאבטחים חמושים - כללי", "url": URL_SODA, "cpc": 6.0,
        "path": ("משרות", "מאבטחים-חמושים"), "job": "124651 סודה סטרים",
        "keywords": [
            ("מאבטח חמוש", "Exact", 100), ("מאבטח חמוש", "Phrase", 100),
            ("דרושים מאבטחים", "Exact", 200), ("דרושים מאבטחים", "Phrase", 200),
            ("מאבטחים חמושים", "Phrase", None), ("דרושים מאבטחים חמושים", "Phrase", 10),
            ("עבודה באבטחה", "Exact", 90), ("עבודה באבטחה", "Phrase", 90),
            ("עבודה כמאבטח", "Phrase", None), ("משרת מאבטח", "Phrase", None),
            ("דרוש מאבטח", "Phrase", None), ("מאבטח במפעל", "Phrase", None),
            ("אבטחת מפעלים", "Phrase", None), ("עבודה באבטחה בדרום", "Phrase", None),
        ],
    },
    {
        "campaign": C1, "name": "מאבטחים באר שבע ונאות חובב", "url": URL_ADAMA, "cpc": 6.0,
        "path": ("משרות", "באר-שבע"), "job": "124655 אדמה מכתשים",
        "keywords": [
            ("דרושים מאבטחים באר שבע", "Exact", 40), ("דרושים מאבטחים באר שבע", "Phrase", 40),
            ("מאבטחים באר שבע", "Phrase", None), ("מאבטח באר שבע", "Phrase", None),
            ("מאבטח חמוש באר שבע", "Phrase", None), ("עבודה באבטחה באר שבע", "Phrase", None),
            ("מאבטח נאות חובב", "Phrase", None), ("עבודה בנאות חובב", "Phrase", None),
            ("דרושים נאות חובב", "Phrase", None),
        ],
    },
    {
        "campaign": C1, "name": "מאבטחים עידן הנגב", "url": URL_SODA, "cpc": 6.0,
        "path": ("משרות", "עידן-הנגב"), "job": "124651 סודה סטרים",
        "keywords": [
            ("עבודה בעידן הנגב", "Phrase", None), ("דרושים עידן הנגב", "Phrase", None),
            ("מאבטח עידן הנגב", "Phrase", None), ("דרושים מאבטחים רהט", "Phrase", None),
            ("מאבטח רהט", "Phrase", None), ("מאבטח להבים", "Phrase", None),
        ],
    },
    {
        "campaign": C1, "name": "עבודה מועדפת", "url": URL_SODA, "cpc": 5.0,
        "path": ("עבודה-מועדפת", "אבטחה"), "job": "124651 סודה סטרים",
        "keywords": [
            ("עבודה מועדפת", "Exact", 1400), ("עבודה מועדפת", "Phrase", 1400),
            ("עבודה מועדפת לחיילים משוחררים", "Phrase", 450),
            ("עבודה מועדפת באר שבע", "Phrase", 60), ("עבודה מועדפת אבטחה", "Phrase", 20),
            ("עבודה מועדפת באבטחה", "Phrase", None), ("עבודה מועדפת בדרום", "Phrase", None),
            ("עבודה מועדפת מאבטח", "Phrase", None), ("משרות עבודה מועדפת", "Phrase", None),
            ("עבודה מועדפת עם הסעות", "Phrase", None),
        ],
    },
    {
        "campaign": C2, "name": "דרושים באר שבע", "url": URL_ADAMA, "cpc": 3.0,
        "path": ("משרות", "באר-שבע"), "job": "124655 אדמה מכתשים",
        "keywords": [
            ("דרושים באר שבע", "Phrase", 2100), ("עבודה בבאר שבע", "Phrase", 600),
            ("משרות באר שבע", "Phrase", None), ("עבודה במשמרות באר שבע", "Phrase", None),
            ("עבודה עם הסעות באר שבע", "Phrase", None),
        ],
    },
    {
        "campaign": C2, "name": "דרושים רהט להבים ודרום", "url": URL_SODA, "cpc": 3.0,
        "path": ("משרות", "נגב"), "job": "124651 סודה סטרים",
        "keywords": [
            ("דרושים רהט", "Phrase", 70), ("עבודה ברהט", "Phrase", None),
            ("דרושים להבים", "Phrase", 40), ("דרושים עומר", "Phrase", None),
            ("עבודה בעומר", "Phrase", None), ("דרושים אופקים", "Phrase", None),
            ("דרושים דימונה", "Phrase", None), ("עבודה בדרום", "Phrase", 100),
            ("דרושים בדרום", "Phrase", None),
        ],
    },
]

# ---------------------------------------------------------------- negatives (phrase)
NEG_COMMON = [
    # learning / licensing / info
    "קורס", "קורסים", "הסמכה", "רישיון נשק", "רשיון נשק", "רישיון לנשק", "מבחן", "מבחנים",
    "שכר מאבטח", "משכורת מאבטח", "כמה מרוויח", "כמה משתכר", "טבלת שכר", "זכויות", "תלוש",
    "פיצויים", "חוק", "ויקיפדיה", "pdf", "מה זה",
    # wrong candidate profile
    "סטודנט", "סטודנטים", "משרה חלקית", "חצי משרה", "מהבית", "אונליין", "נוער", "בני נוער",
    "תיכוניסטים", "שירות לאומי", "ללא צבא", "פטור משירות",
    # B2B / products (not job seekers)
    "חברת אבטחה", "חברות אבטחה", "שירותי אבטחה", "מצלמות אבטחה", "מערכת אבטחה", "מערכות אבטחה",
    "אזעקה", "אבטחת מידע", "סייבר", "נשק למכירה", "אקדח", "מיגון",
    # other security bodies
    "משטרה", "שב\"כ", "מג\"ב", "בודק ביטחוני", "מאבטח אישי",
    # far away cities
    "תל אביב", "ירושלים", "חיפה", "אשדוד", "אשקלון", "אילת", "נתניה", "ראשון לציון",
    "פתח תקווה", "צפון", "מרכז",
]
NEG_C1_EXTRA = [  # informational "preferred work" traffic
    "מענק", "פיקדון", "כמה זמן", "חודשים", "טופס", "אישור", "רשימת", "משרד הביטחון",
    "קרן", "מלונאות", "מלון", "חקלאות", "בניין",
]
NEG_C2_EXTRA = [  # funnel security / preferred-work intent into campaign 1
    "מאבטח", "מאבטחים", "אבטחה", "מועדפת",
    "מלצר", "מלצרית", "ניקיון", "נהג", "נהגים", "מזכירה", "קופאית", "גננת", "סייעת", "אחות",
    "רופא", "מורה", "עורך דין", "רואה חשבון", "הנדסאי", "מהנדס", "מתכנת",
]

# ---------------------------------------------------------------- RSA copy
H_COMMON = [
    "דרושים/ות מאבטחים/ות חמושים",
    "עבודה מועדפת באבטחה",
    "ארוחות והסעות למקום העבודה",
    "משמרות מגוונות 24/7",
    "אפשרויות קידום והתפתחות",
    "הגישו מועמדות תוך דקה",
    "צוות 3 מגייסת עכשיו",
    "מתאים לחיילים משוחררים",
]
H_SODA = [
    "תנאים מעולים למאבטחים/ות",
    "תנאים סוציאליים מהיום הראשון",
    "הכשרה של יום אחד בלבד",
]
H_ADAMA = [
    "ארוחות חמות בכל משמרת",
    "קורס נשק קצר של 9 שעות",
    "מאבטחים למפעל בנאות חובב",
]

D_SODA = [
    "דרושים/ות מאבטחים/ות חמושים/ות למפעל מוביל בעידן הנגב. עבודה מועדפת! הגישו עכשיו",
    "תנאים סוציאליים מלאים מהיום הראשון, ארוחות והסעות. הכשרה של יום אחד בלבד.",
    "דרישות: שירות צבאי מלא, פרופיל 02 ומעלה ורישיון נהיגה. משמרות מגוונות 24/7.",
    "מחפשים עבודה מועדפת בדרום? הצטרפו לצוות האבטחה. השאירו פרטים ונחזור אליכם.",
]
D_ADAMA = [
    "דרושים/ות מאבטחים/ות חמושים/ות למפעל מוביל בנאות חובב, ליד באר שבע. עבודה מועדפת!",
    "ארוחות חמות במשמרת, הסעות ואפשרויות קידום. קורס נשק קצר של 9 שעות לפני תחילת העבודה",
    "דרישות: שירות צבאי מלא ורישיון נהיגה. סיורים ובקרת כניסה במשמרות 24/7.",
    "מחפשים עבודה מועדפת באזור באר שבע? השאירו פרטים בטופס הקצר ונחזור אליכם.",
]

AG_HEADLINES = {
    "מאבטחים חמושים - כללי": ["מאבטחים חמושים בנגב", "עבודה באבטחה בדרום", "מאבטח/ת חמוש/ה - הגישו עכשיו", "משרת מאבטח עם תנאים מעולים"],
    "מאבטחים באר שבע ונאות חובב": ["דרושים מאבטחים בבאר שבע", "מאבטחים/ות לנאות חובב", "עבודה באבטחה ליד באר שבע", "מאבטח חמוש באזור באר שבע"],
    "מאבטחים עידן הנגב": ["מאבטחים/ות לעידן הנגב", "דרושים מאבטחים ליד רהט", "עבודה באבטחה בעידן הנגב", "מאבטח חמוש בפארק עידן הנגב"],
    "עבודה מועדפת": ["עבודה מועדפת בדרום", "עבודה מועדפת לחיילים משוחררים", "עבודה מועדפת עם הסעות", "עבודה מועדפת בנגב"],
    "דרושים באר שבע": ["דרושים/ות בבאר שבע", "עבודה בבאר שבע עם הסעות", "משרות חמות בבאר שבע", "עבודה במשמרות בבאר שבע"],
    "דרושים רהט להבים ודרום": ["דרושים/ות ברהט ובלהבים", "עבודה בדרום עם הסעות", "משרות חמות בנגב", "עבודה ליד רהט ולהבים"],
}


def rsa_for(ag):
    soda = ag["url"] == URL_SODA
    heads = AG_HEADLINES[ag["name"]] + H_COMMON + (H_SODA if soda else H_ADAMA)
    descs = D_SODA if soda else D_ADAMA
    return heads[:15], descs


# ---------------------------------------------------------------- assets
SITELINKS = [
    ("מאבטחים לעידן הנגב", "תנאים סוציאליים מהיום הראשון", "הכשרה של יום אחד בלבד", URL_SODA),
    ("מאבטחים לנאות חובב", "ארוחות חמות והסעות", "משמרות 24/7 ואפשרויות קידום", URL_ADAMA),
    ("כל משרות המאבטח החמוש", "משרות מאבטח/ת חמוש/ה", "בכל רחבי הארץ", URL_ARMED_CAT),
    ("כל משרות האבטחה", "מאבטחים, סיירים ובקרים", "הגישו מועמדות אונליין", URL_SECURITY_CAT),
]
CALLOUTS = [
    "עבודה מועדפת", "ארוחות במשמרת", "הסעות למקום העבודה", "תנאים מהיום הראשון",
    "הכשרה קצרה", "משמרות 24/7", "אפשרויות קידום",
]
SNIPPET = ("Types", ["מאבטח/ת חמוש/ה", "סיור במתקן", "בקרת כניסה", "משמרות 24/7"])

# ---------------------------------------------------------------- validation
LIMITS = {"headline": 30, "description": 90, "path": 15, "sitelink": 25, "sl_desc": 35,
          "callout": 25, "snippet": 25}


def check(text, kind, where):
    if len(text) > LIMITS[kind]:
        sys.exit(f"TOO LONG ({len(text)}>{LIMITS[kind]}) {kind} @ {where}: {text}")


for ag in AD_GROUPS:
    h, d = rsa_for(ag)
    assert len(h) == 15 and len(set(h)) == 15, ag["name"]
    for t in h:
        check(t, "headline", ag["name"])
    for t in d:
        check(t, "description", ag["name"])
    for p in ag["path"]:
        check(p, "path", ag["name"])
for s in SITELINKS:
    check(s[0], "sitelink", s[0]); check(s[1], "sl_desc", s[0]); check(s[2], "sl_desc", s[0])
for c in CALLOUTS:
    check(c, "callout", c)
for v in SNIPPET[1]:
    check(v, "snippet", v)

# ---------------------------------------------------------------- Editor CSVs


def write_csv(name, header, rows):
    path = os.path.join(EDITOR, name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


write_csv("01_campaigns.csv",
          ["Campaign", "Campaign Type", "Networks", "Budget", "Budget type", "Bid Strategy Type",
           "Languages", "Final URL suffix", "Campaign Status"],
          [[c, "Search", "Google search", b, "Daily", "Maximize clicks", "he;en;ar", URL_SUFFIX, "Paused"]
           for c, b, _, _ in CAMPAIGNS])

write_csv("02_ad_groups.csv",
          ["Campaign", "Ad Group", "Max CPC", "Ad Group Type", "Ad Group Status"],
          [[ag["campaign"], ag["name"], f'{ag["cpc"]:.2f}', "Standard", "Enabled"] for ag in AD_GROUPS])

write_csv("03_keywords.csv",
          ["Campaign", "Ad Group", "Keyword", "Criterion Type", "Final URL", "Status"],
          [[ag["campaign"], ag["name"], kw, mt, "", "Enabled"]
           for ag in AD_GROUPS for kw, mt, _ in ag["keywords"]])

neg_rows = []
for camp, extra in ((C1, NEG_C1_EXTRA), (C2, NEG_C2_EXTRA)):
    for kw in NEG_COMMON + extra:
        neg_rows.append([camp, "", kw, "Negative Phrase"])
write_csv("04_campaign_negative_keywords.csv", ["Campaign", "Ad Group", "Keyword", "Criterion Type"], neg_rows)

rsa_header = (["Campaign", "Ad Group", "Ad type"] + [f"Headline {i}" for i in range(1, 16)]
              + [f"Description {i}" for i in range(1, 5)] + ["Path 1", "Path 2", "Final URL", "Status"])
rsa_rows = []
for ag in AD_GROUPS:
    h, d = rsa_for(ag)
    rsa_rows.append([ag["campaign"], ag["name"], "Responsive search ad"] + h + d
                    + list(ag["path"]) + [ag["url"], "Enabled"])
write_csv("05_responsive_search_ads.csv", rsa_header, rsa_rows)

write_csv("06_sitelinks.csv",
          ["Campaign", "Link Text", "Description Line 1", "Description Line 2", "Final URL"],
          [[c, *s] for c, *_ in CAMPAIGNS for s in SITELINKS])
write_csv("07_callouts.csv", ["Campaign", "Callout text"],
          [[c, t] for c, *_ in CAMPAIGNS for t in CALLOUTS])
write_csv("08_structured_snippets.csv", ["Campaign", "Header", "Values"],
          [[c, SNIPPET[0], ";".join(SNIPPET[1])] for c, *_ in CAMPAIGNS])

# ---------------------------------------------------------------- Brief xlsx
F = "Arial"
H_FILL = PatternFill("solid", fgColor="1F3864")
SEC_FILL = PatternFill("solid", fgColor="D9E1F2")
TODO_FILL = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top", horizontal="right")

wb = Workbook()


def sheet(title, header, rows, widths, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = title
    ws.sheet_view.rightToLeft = True
    ws.append(header)
    for c in ws[1]:
        c.font = Font(name=F, bold=True, color="FFFFFF")
        c.fill = H_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="right")
        c.border = BORDER
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=F)
            c.alignment = WRAP
            c.border = BORDER
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    return ws


def mark_section(ws, col_count):
    for row in ws.iter_rows(min_row=2):
        if row[0].value and all(c.value in (None, "") for c in row[1:col_count]):
            for c in row[:col_count]:
                c.fill = SEC_FILL
                c.font = Font(name=F, bold=True)


# 1. Overview
total_budget = sum(b for _, b, _, _ in CAMPAIGNS)
overview = [
    ["מטרה", ""],
    ["יעד עסקי", "גיוס מאבטחים/ות חמושים/ות לשתי משרות בנגב: #124651 (סודה סטרים, עידן הנגב) ו-#124655 (אדמה מכתשים, נאות חובב / באר שבע)"],
    ["המרה ראשית", "שליחת טופס מועמדות בעמוד המשרה (Primary)"],
    ["המרות משניות", "קליק וואטסאפ, קליק טלפון (Secondary — לא נכנסות לאופטימיזציה)"],
    ["KPI מרכזי", "עלות לליד מתאים (Cost per Qualified Lead) — לפי סינון הגיוס, לא לפי כמות טפסים"],
    ["KPI משניים", "CTR ≥ 8% בקבוצות High Intent · CVR עמוד ≥ 10% · Search Impression Share ≥ 60% בביטויי מאבטחים"],
    ["מבנה", ""],
    ["סוג קמפיין", "Search בלבד (Google Search, ללא Search Partners וללא Display Expansion)"],
    ["קמפיינים", f"2 קמפיינים: '{C1}' (כוונה גבוהה) + '{C2}' (גיאוגרפי רחב, תקציב מוגבל)"],
    ["קבוצות מודעות", f"{len(AD_GROUPS)} קבוצות, {sum(len(a['keywords']) for a in AD_GROUPS)} מילות מפתח (Exact + Phrase, ללא Broad בשלב ההשקה)"],
    ["תקציב", ""],
    ["תקציב יומי כולל", f"₪{total_budget} ליום (≈ ₪{total_budget * 30.4:,.0f} לחודש)"],
    [C1, f"₪{CAMPAIGNS[0][1]} ליום · Max CPC limit ₪{CAMPAIGNS[0][2]:.0f}"],
    [C2, f"₪{CAMPAIGNS[1][1]} ליום · Max CPC limit ₪{CAMPAIGNS[1][2]:.0f}"],
    ["אסטרטגיית הצעות מחיר", ""],
    ["שלב 1 (ימים 1–14)", "Maximize Clicks עם תקרת CPC — איסוף נתונים והמרות ראשונות"],
    ["שלב 2 (≥15 המרות טופס ב-30 יום)", "מעבר ל-Maximize Conversions (המרה ראשית בלבד)"],
    ["שלב 3 (≥30 המרות ב-30 יום)", "הגדרת tCPA לפי עלות לליד בפועל + 10–15%; שינויי יעד בצעדים של 10–15% בלבד"],
    ["טרגוט", ""],
    ["מיקום", "רדיוס 35 ק\"מ סביב באר שבע (מכסה נאות חובב, עידן הנגב, רהט, להבים, עומר, אופקים, דימונה, ירוחם). אפשרות: 'Presence — אנשים שנמצאים במיקום' (לא 'או מתעניינים')"],
    ["שפות", "עברית + אנגלית + ערבית (חלק גדול מהמכשירים בישראל מוגדרים באנגלית; קהל בפזורה ורהט)"],
    ["מכשירים", "כל המכשירים; צפי ל-85%+ מובייל — לוודא שהטופס בעמוד נוח למובייל"],
    ["תזמון", "24/7 בשבועיים הראשונים; לאחר מכן לבחון התאמת הצעות לפי שעות (מינימום נפח)"],
    ["קהלים (Observation)", "להוסיף במצב Observation בלבד: In-market 'Jobs & Education > Jobs', Remarketing של מבקרי /jobs/ באתר — ללא צמצום טרגוט"],
    ["רגולציה וזהירות", ""],
    ["שכר", "לא מפרסמים שכר במודעות (לא סכום ולא 'שכר גבוה') — לפי הנחיית הלקוח"],
    ["שוויון הזדמנויות", "נוסח ניטרלי מגדרית (מאבטחים/ות) כנדרש בחוק שוויון ההזדמנויות בעבודה; לא לצמצם לפי גיל או מגדר"],
    ["סימני מסחר", "לא משתמשים בשמות המעסיקים (סודה סטרים / אדמה) — לא במילות המפתח ולא בטקסט המודעה — לפי הנחיית הלקוח"],
    ["EU political ads", "בזמן ה-Post ב-Editor לסמן: 'No, this campaign does not have EU political ads'"],
]
ws = sheet("סקירה", ["נושא", "פירוט"], overview, [34, 120], first=True)
mark_section(ws, 2)

# 2. Structure
struct = []
for c, b, cpc, role in CAMPAIGNS:
    struct.append([c, "", f"₪{b}/יום", f"₪{cpc:.0f}", role, "", ""])
    for ag in [a for a in AD_GROUPS if a["campaign"] == c]:
        struct.append(["", ag["name"], "", f"₪{ag['cpc']:.0f}", ag["job"], "/".join(ag["path"]), ag["url"]])
ws = sheet("מבנה", ["קמפיין", "קבוצת מודעות", "תקציב", "Max CPC", "משרה / תפקיד", "Display path", "Final URL"],
           struct, [30, 28, 12, 10, 50, 26, 70])

# 3. Keywords
kw_rows = []
for ag in AD_GROUPS:
    for kw, mt, vol in ag["keywords"]:
        disp = f"[{kw}]" if mt == "Exact" else f'"{kw}"'
        kw_rows.append([ag["campaign"], ag["name"], kw, mt, disp, vol if vol is not None else "—"])
ws = sheet("מילות מפתח", ["קמפיין", "קבוצת מודעות", "מילת מפתח", "התאמה", "כתיב Editor", "נפח חודשי (Ahrefs IL)"],
           kw_rows, [30, 28, 34, 10, 36, 18])
n = len(kw_rows) + 3
ws.cell(n, 1, "מקור נפחים: Ahrefs Keywords Explorer, ישראל, נובמבר 2026. '—' = אין נתון / נפח נמוך מאוד. "
              "נפחים של Exact ו-Phrase לאותו ביטוי זהים (נפח הביטוי עצמו).").font = Font(name=F, italic=True)

# 4. Negatives
neg = ([["כל הקמפיינים", k, "Phrase", "משותף"] for k in NEG_COMMON]
       + [[C1, k, "Phrase", "תנועה אינפורמטיבית על עבודה מועדפת"] for k in NEG_C1_EXTRA]
       + [[C2, k, "Phrase", "ניתוב כוונת אבטחה לקמפיין 1 / מקצועות לא רלוונטיים"] for k in NEG_C2_EXTRA])
sheet("מילות שליליות", ["רמה", "מילת מפתח שלילית", "התאמה", "סיבה"], neg, [32, 26, 10, 50])

# 5. RSA with live length checks
rsa_sheet_rows = []
for ag in AD_GROUPS:
    h, d = rsa_for(ag)
    for i, t in enumerate(h, 1):
        rsa_sheet_rows.append([ag["campaign"], ag["name"], f"Headline {i}", t, None, 30])
    for i, t in enumerate(d, 1):
        rsa_sheet_rows.append([ag["campaign"], ag["name"], f"Description {i}", t, None, 90])
    for i, t in enumerate(ag["path"], 1):
        rsa_sheet_rows.append([ag["campaign"], ag["name"], f"Path {i}", t, None, 15])
ws = sheet("מודעות RSA", ["קמפיין", "קבוצת מודעות", "שדה", "טקסט", "תווים", "מקסימום", "תקין?"],
           rsa_sheet_rows, [28, 28, 14, 80, 8, 10, 9])
for r in range(2, len(rsa_sheet_rows) + 2):
    ws.cell(r, 5, f"=LEN(D{r})")
    ws.cell(r, 7, f'=IF(E{r}<=F{r},"✔","✘ ארוך")')
    for c in (5, 6, 7):
        ws.cell(r, c).font = Font(name=F)
        ws.cell(r, c).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(r, c).border = BORDER

# 6. Assets
assets = [["Sitelink", s[0], f"{s[1]} | {s[2]}", s[3]] for s in SITELINKS]
assets += [["Callout", c, "", ""] for c in CALLOUTS]
assets += [["Structured snippet", f"Header: {SNIPPET[0]} (סוגים)", " ; ".join(SNIPPET[1]), ""]]
assets += [["Call asset", "להשלים ידנית", "מספר גיוס ישיר (073-…) — *4960 לא נתמך כנכס שיחה. לאשר עם הלקוח איזה מספר מטפל במועמדים", ""],
           ["Lead form asset", "אופציונלי", "טופס לידים בתוך גוגל: שם, טלפון, עיר + שאלות סינון (שירות מלא, פרופיל 02, רישיון). מחייב חיבור CRM / הורדה יומית", ""]]
ws = sheet("נכסים", ["סוג", "טקסט", "תיאור / ערכים", "Final URL"], assets, [20, 30, 70, 60])
for row in ws.iter_rows(min_row=len(assets), max_row=len(assets) + 1):
    for c in row:
        c.fill = TODO_FILL

# 7. Tracking
tracking = [
    ["Form submit – job application", "Primary", "GTM: Trigger על אירוע הצלחת שליחת הטופס (Form submission / thank-you event) בעמודי /jobs/* → Google Ads Conversion + GA4 generate_lead", "חובה לפני השקה"],
    ["WhatsApp click", "Secondary", "GTM: Click URL contains 'wa.me' או 'api.whatsapp.com'", "חובה לפני השקה"],
    ["Phone click", "Secondary", "GTM: Click URL starts with 'tel:'", "חובה לפני השקה"],
    ["Enhanced conversions for leads", "—", "להפעיל ב-Google Ads + להעביר טלפון מגובב (hashed) מהטופס — משפר שיוך ומאפשר בהמשך ייבוא לידים מתאימים", "מומלץ"],
    ["Offline conversion import", "Primary (שלב 2)", "ייבוא 'ליד מתאים' / 'התקבל לעבודה' מה-CRM לפי GCLID או טלפון — האלגוריתם ילמד לייצר מועמדים מתאימים ולא רק טפסים", "מומלץ, אחרי 2–4 שבועות"],
    ["UTM", "—", f"Final URL suffix ברמת קמפיין: {URL_SUFFIX} — לוודא שה-CRM שומר את ה-UTM יחד עם הליד", "כלול ב-CSV"],
    ["Auto-tagging", "—", "לוודא שהוא פעיל בחשבון (GCLID)", "לבדוק"],
]
sheet("מעקב והמרות", ["המרה / רכיב", "סוג", "הגדרה", "סטטוס"], tracking, [30, 16, 100, 24])

# 8. Launch checklist
checklist = [
    ["לפני ייבוא", "לאחד מספר וואטסאפ בעמודי המשרה (כרגע מופיעים 052-2379532, 053-5216650, 053-2237953)", "☐"],
    ["לפני ייבוא", "להשוות את עמוד אדמה לעמוד סודה סטרים (להוסיף 'תנאים מהיום הראשון' אם רלוונטי)", "☐"],
    ["לפני ייבוא", "לבטל את הפופאפ 'כיף שבאתם/ן' לתנועה עם utm_source=google בעמודי המשרה", "☐"],
    ["מעקב", "להגדיר את 3 ההמרות (טאב 'מעקב והמרות') ולבדוק ב-Tag Assistant", "☐"],
    ["ייבוא", "Google Ads Editor → Get recent changes → Account → Import → From file, לפי סדר הקבצים 01→08", "☐"],
    ["ייבוא", "אחרי ייבוא 01: להגדיר ידנית בכל קמפיין — מיקום (רדיוס 35 ק\"מ סביב באר שבע, Presence), תקרת CPC, כיבוי Search Partners + Display", "☐"],
    ["ייבוא", "לבדוק ב-Editor שכל ההמרות הראשיות משויכות לקמפיין (Account-default goals → Submit lead form)", "☐"],
    ["ייבוא", "Check changes → לתקן שגיאות → Post. הקמפיינים מיובאים במצב Paused", "☐"],
    ["השקה", "Preview & diagnosis ל-3 ביטויים מובילים; הפעלת הקמפיינים", "☐"],
    ["ימים 1–7", "Search Terms report כל 3–4 ימים → הוספת שליליות", "☐"],
    ["ימים 7–14", "בדיקת Asset performance; החלפת כותרות 'Low'; בדיקת Impression Share ו-Lost IS (budget/rank)", "☐"],
    ["יום 14+", "מעבר ל-Maximize Conversions אם יש ≥15 המרות טופס; שקילת העברת תקציב מקמפיין 2 לקמפיין 1 לפי עלות לליד", "☐"],
    ["שוטף", "סנכרון שבועי עם הגיוס: כמה מהלידים מתאימים (שירות מלא, פרופיל, רישיון) — זה ה-KPI האמיתי", "☐"],
]
sheet("צ'קליסט השקה", ["שלב", "משימה", "בוצע"], checklist, [16, 120, 8])

# 9. Editor import guide
guide = [
    ["01_campaigns.csv", "2 קמפיינים, Search, תקציב יומי, Maximize clicks, שפות, Final URL suffix. סטטוס Paused", "חובה להגדיר מיקום ידנית — קמפיין בלי מיקום מטורגט לכל העולם"],
    ["02_ad_groups.csv", f"{len(AD_GROUPS)} קבוצות מודעות + Max CPC", ""],
    ["03_keywords.csv", f"{sum(len(a['keywords']) for a in AD_GROUPS)} מילות מפתח, Exact/Phrase", ""],
    ["04_campaign_negative_keywords.csv", f"{len(neg_rows)} שליליות ברמת קמפיין (Negative Phrase)", "אפשר להמיר לרשימה משותפת (Shared library) אחרי הייבוא"],
    ["05_responsive_search_ads.csv", f"{len(AD_GROUPS)} מודעות RSA (15 כותרות + 4 תיאורים לכל אחת)", "ללא Pinning — לתת לגוגל לבדוק קומבינציות"],
    ["06_sitelinks.csv", "4 Sitelinks לכל קמפיין", ""],
    ["07_callouts.csv", "7 Callouts לכל קמפיין", ""],
    ["08_structured_snippets.csv", "Structured snippet (Header: Types)", "אם Editor לא מזהה את הקובץ — להוסיף ידנית (Shared library → Assets)"],
    ["קידוד", "UTF-8 עם BOM (נפתח תקין בעברית גם ב-Excel)", "אם Editor מציג ג'יבריש — לשמור מחדש כ-UTF-16 / להעתיק-להדביק דרך Make multiple changes"],
]
sheet("ייבוא ל-Editor", ["קובץ", "מה בפנים", "הערות"], guide, [36, 70, 70])

brief_path = os.path.join(OUT, "brief-search-security-negev.xlsx")
wb.save(brief_path)
print("OK", brief_path)
