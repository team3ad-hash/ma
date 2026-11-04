# -*- coding: utf-8 -*-
"""Builds the campaign brief (xlsx) and Google Ads Editor CSV files for the
Search campaigns promoting the two armed-guard jobs in the Negev (Team 3).

Structure: one Search campaign per job; every ad in a campaign lands on that
job's page, with UTM parameters in the Final URL.

Run:  python build.py   (writes into ./output)
"""
import csv
import glob
import os
import shutil
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
EDITOR = os.path.join(OUT, "editor-csv")
shutil.rmtree(EDITOR, ignore_errors=True)
os.makedirs(EDITOR, exist_ok=True)

# ---------------------------------------------------------------- job pages
URL_SODA = ("https://www.team3.co.il/jobs/%d7%9e%d7%90%d7%91%d7%98%d7%97-%d7%a2%d7%9d-%d7%a0%d7%a9%d7%a7/"
            "%d7%9c%d7%a1%d7%95%d7%93%d7%94-%d7%a1%d7%98%d7%a8%d7%99%d7%9d-%d7%a2%d7%99%d7%93%d7%9f-"
            "%d7%94%d7%a0%d7%92%d7%91-%d7%93%d7%a8%d7%95%d7%a9%d7%99%d7%9d-%d7%95%d7%aa-%d7%9e%d7%90"
            "%d7%91%d7%98%d7%97%d7%99/")
URL_ADAMA = ("https://www.team3.co.il/jobs/security/%d7%94%d7%a6%d7%98%d7%a8%d7%a4%d7%95-%d7%9c%d7%a6"
             "%d7%95%d7%95%d7%aa-%d7%94%d7%97%d7%9e%d7%95%d7%a9%d7%99%d7%9d-%d7%97%d7%9e%d7%95%d7%a9"
             "%d7%95%d7%aa-%d7%a9%d7%9c-%d7%90%d7%93%d7%9e%d7%94-%d7%9e%d7%9b/")

# utm_term is added dynamically through the campaign-level Final URL suffix
URL_SUFFIX = "utm_term={keyword}"


def final_url(base, utm_campaign, utm_content):
    return (f"{base}?utm_source=google&utm_medium=cpc"
            f"&utm_campaign={utm_campaign}&utm_content={utm_content}")


# ---------------------------------------------------------------- shared copy
GENERIC_KWS = [
    ("מאבטח חמוש", "Exact", 100), ("מאבטח חמוש", "Phrase", 100),
    ("דרושים מאבטחים", "Exact", 200), ("דרושים מאבטחים", "Phrase", 200),
    ("מאבטחים חמושים", "Phrase", None), ("דרושים מאבטחים חמושים", "Phrase", 10),
    ("עבודה באבטחה", "Exact", 90), ("עבודה באבטחה", "Phrase", 90),
    ("עבודה כמאבטח", "Phrase", None), ("משרת מאבטח", "Phrase", None),
    ("דרוש מאבטח", "Phrase", None), ("מאבטח במפעל", "Phrase", None),
    ("אבטחת מפעלים", "Phrase", None), ("עבודה באבטחה בדרום", "Phrase", None),
]
PREFERRED_KWS = [
    ("עבודה מועדפת", "Exact", 1400), ("עבודה מועדפת", "Phrase", 1400),
    ("עבודה מועדפת לחיילים משוחררים", "Phrase", 450),
    ("עבודה מועדפת באר שבע", "Phrase", 60), ("עבודה מועדפת אבטחה", "Phrase", 20),
    ("עבודה מועדפת באבטחה", "Phrase", None), ("עבודה מועדפת בדרום", "Phrase", None),
    ("עבודה מועדפת מאבטח", "Phrase", None), ("משרות עבודה מועדפת", "Phrase", None),
    ("עבודה מועדפת עם הסעות", "Phrase", None),
]

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

# ---------------------------------------------------------------- campaigns
CAMPAIGNS = [
    {
        "name": "סודה סטרים - עידן הנגב 4/11/26",
        "short": "עידן הנגב",
        "job": "#124651 — מאבטחים/ות חמושים/ות, עידן הנגב",
        "budget": 80,
        "url": URL_SODA,
        "utm_campaign": "sodastream-idan-hanegev-4-11-26",
        "geo": "רדיוס 25 ק\"מ סביב פארק התעשייה עידן הנגב (מכסה רהט, להבים, עומר, באר שבע, תל שבע, לקיה, חורה). Presence בלבד",
        "headlines_job": ["תנאים מעולים למאבטחים/ות", "תנאים סוציאליים מהיום הראשון", "הכשרה של יום אחד בלבד"],
        "descriptions": [
            "דרושים/ות מאבטחים/ות חמושים/ות למפעל מוביל בעידן הנגב. עבודה מועדפת! הגישו עכשיו",
            "תנאים סוציאליים מלאים מהיום הראשון, ארוחות והסעות. הכשרה של יום אחד בלבד.",
            "דרישות: שירות צבאי מלא, פרופיל 02 ומעלה ורישיון נהיגה. משמרות מגוונות 24/7.",
            "מחפשים עבודה מועדפת בדרום? הצטרפו לצוות האבטחה. השאירו פרטים ונחזור אליכם.",
        ],
        "campaign_negatives": ["נאות חובב", "דימונה", "ירוחם"],
        "ad_groups": [
            {"name": "מאבטחים חמושים - כללי", "slug": "armed_guard_generic", "cpc": 6.0,
             "path": ("משרות", "מאבטחים-חמושים"), "keywords": GENERIC_KWS,
             "headlines": ["מאבטחים חמושים בנגב", "עבודה באבטחה בדרום",
                           "מאבטח/ת חמוש/ה - הגישו עכשיו", "משרת מאבטח עם תנאים מעולים"]},
            {"name": "מאבטחים עידן הנגב ורהט", "slug": "idan_hanegev_rahat", "cpc": 6.0,
             "path": ("משרות", "עידן-הנגב"),
             "keywords": [("עבודה בעידן הנגב", "Phrase", None), ("דרושים עידן הנגב", "Phrase", None),
                          ("מאבטח עידן הנגב", "Phrase", None), ("דרושים מאבטחים רהט", "Phrase", None),
                          ("מאבטח רהט", "Phrase", None), ("מאבטח להבים", "Phrase", None),
                          ("מאבטח עומר", "Phrase", None)],
             "headlines": ["מאבטחים/ות לעידן הנגב", "דרושים מאבטחים ליד רהט",
                           "עבודה באבטחה בעידן הנגב", "מאבטח חמוש בפארק עידן הנגב"]},
            {"name": "עבודה מועדפת", "slug": "preferred_work", "cpc": 5.0,
             "path": ("עבודה-מועדפת", "אבטחה"), "keywords": PREFERRED_KWS,
             "headlines": ["עבודה מועדפת בדרום", "עבודה מועדפת לחיילים משוחררים",
                           "עבודה מועדפת עם הסעות", "עבודה מועדפת בנגב"]},
            {"name": "דרושים רהט להבים ועומר", "slug": "jobs_rahat_lehavim_omer", "cpc": 3.0,
             "path": ("משרות", "נגב"), "geo_broad": True,
             "keywords": [("דרושים רהט", "Phrase", 70), ("עבודה ברהט", "Phrase", None),
                          ("דרושים להבים", "Phrase", 40), ("דרושים עומר", "Phrase", None),
                          ("עבודה בעומר", "Phrase", None), ("דרושים אופקים", "Phrase", None),
                          ("עבודה בדרום", "Phrase", 100), ("דרושים בדרום", "Phrase", None)],
             "headlines": ["דרושים/ות ברהט ובלהבים", "עבודה בדרום עם הסעות",
                           "משרות חמות בנגב", "עבודה ליד רהט ולהבים"]},
        ],
    },
    {
        "name": "אדמה - מכתשים 4/11/26",
        "short": "נאות חובב",
        "job": "#124655 — מאבטחים/ות חמושים/ות, נאות חובב / באר שבע",
        "budget": 80,
        "url": URL_ADAMA,
        "utm_campaign": "adama-makhteshim-4-11-26",
        "geo": "רדיוס 25 ק\"מ סביב נאות חובב (מכסה באר שבע, עומר, דימונה, ירוחם, שגב שלום, כסייפה). Presence בלבד",
        "headlines_job": ["ארוחות חמות בכל משמרת", "קורס נשק קצר של 9 שעות", "מאבטחים למפעל בנאות חובב"],
        "descriptions": [
            "דרושים/ות מאבטחים/ות חמושים/ות למפעל מוביל בנאות חובב, ליד באר שבע. עבודה מועדפת!",
            "ארוחות חמות במשמרת, הסעות ואפשרויות קידום. קורס נשק קצר של 9 שעות לפני תחילת העבודה",
            "דרישות: שירות צבאי מלא ורישיון נהיגה. סיורים ובקרת כניסה במשמרות 24/7.",
            "מחפשים עבודה מועדפת באזור באר שבע? השאירו פרטים בטופס הקצר ונחזור אליכם.",
        ],
        "campaign_negatives": ["עידן הנגב", "רהט", "להבים"],
        "ad_groups": [
            {"name": "מאבטחים חמושים - כללי", "slug": "armed_guard_generic", "cpc": 6.0,
             "path": ("משרות", "מאבטחים-חמושים"), "keywords": GENERIC_KWS,
             "headlines": ["מאבטחים חמושים ליד באר שבע", "עבודה באבטחה בנגב",
                           "מאבטח/ת חמוש/ה - הגישו עכשיו", "משרת מאבטח עם ארוחות והסעות"]},
            {"name": "מאבטחים באר שבע ונאות חובב", "slug": "beer_sheva_neot_hovav", "cpc": 6.0,
             "path": ("משרות", "באר-שבע"),
             "keywords": [("דרושים מאבטחים באר שבע", "Exact", 40), ("דרושים מאבטחים באר שבע", "Phrase", 40),
                          ("מאבטחים באר שבע", "Phrase", None), ("מאבטח באר שבע", "Phrase", None),
                          ("מאבטח חמוש באר שבע", "Phrase", None), ("עבודה באבטחה באר שבע", "Phrase", None),
                          ("מאבטח נאות חובב", "Phrase", None), ("עבודה בנאות חובב", "Phrase", None),
                          ("דרושים נאות חובב", "Phrase", None)],
             "headlines": ["דרושים מאבטחים בבאר שבע", "מאבטחים/ות לנאות חובב",
                           "עבודה באבטחה ליד באר שבע", "מאבטח חמוש באזור באר שבע"]},
            {"name": "עבודה מועדפת", "slug": "preferred_work", "cpc": 5.0,
             "path": ("עבודה-מועדפת", "אבטחה"), "keywords": PREFERRED_KWS,
             "headlines": ["עבודה מועדפת ליד באר שבע", "עבודה מועדפת לחיילים משוחררים",
                           "עבודה מועדפת עם הסעות", "עבודה מועדפת בנגב"]},
            {"name": "דרושים באר שבע ודימונה", "slug": "jobs_beer_sheva_dimona", "cpc": 3.0,
             "path": ("משרות", "באר-שבע"), "geo_broad": True,
             "keywords": [("דרושים באר שבע", "Phrase", 2100), ("עבודה בבאר שבע", "Phrase", 600),
                          ("משרות באר שבע", "Phrase", None), ("עבודה במשמרות באר שבע", "Phrase", None),
                          ("עבודה עם הסעות באר שבע", "Phrase", None), ("דרושים דימונה", "Phrase", None),
                          ("עבודה בדימונה", "Phrase", None), ("דרושים ירוחם", "Phrase", None)],
             "headlines": ["דרושים/ות בבאר שבע", "עבודה בבאר שבע עם הסעות",
                           "משרות חמות בבאר שבע", "עבודה במשמרות בבאר שבע"]},
        ],
    },
]


# ---------------------------------------------------------------- extra RSA angles
# Google allows max 3 ENABLED RSAs per ad group -> v1, v2, v3 enabled; v4 paused (backup).
ANGLES = {
    "עידן הנגב": [
        ("v2_benefits", "זווית: תנאים והטבות", "Enabled", [
            "תנאים סוציאליים מלאים", "תנאים מהיום הראשון לעבודה", "ארוחות במשמרת על חשבוננו",
            "הסעות מסודרות לעבודה", "קידום והתפתחות בתפקיד", "עבודה יציבה במפעל מוביל",
            "משמרות מגוונות בכל שעות היום", "הכשרה קצרה - יום אחד", "סיורים ובקרת כניסה במפעל",
            "הצטרפו לצוות האבטחה", "השאירו פרטים ונחזור אליכם"], [
            "תנאים סוציאליים מלאים מהיום הראשון, ארוחות במשמרת והסעות. הצטרפו לצוות האבטחה.",
            "עבודה כמאבטח/ת חמוש/ה במפעל מוביל בעידן הנגב: סיורים ובקרת כניסה במשמרות 24/7.",
            "הכשרה של יום אחד בלבד ואפשרויות קידום נרחבות. השאירו פרטים בטופס הקצר.",
            "דרישות: שירות צבאי מלא, פרופיל 02 ומעלה ורישיון נהיגה. עבודה מועדפת!"]),
        ("v3_discharged", "זווית: חיילים משוחררים / עבודה מועדפת", "Enabled", [
            "השתחררתם? יש לנו עבודה", "עבודה מועדפת למשוחררים/ות", "עבודה מועדפת עם תנאים טובים",
            "עבודה מועדפת בנגב עם הסעות", "מתאים לפרופיל 02 ומעלה", "שירות מלא ורישיון נהיגה? בואו",
            "אחרי הצבא - לעבודה באבטחה", "מאבטח/ת חמוש/ה בעידן הנגב", "הכשרה של יום ומתחילים",
            "ארוחות והסעות כלולות", "הגישו מועמדות בקלות"], [
            "השתחררתם? עבודה מועדפת כמאבטחים/ות חמושים/ות במפעל מוביל בעידן הנגב. הגישו עכשיו",
            "מתאים למשוחררים/ות עם שירות צבאי מלא, פרופיל 02 ומעלה ורישיון נהיגה.",
            "הכשרה של יום אחד, ארוחות והסעות ותנאים סוציאליים מלאים מהיום הראשון.",
            "משמרות מגוונות 24/7 ואפשרויות קידום. השאירו פרטים ונחזור אליכם בהקדם."]),
        ("v4_easy_apply", "זווית: הגשה קלה ומהירה (גיבוי)", "Paused", [
            "טופס קצר ופשוט להגשה", "נחזור אליכם בהקדם", "גיוס פעיל למאבטחים/ות",
            "מגייסים מאבטחים/ות לנגב", "הכשרה של יום - ויוצאים לדרך", "אפשר לפנות גם בוואטסאפ",
            "מאבטח/ת חמוש/ה - עידן הנגב", "משמרות 24/7 במפעל מוביל", "תנאים מלאים מהיום הראשון",
            "ארוחות + הסעות לעבודה", "עבודה מועדפת - הגישו היום"], [
            "מגייסים מאבטחים/ות חמושים/ות לעידן הנגב. ממלאים טופס קצר ונחזור אליכם בהקדם.",
            "הכשרה של יום אחד בלבד, תנאים סוציאליים מלאים מהיום הראשון, ארוחות והסעות.",
            "עבודה מועדפת! דרישות: שירות צבאי מלא, פרופיל 02 ומעלה ורישיון נהיגה.",
            "סיורים ובקרת כניסה במשמרות מגוונות 24/7. אפשרויות קידום נרחבות בצוות 3."]),
    ],
    "נאות חובב": [
        ("v2_benefits", "זווית: תנאים והטבות", "Enabled", [
            "ארוחות חמות במשמרת", "הסעות מסודרות לעבודה", "קידום והתפתחות בתפקיד",
            "עבודה יציבה במפעל מוביל", "משמרות מגוונות בכל שעות היום", "קורס נשק קצר - 9 שעות",
            "סיורים ובקרת כניסה במפעל", "הצטרפו לצוות האבטחה", "השאירו פרטים ונחזור אליכם",
            "עבודה ליד באר שבע", "מאבטח/ת חמוש/ה במפעל"], [
            "ארוחות חמות במשמרת, הסעות ואפשרויות קידום. הצטרפו לצוות האבטחה בנאות חובב.",
            "עבודה כמאבטח/ת חמוש/ה במפעל מוביל ליד באר שבע: סיורים ובקרת כניסה במשמרות 24/7.",
            "קורס נשק קצר של 9 שעות לפני תחילת העבודה. השאירו פרטים בטופס הקצר.",
            "דרישות: שירות צבאי מלא ורישיון נהיגה. עבודה מועדפת!"]),
        ("v3_discharged", "זווית: חיילים משוחררים / עבודה מועדפת", "Enabled", [
            "השתחררתם? יש לנו עבודה", "עבודה מועדפת למשוחררים/ות", "עבודה מועדפת עם ארוחות חמות",
            "עבודה מועדפת בנגב עם הסעות", "שירות מלא ורישיון נהיגה? בואו", "אחרי הצבא - לעבודה באבטחה",
            "מאבטח/ת חמוש/ה בנאות חובב", "קורס נשק של 9 שעות בלבד", "ארוחות והסעות כלולות",
            "הגישו מועמדות בקלות", "קידום והתפתחות בתפקיד"], [
            "השתחררתם? עבודה מועדפת כמאבטחים/ות חמושים/ות במפעל מוביל בנאות חובב. הגישו עכשיו",
            "מתאים למשוחררים/ות עם שירות צבאי מלא ורישיון נהיגה. קורס נשק קצר של 9 שעות.",
            "ארוחות חמות במשמרת, הסעות ואפשרויות קידום והתפתחות.",
            "משמרות מגוונות 24/7 ליד באר שבע. השאירו פרטים ונחזור אליכם בהקדם."]),
        ("v4_easy_apply", "זווית: הגשה קלה ומהירה (גיבוי)", "Paused", [
            "טופס קצר ופשוט להגשה", "נחזור אליכם בהקדם", "גיוס פעיל למאבטחים/ות",
            "מגייסים מאבטחים/ות לנגב", "קורס של 9 שעות - ויוצאים לדרך", "אפשר לפנות גם בוואטסאפ",
            "מאבטח/ת חמוש/ה - נאות חובב", "משמרות 24/7 במפעל מוביל", "ארוחות חמות + הסעות",
            "עבודה מועדפת - הגישו היום", "עבודה ליד באר שבע"], [
            "מגייסים מאבטחים/ות חמושים/ות לנאות חובב. ממלאים טופס קצר ונחזור אליכם בהקדם.",
            "קורס נשק קצר של 9 שעות, ארוחות חמות במשמרת, הסעות ואפשרויות קידום.",
            "עבודה מועדפת! דרישות: שירות צבאי מלא ורישיון נהיגה.",
            "סיורים ובקרת כניסה במשמרות מגוונות 24/7. אפשרויות קידום בצוות 3."]),
    ],
}

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
    # informational "preferred work" traffic
    "מענק", "פיקדון", "כמה זמן", "חודשים", "טופס", "אישור", "רשימת", "משרד הביטחון",
    "קרן", "מלונאות", "מלון", "חקלאות", "בניין",
    # unrelated professions (mainly for the geo-broad ad groups)
    "מלצר", "מלצרית", "ניקיון", "נהג", "נהגים", "מזכירה", "קופאית", "גננת", "סייעת", "אחות",
    "רופא", "מורה", "עורך דין", "רואה חשבון", "הנדסאי", "מהנדס", "מתכנת",
]
# ad-group-level negatives on the geo-broad groups: keep security / preferred-work
# queries in the dedicated ad groups of the same campaign
NEG_GEO_BROAD_AG = ["מאבטח", "מאבטחים", "אבטחה", "מועדפת"]

CALLOUTS = [
    "עבודה מועדפת", "ארוחות במשמרת", "הסעות למקום העבודה", "תנאים מהיום הראשון",
    "הכשרה קצרה", "משמרות 24/7", "אפשרויות קידום",
]
CALLOUTS_BY_CAMPAIGN = {
    CAMPAIGNS[0]["name"]: CALLOUTS,
    CAMPAIGNS[1]["name"]: [c for c in CALLOUTS if c != "תנאים מהיום הראשון"] + ["קורס נשק של 9 שעות"],
}
SNIPPET = ("Types", ["מאבטח/ת חמוש/ה", "סיור במתקן", "בקרת כניסה", "משמרות 24/7"])

# ---------------------------------------------------------------- validation
LIMITS = {"headline": 30, "description": 90, "path": 15, "callout": 25, "snippet": 25}


def check(text, kind, where):
    if len(text) > LIMITS[kind]:
        sys.exit(f"TOO LONG ({len(text)}>{LIMITS[kind]}) {kind} @ {where}: {text}")


def _uniq(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def rsa_variants(camp, ag):
    """[(key, label, status, headlines[15], descriptions[4])] for an ad group."""
    fill = H_COMMON + camp["headlines_job"]
    res = [("v1_core", "מודעה מקורית", "Enabled",
            _uniq(ag["headlines"] + fill)[:15], camp["descriptions"])]
    for key, label, status, heads, descs in ANGLES[camp["short"]]:
        res.append((key, label, status, _uniq(ag["headlines"] + heads + fill)[:15], descs))
    return res


for camp in CAMPAIGNS:
    names = [a["name"] for a in camp["ad_groups"]]
    assert len(set(names)) == len(names)
    for ag in camp["ad_groups"]:
        variants = rsa_variants(camp, ag)
        assert sum(v[2] == "Enabled" for v in variants) <= 3, "max 3 enabled RSAs per ad group"
        for key, _, _, h, d in variants:
            where = f'{camp["name"]} / {ag["name"]} / {key}'
            assert len(h) == 15 and len(set(h)) == 15, where
            assert len(d) == 4 and len(set(d)) == 4, where
            for t in h:
                check(t, "headline", where)
            for t in d:
                check(t, "description", where)
        for p in ag["path"]:
            check(p, "path", where)
        assert final_url(camp["url"], camp["utm_campaign"], ag["slug"]).startswith(camp["url"])
for lst in CALLOUTS_BY_CAMPAIGN.values():
    for c in lst:
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
          [[c["name"], "Search", "Google search", c["budget"], "Daily", "Manual CPC", "he;en;ar",
            URL_SUFFIX, "Paused"] for c in CAMPAIGNS])

write_csv("02_ad_groups.csv",
          ["Campaign", "Ad Group", "Max CPC", "Ad Group Type", "Ad Group Status"],
          [[c["name"], ag["name"], f'{ag["cpc"]:.2f}', "Standard", "Enabled"]
           for c in CAMPAIGNS for ag in c["ad_groups"]])

write_csv("03_keywords.csv",
          ["Campaign", "Ad Group", "Keyword", "Criterion Type", "Status"],
          [[c["name"], ag["name"], kw, mt, "Enabled"]
           for c in CAMPAIGNS for ag in c["ad_groups"] for kw, mt, _ in ag["keywords"]])

neg_rows = []
for c in CAMPAIGNS:
    for kw in NEG_COMMON + c["campaign_negatives"]:
        neg_rows.append([c["name"], "", kw, "Negative Phrase"])
    for ag in c["ad_groups"]:
        if ag.get("geo_broad"):
            for kw in NEG_GEO_BROAD_AG:
                neg_rows.append([c["name"], ag["name"], kw, "Negative Phrase"])
write_csv("04_negative_keywords.csv", ["Campaign", "Ad Group", "Keyword", "Criterion Type"], neg_rows)

rsa_header = (["Campaign", "Ad Group", "Ad type"] + [f"Headline {i}" for i in range(1, 16)]
              + [f"Description {i}" for i in range(1, 5)] + ["Path 1", "Path 2", "Final URL", "Status"])
rsa_rows = []
for c in CAMPAIGNS:
    for ag in c["ad_groups"]:
        for key, _, status, h, d in rsa_variants(c, ag):
            rsa_rows.append([c["name"], ag["name"], "Responsive search ad"] + h + d + list(ag["path"])
                            + [final_url(c["url"], c["utm_campaign"], f'{ag["slug"]}_{key}'), status])
write_csv("05_responsive_search_ads.csv", rsa_header, rsa_rows)

write_csv("06_callouts.csv", ["Campaign", "Callout text"],
          [[c, t] for c, lst in CALLOUTS_BY_CAMPAIGN.items() for t in lst])
write_csv("07_structured_snippets.csv", ["Campaign", "Header", "Values"],
          [[c["name"], SNIPPET[0], ";".join(SNIPPET[1])] for c in CAMPAIGNS])

# single combined file
parts = sorted(glob.glob(os.path.join(EDITOR, "0*.csv")))
all_cols, tables = [], []
for pth in parts:
    with open(pth, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    tables.append(rows)
    for col in rows[0]:
        if col not in all_cols:
            all_cols.append(col)
combined = os.path.join(OUT, "google-ads-editor-import.csv")
n_combined = 0
with open(combined, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(all_cols)
    for rows in tables:
        idx = {col: i for i, col in enumerate(rows[0])}
        for r in rows[1:]:
            w.writerow([r[idx[col]] if col in idx else "" for col in all_cols])
            n_combined += 1

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


n_kw = sum(len(ag["keywords"]) for c in CAMPAIGNS for ag in c["ad_groups"])
n_ag = sum(len(c["ad_groups"]) for c in CAMPAIGNS)
total_budget = sum(c["budget"] for c in CAMPAIGNS)

# 1. Overview
overview = [
    ["מטרה", ""],
    ["יעד עסקי", "גיוס מאבטחים/ות חמושים/ות לשתי משרות בנגב: " + " · ".join(c["job"] for c in CAMPAIGNS)],
    ["המרה ראשית", "שליחת טופס מועמדות בעמוד המשרה — המרה נפרדת לכל משרה (Primary)"],
    ["המרות משניות", "קליק וואטסאפ, קליק טלפון (Secondary — לא נכנסות לאופטימיזציה)"],
    ["KPI מרכזי", "עלות לליד מתאים (Cost per Qualified Lead) לכל משרה — לפי סינון הגיוס, לא לפי כמות טפסים"],
    ["KPI משניים", "CTR ≥ 8% בקבוצות הכוונה הגבוהה · CVR עמוד ≥ 10% · Search Impression Share ≥ 60% בביטויי מאבטחים"],
    ["מבנה", ""],
    ["סוג קמפיין", "Search בלבד (Google Search, ללא Search Partners וללא Display Expansion)"],
    ["קמפיינים", "קמפיין נפרד לכל משרה: " + " · ".join(c["name"] for c in CAMPAIGNS)],
    ["קבוצות מודעות", f"{n_ag} קבוצות (4 לכל קמפיין), {n_kw} מילות מפתח (Exact + Phrase, ללא Broad בשלב ההשקה)"],
    ["דפי נחיתה", "כל המודעות בכל קמפיין מפנות לדף המשרה של אותו קמפיין בלבד, עם UTM ב-Final URL"],
    ["Sitelinks", "לא בשימוש — כל Sitelink היה מוביל לדף אחר מדף המשרה (וגוגל לא מאשר כמה Sitelinks לאותה כתובת)"],
    ["חפיפה בין הקמפיינים", "קבוצות 'מאבטחים חמושים - כללי' ו'עבודה מועדפת' זהות בשני הקמפיינים. גוגל יציג בכל חיפוש מודעה אחת בלבד מהחשבון (זו עם ה-Ad Rank הגבוה). הבידול: טרגוט גיאוגרפי שונה + שליליות ערים הדדיות"],
    ["תקציב", ""],
    ["תקציב יומי כולל", f"₪{total_budget} ליום (≈ ₪{total_budget * 30.4:,.0f} לחודש)"],
] + [[c["name"], f"₪{c['budget']} ליום"] for c in CAMPAIGNS] + [
    ["אסטרטגיית הצעות מחיר", ""],
    ["שלב 1 (ימים 1–14)", "Manual CPC לפי קבוצת מודעות: ₪6 כוונה גבוהה · ₪5 עבודה מועדפת · ₪3 קבוצות גיאוגרפיות רחבות — שליטה בתקציב שזורם לביטויים הרחבים"],
    ["שלב 2 (≥15 המרות טופס ב-30 יום, לכל קמפיין)", "מעבר ל-Maximize Conversions (המרת הטופס של אותה משרה בלבד)"],
    ["שלב 3 (≥30 המרות ב-30 יום)", "הגדרת tCPA לפי עלות לליד בפועל + 10–15%; שינויי יעד בצעדים של 10–15% בלבד"],
    ["טרגוט", ""],
] + [[f"מיקום — {c['short']}", c["geo"]] for c in CAMPAIGNS] + [
    ["שפות", "עברית + אנגלית + ערבית (חלק גדול מהמכשירים בישראל מוגדרים באנגלית; קהל בפזורה ורהט)"],
    ["מכשירים", "כל המכשירים; צפי ל-85%+ מובייל — לוודא שהטופס בעמוד נוח למובייל"],
    ["תזמון", "24/7 בשבועיים הראשונים; לאחר מכן לבחון התאמת הצעות לפי שעות (מינימום נפח)"],
    ["קהלים (Observation)", "להוסיף במצב Observation בלבד: In-market 'Jobs & Education > Jobs', Remarketing של מבקרי /jobs/ באתר — ללא צמצום טרגוט"],
    ["רגולציה והנחיות לקוח", ""],
    ["שכר", "לא מפרסמים שכר במודעות (לא סכום ולא 'שכר גבוה') — לפי הנחיית הלקוח"],
    ["שמות מעסיקים", "לא משתמשים בשמות המעסיקים — לא במילות המפתח ולא בטקסט המודעה — לפי הנחיית הלקוח"],
    ["שוויון הזדמנויות", "נוסח ניטרלי מגדרית (מאבטחים/ות) כנדרש בחוק שוויון ההזדמנויות בעבודה; לא לצמצם לפי גיל או מגדר"],
    ["EU political ads", "בזמן ה-Post ב-Editor לסמן: 'No, this campaign does not have EU political ads'"],
]
ws = sheet("סקירה", ["נושא", "פירוט"], overview, [40, 120], first=True)
mark_section(ws, 2)

# 2. Structure
struct = []
for c in CAMPAIGNS:
    struct.append([c["name"], "", f"₪{c['budget']}/יום", "", c["job"], "", ""])
    for ag in c["ad_groups"]:
        struct.append(["", ag["name"], "", f"₪{ag['cpc']:.0f}", len(ag["keywords"]), "/".join(ag["path"]),
                       final_url(c["url"], c["utm_campaign"], ag["slug"]) + "_v1…v4"])
ws = sheet("מבנה", ["קמפיין", "קבוצת מודעות", "תקציב", "Max CPC", "משרה / מס' מילות מפתח",
                    "Display path", "Final URL (כולל UTM)"], struct, [36, 28, 12, 10, 40, 26, 90])
for row in ws.iter_rows(min_row=2):
    if row[0].value:
        for cell in row:
            cell.fill = SEC_FILL
            cell.font = Font(name=F, bold=True)

# 3. UTM
utm_rows = []
for c in CAMPAIGNS:
    for ag in c["ad_groups"]:
        for key, label, status, _, _ in rsa_variants(c, ag):
            utm_rows.append([c["name"], ag["name"], f"{key} ({status})", "google", "cpc", c["utm_campaign"],
                             f'{ag["slug"]}_{key}', "{keyword} (דינמי, Final URL suffix)"])
ws = sheet("UTM", ["קמפיין", "קבוצת מודעות", "מודעה", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"],
           utm_rows, [30, 28, 24, 12, 12, 34, 40, 34])
r = len(utm_rows) + 3
ws.cell(r, 1, "utm_source / utm_medium / utm_campaign / utm_content כתובים ישירות ב-Final URL של כל מודעה. "
              "utm_term מתווסף אוטומטית דרך Final URL suffix ברמת הקמפיין (utm_term={keyword}). "
              "לוודא שהטופס באתר שומר את ה-UTM יחד עם הליד ב-CRM.").font = Font(name=F, italic=True)

# 4. Keywords
kw_rows = []
for c in CAMPAIGNS:
    for ag in c["ad_groups"]:
        for kw, mt, vol in ag["keywords"]:
            disp = f"[{kw}]" if mt == "Exact" else f'"{kw}"'
            kw_rows.append([c["name"], ag["name"], kw, mt, disp, vol if vol is not None else "—"])
ws = sheet("מילות מפתח", ["קמפיין", "קבוצת מודעות", "מילת מפתח", "התאמה", "כתיב Editor", "נפח חודשי (Ahrefs IL)"],
           kw_rows, [36, 28, 34, 10, 36, 18])
ws.cell(len(kw_rows) + 3, 1, "מקור נפחים: Ahrefs Keywords Explorer, ישראל, נובמבר 2026. '—' = אין נתון / נפח נמוך מאוד. "
                             "נפחים של Exact ו-Phrase לאותו ביטוי זהים (נפח הביטוי עצמו).").font = Font(name=F, italic=True)

# 5. Negatives
neg = [["שני הקמפיינים", "", k, "Phrase"] for k in NEG_COMMON]
for c in CAMPAIGNS:
    neg += [[c["name"], "", k, "Phrase — ניתוב ערים לקמפיין של המשרה השנייה"] for k in c["campaign_negatives"]]
    for ag in c["ad_groups"]:
        if ag.get("geo_broad"):
            neg += [[c["name"], ag["name"], k, "Phrase — ניתוב לקבוצות האבטחה / עבודה מועדפת"] for k in NEG_GEO_BROAD_AG]
sheet("מילות שליליות", ["קמפיין", "קבוצת מודעות (ריק = רמת קמפיין)", "מילת מפתח שלילית", "התאמה / סיבה"],
      neg, [36, 30, 26, 50])

# 6. RSA with live length checks
rsa_sheet_rows = []
for c in CAMPAIGNS:
    for ag in c["ad_groups"]:
        for key, label, status, h, d in rsa_variants(c, ag):
            ad = f"{key} — {label} ({status})"
            for i, t in enumerate(h, 1):
                rsa_sheet_rows.append([c["name"], ag["name"], ad, f"Headline {i}", t, None, 30])
            for i, t in enumerate(d, 1):
                rsa_sheet_rows.append([c["name"], ag["name"], ad, f"Description {i}", t, None, 90])
            for i, t in enumerate(ag["path"], 1):
                rsa_sheet_rows.append([c["name"], ag["name"], ad, f"Path {i}", t, None, 15])
ws = sheet("מודעות RSA", ["קמפיין", "קבוצת מודעות", "מודעה", "שדה", "טקסט", "תווים", "מקסימום", "תקין?"],
           rsa_sheet_rows, [28, 26, 34, 14, 80, 8, 10, 9])
for r in range(2, len(rsa_sheet_rows) + 2):
    ws.cell(r, 6, f"=LEN(E{r})")
    ws.cell(r, 8, f'=IF(F{r}<=G{r},"✔","✘ ארוך")')
    for col in (6, 7, 8):
        ws.cell(r, col).font = Font(name=F)
        ws.cell(r, col).alignment = Alignment(horizontal="center", vertical="top")
        ws.cell(r, col).border = BORDER

# 7. Assets
assets = []
for c, lst in CALLOUTS_BY_CAMPAIGN.items():
    assets += [[c, "Callout", t, ""] for t in lst]
assets += [["שני הקמפיינים", "Structured snippet", f"Header: {SNIPPET[0]} (סוגים)", " ; ".join(SNIPPET[1])]]
todo_start = len(assets) + 2
assets += [["שני הקמפיינים", "Call asset", "להשלים ידנית", "מספר גיוס ישיר (073-…) — *4960 לא נתמך כנכס שיחה. לאשר עם הלקוח איזה מספר מטפל במועמדים"],
           ["שני הקמפיינים", "Lead form asset", "אופציונלי", "טופס לידים בתוך גוגל: שם, טלפון, עיר + שאלות סינון (שירות מלא, פרופיל 02, רישיון). מחייב חיבור CRM / הורדה יומית"]]
ws = sheet("נכסים", ["קמפיין", "סוג", "טקסט", "תיאור / ערכים"], assets, [36, 20, 30, 80])
for row in ws.iter_rows(min_row=todo_start, max_row=todo_start + 1):
    for cell in row:
        cell.fill = TODO_FILL

# 8. Tracking
tracking = [
    ["Form submit – job 124651", "Primary (קמפיין עידן הנגב)", "GTM: אירוע הצלחת שליחת טופס בעמוד משרה 124651 → Google Ads Conversion נפרדת + GA4 generate_lead (job_id=124651)", "חובה לפני השקה"],
    ["Form submit – job 124655", "Primary (קמפיין נאות חובב)", "GTM: אירוע הצלחת שליחת טופס בעמוד משרה 124655 → Google Ads Conversion נפרדת + GA4 generate_lead (job_id=124655)", "חובה לפני השקה"],
    ["Campaign-specific goals", "—", "בהגדרות כל קמפיין: Goals → Use campaign-specific goal → רק ההמרה של המשרה שלו", "חובה לפני השקה"],
    ["WhatsApp click", "Secondary", "GTM: Click URL contains 'wa.me' או 'api.whatsapp.com'", "חובה לפני השקה"],
    ["Phone click", "Secondary", "GTM: Click URL starts with 'tel:'", "חובה לפני השקה"],
    ["Enhanced conversions for leads", "—", "להפעיל ב-Google Ads + להעביר טלפון מגובב (hashed) מהטופס", "מומלץ"],
    ["Offline conversion import", "Primary (שלב 2)", "ייבוא 'ליד מתאים' / 'התקבל לעבודה' מה-CRM לפי GCLID או טלפון", "מומלץ, אחרי 2–4 שבועות"],
    ["UTM", "—", "ראו טאב UTM — כלול ב-Final URL של כל מודעה + utm_term דרך Final URL suffix", "כלול ב-CSV"],
    ["Auto-tagging", "—", "לוודא שהוא פעיל בחשבון (GCLID)", "לבדוק"],
]
sheet("מעקב והמרות", ["המרה / רכיב", "סוג", "הגדרה", "סטטוס"], tracking, [30, 26, 100, 24])

# 9. Launch checklist
checklist = [
    ["לפני ייבוא", "לאחד מספר וואטסאפ בעמודי המשרה (כרגע מופיעים 052-2379532, 053-5216650, 053-2237953)", "☐"],
    ["לפני ייבוא", "לבטל את הפופאפ 'כיף שבאתם/ן' לתנועה עם utm_source=google בעמודי המשרה", "☐"],
    ["לפני ייבוא", "לוודא שעמודי המשרה נטענים תקין עם פרמטרי UTM ושהטופס שומר אותם", "☐"],
    ["מעקב", "להגדיר המרת טופס נפרדת לכל משרה + וואטסאפ + טלפון (טאב 'מעקב והמרות') ולבדוק ב-Tag Assistant", "☐"],
    ["ייבוא", "Google Ads Editor → Account → Import → From file → google-ads-editor-import.csv", "☐"],
    ["ייבוא", "להגדיר ידנית בכל קמפיין: מיקום (טאב 'סקירה' — רדיוס 25 ק\"מ, Presence), כיבוי Search Partners + Display", "☐"],
    ["ייבוא", "בכל קמפיין: Campaign-specific goal → רק המרת הטופס של המשרה שלו", "☐"],
    ["ייבוא", "Check changes → לתקן שגיאות → EU political ads = No → Post. הקמפיינים מיובאים במצב Paused", "☐"],
    ["השקה", "Preview & diagnosis ל-3 ביטויים מובילים בכל קמפיין; לוודא שהמודעה מפנה לדף המשרה הנכון; הפעלה", "☐"],
    ["ימים 1–7", "Search Terms report כל 3–4 ימים → הוספת שליליות", "☐"],
    ["ימים 7–14", "Asset performance; החלפת כותרות 'Low'; Impression Share ו-Lost IS (budget/rank); איזה קמפיין זוכה בביטויים המשותפים", "☐"],
    ["יום 14+", "מעבר ל-Maximize Conversions בכל קמפיין שהגיע ל-≥15 המרות טופס", "☐"],
    ["שוטף", "סנכרון שבועי עם הגיוס: כמה מהלידים בכל משרה מתאימים — זה ה-KPI האמיתי; כשמשרה מאוישת — להשהות את הקמפיין שלה", "☐"],
]
sheet("צ'קליסט השקה", ["שלב", "משימה", "בוצע"], checklist, [16, 120, 8])

# 10. Editor import guide
guide = [
    ["google-ads-editor-import.csv", f"קובץ אחד לייבוא ({n_combined} שורות): קמפיינים, קבוצות, מילות מפתח, שליליות, מודעות, Callouts, Snippets", "מומלץ"],
    ["editor-csv/01…07", "אותו תוכן מפוצל לפי סוג ישות", "גיבוי — אם הקובץ המאוחד נכשל, לייבא לפי הסדר"],
    ["קמפיינים", "Search, Manual CPC, ₪80 ליום כל אחד, Final URL suffix = utm_term={keyword}, Paused", "חובה להגדיר מיקום ידנית — קמפיין בלי מיקום מטורגט לכל העולם"],
    ["שליליות", f"{len(neg_rows)} שורות: ברמת קמפיין + ברמת קבוצה (קבוצות גיאוגרפיות רחבות)", ""],
    ["מודעות", f"{len(rsa_rows)} מודעות RSA — 4 לכל קבוצה (15 כותרות + 4 תיאורים), Final URL = דף המשרה + UTM (utm_content = קבוצה_מודעה)", "גוגל מאפשר עד 3 RSA פעילות לקבוצה: v1–v3 פעילות, v4 מושהית כגיבוי. ללא Pinning"],
    ["קידוד", "UTF-8 עם BOM", "אם Editor מציג ג'יבריש — לבקש גרסת UTF-16"],
]
sheet("ייבוא ל-Editor", ["קובץ / רכיב", "מה בפנים", "הערות"], guide, [36, 80, 60])

brief_path = os.path.join(OUT, "brief-search-security-negev.xlsx")
wb.save(brief_path)
print("OK", brief_path)
print("OK", combined, n_combined, "rows")
