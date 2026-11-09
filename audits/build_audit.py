"""Build the Google Ads audit deck for "צוות 3 מוקד ומערכות מיגון" (4598680211)."""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.oxml.ns import qn

OUT = sys.argv[1]

NAVY = RGBColor(0x14, 0x22, 0x3D)
INK = RGBColor(0x1F, 0x2A, 0x44)
MUTED = RGBColor(0x6B, 0x72, 0x80)
ACCENT = RGBColor(0x2D, 0x5B, 0xFF)
RED = RGBColor(0xC6, 0x28, 0x28)
AMBER = RGBColor(0xE0, 0x8A, 0x00)
GREEN = RGBColor(0x1F, 0x9D, 0x55)
LIGHT = RGBColor(0xF3, 0xF5, 0xF9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
W = prs.slide_width


def rtl(paragraph, align=PP_ALIGN.RIGHT):
    paragraph.alignment = align
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("rtl", "1")


def add_text(slide, x, y, w, h, text, size=14, bold=False, color=INK, align=PP_ALIGN.RIGHT,
             anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        rtl(p, align)
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = FONT
    return tb


def bullets(slide, x, y, w, h, items, size=15, gap=6):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        rtl(p)
        p.space_after = Pt(gap)
        if isinstance(item, tuple):
            head, body = item
            r = p.add_run(); r.text = "■ " + head
            r.font.bold = True; r.font.size = Pt(size); r.font.color.rgb = INK; r.font.name = FONT
            r2 = p.add_run(); r2.text = " — " + body
            r2.font.size = Pt(size); r2.font.color.rgb = INK; r2.font.name = FONT
        else:
            r = p.add_run(); r.text = "■ " + item
            r.font.size = Pt(size); r.font.color.rgb = INK; r.font.name = FONT
    return tb


def header(slide, title, subtitle=None):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(1.05))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    add_text(slide, Inches(0.5), Inches(0.18), W - Inches(1.0), Inches(0.7), title, size=26,
             bold=True, color=WHITE)
    if subtitle:
        add_text(slide, Inches(0.5), Inches(1.15), W - Inches(1.0), Inches(0.5), subtitle,
                 size=13, color=MUTED)


def footer(slide, n):
    add_text(slide, Inches(0.4), Inches(7.05), Inches(5), Inches(0.35),
             f"צוות 3 מוקד ומערכות מיגון | אודיט Google Ads | {n}", size=10, color=MUTED)


def table(slide, x, y, w, rows, col_w=None, size=12, head_fill=NAVY, row_h=Inches(0.36),
          color_col=None):
    nrows, ncols = len(rows), len(rows[0])
    shp = slide.shapes.add_table(nrows, ncols, x, y, w, row_h * nrows)
    tbl = shp.table
    # RTL table
    tblPr = tbl._tbl.tblPr
    tblPr.set("rtl", "1")
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(cw)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            rtl(p, PP_ALIGN.RIGHT if c == 0 else PP_ALIGN.CENTER)
            run = p.add_run()
            run.text = str(val)
            run.font.size = Pt(size)
            run.font.name = FONT
            if r == 0:
                run.font.bold = True
                run.font.color.rgb = WHITE
                cell.fill.solid(); cell.fill.fore_color.rgb = head_fill
            else:
                run.font.color.rgb = INK
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT if r % 2 == 0 else WHITE
                if color_col is not None and c == color_col:
                    v = str(val)
                    if v.startswith("קריטי"):
                        run.font.color.rgb = RED; run.font.bold = True
                    elif v.startswith("גבוה"):
                        run.font.color.rgb = AMBER; run.font.bold = True
                    elif v.startswith("בינוני"):
                        run.font.color.rgb = ACCENT; run.font.bold = True
    return tbl


def kpi_tile(slide, x, y, w, h, label, value, note=None, color=ACCENT):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT
    box.line.color.rgb = RGBColor(0xDD, 0xE2, 0xEA)
    box.adjustments[0] = 0.08
    add_text(slide, x + Inches(0.15), y + Inches(0.12), w - Inches(0.3), Inches(0.4), label,
             size=12, color=MUTED)
    add_text(slide, x + Inches(0.15), y + Inches(0.48), w - Inches(0.3), Inches(0.7), value,
             size=28, bold=True, color=color)
    if note:
        add_text(slide, x + Inches(0.15), y + h - Inches(0.5), w - Inches(0.3), Inches(0.4),
                 note, size=11, color=MUTED)


page = 0


def new_slide(title, subtitle=None):
    global page
    page += 1
    s = prs.slides.add_slide(BLANK)
    header(s, title, subtitle)
    footer(s, page)
    return s


# ---------------------------------------------------------------- 1. Title
page += 1
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
add_text(s, Inches(0.8), Inches(2.0), W - Inches(1.6), Inches(1.0), "אודיט מלא — Google Ads",
         size=44, bold=True, color=WHITE)
add_text(s, Inches(0.8), Inches(3.05), W - Inches(1.6), Inches(0.8),
         "צוות 3 מוקד ומערכות מיגון  |  חשבון 459-868-0211", size=24, color=WHITE)
add_text(s, Inches(0.8), Inches(4.1), W - Inches(1.6), Inches(1.2), [
    "תקופת ניתוח עיקרית: 11.08.2026 – 08.11.2026 (90 יום)",
    "מגמה: נובמבר 2025 – נובמבר 2026  |  מטבע: ₪  |  נתונים נמשכו מה-API ב-09.11.2026",
], size=16, color=RGBColor(0xC9, 0xD3, 0xE6))

# ---------------------------------------------------------------- 2. Exec summary
s = new_slide("תקציר מנהלים", "השורה התחתונה: החשבון לא מוגבל בתקציב — הוא מוגבל באיכות המדידה ובאיכות התנועה")
kpi_tile(s, Inches(9.8), Inches(1.75), Inches(3.0), Inches(1.6), "הוצאה (90 יום)", "₪66.7K",
         "~₪740 ליום")
kpi_tile(s, Inches(6.6), Inches(1.75), Inches(3.0), Inches(1.6), "המרות ראשיות", "666",
         "481 שיחות + 182 טפסים")
kpi_tile(s, Inches(3.4), Inches(1.75), Inches(3.0), Inches(1.6), "עלות להמרה", "₪100",
         "לעומת ~₪30 בינואר–יוני", color=RED)
kpi_tile(s, Inches(0.2), Inches(1.75), Inches(3.0), Inches(1.6), "עלות לליד טופס", "₪367",
         "לעומת ~₪124 במרץ", color=RED)
bullets(s, Inches(0.5), Inches(3.6), W - Inches(1.0), Inches(3.4), [
    ("לידים מטפסים ירדו ב-~70%", "מ-~190 בחודש (מרץ–יוני) ל-~60 בחודש (אוג׳–אוק׳) בהוצאה דומה של ₪20–25K. זה הסימן האמיתי לבעיה, לא ה-CPA הכולל."),
    ("ההמרות של ינואר–יוני היו מנופחות", "שיחות מודעה שנספרו מ-40 שניות, מקמפייני PMax של רשימות לקוחות (\"מנותקים\", \"לקוחות בסטטוס נסגר\") — ככל הנראה לקוחות קיימים ושירות. 1,223 \"שיחות\" ביוני לבד."),
    ("~37% מההוצאה בחיפוש הולכת למתחרים ולחיפושי ניווט", "\"מוקד מבצר\", \"G1 טלפון\", \"מוקד 99 טלפון\", \"hikvision תמיכה\" — דרך מילת מפתח רחבה \"מוקד אבטחה\" (46% מתקציב הקמפיין)."),
    ("חוויית דף נחיתה \"מתחת לממוצע\" כמעט בכל מילות המפתח", "ציון איכות 5 ברוב ההוצאה; 95% מהתנועה ממובייל."),
    ("ניהול ידני שמאפס למידה", "השהיה והפעלה של כל הקמפיינים (5.11 → 8.11) ועריכות מודעות רחבות — 3 מתוך 4 קמפיינים פעילים בסטטוס Learning."),
], size=14)

# ---------------------------------------------------------------- 3. Trend chart
s = new_slide("מגמה חודשית: הוצאה מול המרות ולידים מטפסים",
              "מאז יולי: ההוצאה ירדה ב-~30%, ההמרות המדווחות ב-~80%, והלידים מטפסים ב-~70%")
months = ["11/25", "12/25", "01/26", "02/26", "03/26", "04/26", "05/26", "06/26", "07/26",
          "08/26", "09/26", "10/26"]
spend = [26.7, 27.0, 27.2, 21.7, 23.6, 36.2, 33.7, 52.8, 29.6, 24.7, 24.4, 20.5]
conv = [1201, 1234, 721, 898, 1286, 1002, 876, 1412, 260, 254, 210, 222]
cd = CategoryChartData()
cd.categories = months
cd.add_series("הוצאה (אלפי ₪)", spend)
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(6.8), Inches(1.7), Inches(6.2),
                        Inches(4.9), cd)
ch = gf.chart
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb = ACCENT
ch.has_title = True; ch.chart_title.text_frame.text = "הוצאה חודשית (אלפי ₪)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)

cd2 = CategoryChartData()
cd2.categories = ["03/26", "04/26", "05/26", "06/26", "07/26", "08/26", "09/26", "10/26"]
cd2.add_series("לידים מטפסים", [189, 219, 193, 189, 105, 52, 62, 61])
cd2.add_series("שיחות ממודעה (≥40 שנ׳)", [433, 601, 683, 1223, 155, 199, 148, 161])
gf2 = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.3), Inches(1.7), Inches(6.3),
                         Inches(4.9), cd2)
ch2 = gf2.chart
ch2.has_legend = True; ch2.legend.position = XL_LEGEND_POSITION.BOTTOM; ch2.legend.include_in_layout = False
ch2.series[0].format.line.color.rgb = RED
ch2.series[1].format.line.color.rgb = MUTED
ch2.has_title = True; ch2.chart_title.text_frame.text = "המרות לפי סוג (מרץ–אוקטובר)"
ch2.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
add_text(s, Inches(0.5), Inches(6.65), W - Inches(1.0), Inches(0.4),
         "קפיצת השיחות ביוני (1,223) מגיעה מקמפייני PMax של רשימות לקוחות שהושהו ביולי–אוגוסט. ירידת הטפסים היא ירידה אמיתית בביקוש שנקלט.",
         size=12, color=MUTED)

# ---------------------------------------------------------------- 4. Campaign table
s = new_slide("ביצועים לפי קמפיין — 90 יום", "4 קמפיינים פעילים + 2 שהיו פעילים בתקופה. כל הסכומים ב-₪")
rows = [
    ["קמפיין", "סוג", "הוצאה", "קליקים", "CPC", "המרות", "CPA", "טפסים", "₪/טופס", "נתח חשיפות", "אבד בדירוג"],
    ["מוקד אבטחה- Search", "Search", "39,080", "2,616", "14.9", "372", "105", "77", "504", "40%", "57%"],
    ["Remarketing 17/8", "PMax", "19,888", "10,095", "2.0", "235", "85", "57", "348", "—", "—"],
    ["אזעקה לבית", "Search", "4,626", "734", "6.3", "46", "101", "44", "105", "26%", "74%"],
    ["אזעקה לעסק 3/9/26 (מושהה)", "Search", "2,429", "37", "65.7", "2", "1,215", "2", "1,215", "68%", "23%"],
    ["Demand Gen 2/11/26", "Demand Gen", "391", "231", "1.7", "0", "—", "0", "—", "—", "—"],
    ["Pmax מנותקים (מושהה)", "PMax", "291", "47", "6.2", "11", "26", "1", "291", "—", "—"],
    ["סה\"כ", "", "66,706", "13,760", "4.8", "666", "100", "182", "367", "", ""],
]
table(s, Inches(0.3), Inches(1.7), Inches(12.7), rows,
      col_w=[2.9, 1.1, 1.0, 0.95, 0.8, 0.95, 0.85, 0.9, 0.95, 1.1, 1.2], size=12)
bullets(s, Inches(0.5), Inches(4.85), W - Inches(1.0), Inches(2.1), [
    ("\"אזעקה לבית\" הוא הקמפיין היעיל בחשבון", "₪105 לטופס — פי 3–5 זול מהשאר — ומקבל רק 7% מהתקציב, עם 74% חשיפות שאבדו בגלל דירוג."),
    ("\"מוקד אבטחה- Search\" לוקח 59% מהתקציב", "79% מההמרות שלו הן שיחות; ₪504 לטופס. השם לא תואם לתוכן — רוב ההוצאה בפועל על מצלמות."),
    ("\"אזעקה לעסק\"", "₪2,429 על 37 קליקים (CPC ₪66) ושני טפסים — מושהה, ובצדק. לא להחזיר באותו מבנה."),
], size=13)

# ---------------------------------------------------------------- 5. Conversion tracking
s = new_slide("מעקב המרות — הבעיה מספר 1",
              "האלגוריתם מאופטמז לשיחות קצרות ולא מסוננות, ולא ללידים שנסגרים")
rows = [
    ["פעולת המרה", "סטטוס", "ספירה", "סף / הגדרה", "90 יום", "ממצא"],
    ["שיחת טלפון ממודעה", "ראשית", "אחת לקליק", "40 שניות", "481", "קריטי — 40% מהשיחות <40 שנ׳, ושיחות מתחרים/שירות נספרות"],
    ["Submit lead form Thank you- Sales", "ראשית", "כל ההמרות", "ללא ערך", "182", "גבוה — לשנות ל\"אחת\"; ללא ערך המרה"],
    ["Click to call - sales phone number", "ראשית", "אחת", "10 שניות", "3", "גבוה — מספר מעקב באתר כמעט לא עובד"],
    ["Click to call 27/8/26", "ראשית", "אחת", "60 שניות", "0", "בינוני — לא נספר דבר; לבדוק או להסיר"],
    ["Android installs (all other apps)", "ראשית", "אחת", "—", "0", "בינוני — לא רלוונטי לעסק; להסיר מהיעדים"],
    ["GA4 טלפונים למכירות", "משנית*", "כל ההמרות", "—", "453", "בינוני — מסומן ראשי ביעד אך לא נכלל; מצב לא עקבי"],
    ["Click on Whatsapp button", "משנית", "כל ההמרות", "—", "349", "בינוני — מקור לידים גדול שלא נמדד בהצעות המחיר"],
]
table(s, Inches(0.3), Inches(1.7), Inches(12.7), rows,
      col_w=[3.0, 0.95, 1.1, 1.15, 0.85, 5.65], size=11, color_col=5)
bullets(s, Inches(0.5), Inches(5.0), W - Inches(1.0), Inches(2.0), [
    ("פילוח שיחות (30 יום, 344 שיחות)", "129 מתחת ל-40 שנ׳, 77 בין 40–90 שנ׳, 120 מעל 90 שנ׳. 61% מהשיחות מגיעות מ-PMax \"Remarketing\"."),
    ("אין ערכי המרה ואין ייבוא מ-CRM", "Google לא יודע איזה ליד הפך לעסקה — לכן הוא קונה את ההמרה הזולה ביותר (שיחה של 41 שנ׳ ממתחרה)."),
    ("כ-60 פעולות המרה ישנות (UA / GA4 מוסתרות)", "רעש בממשק; לא משפיע על הבידינג אבל מקשה על ניהול."),
], size=13)

# ---------------------------------------------------------------- 6. Search terms
s = new_slide("מונחי חיפוש — לאן הכסף הולך",
              "300 מונחי החיפוש המובילים (₪18.1K מתוך ההוצאה בחיפוש), 90 יום")
rows = [
    ["סוג שאילתה", "הוצאה", "% מההוצאה", "קליקים", "המרות"],
    ["כללית (מצלמות / אזעקה / מוקד)", "₪11,383", "63%", "742", "105"],
    ["שם של מתחרה", "₪5,916", "33%", "265", "56"],
    ["ניווט / שירות (\"טלפון\", \"תמיכה\")", "₪764", "4%", "27", "7"],
    ["מותג צוות 3", "₪19", "0%", "5", "0"],
]
table(s, Inches(6.9), Inches(1.7), Inches(6.1), rows, col_w=[2.5, 1.0, 0.95, 0.85, 0.8], size=12)
add_text(s, Inches(0.4), Inches(1.65), Inches(6.2), Inches(0.4), "דוגמאות לשאילתות מתחרים / ניווט שקיבלו קליקים:",
         size=14, bold=True)
bullets(s, Inches(0.4), Inches(2.1), Inches(6.2), Inches(3.0), [
    "מוקד מבצר (₪339) · מוקד מבצר טלפון (₪163)",
    "g1 טלפון (₪257) · מוקד ג׳י וואן (₪181) · ג׳י וואן (₪76)",
    "בן בטחון טלפון נתניה (₪140) · בת קול באר שבע (₪215)",
    "מוקד 99 טלפון / עפולה / אשדוד · מוקד אמון נתניה / הרצליה",
    "hikvision תמיכה / dvr · פרוויזן תמיכה · קוברה מצלמות לרכב",
    "עמישב ביטחון · מוקד שחר טלפון · מוקד עורב · מולאן בית שמש",
], size=13, gap=3)
bullets(s, Inches(0.5), Inches(4.75), W - Inches(1.0), Inches(2.2), [
    ("המקור", "מילת המפתח \"מוקד אבטחה\" בהתאמה רחבה בקבוצה שנקראת \"Phrase\" — ₪18.1K (46% מהקמפיין). הרשימה השלילית המשותפת (1,217 מילים) לא חוסמת את רוב שמות המתחרים."),
    ("למה זה מסוכן", "מי שמחפש \"מוקד מבצר טלפון\" הוא בדרך כלל לקוח של מבצר שמחפש שירות. אם הוא מתקשר ומחזיק 40 שנ׳ — זו \"המרה\", והאלגוריתם לומד לחפש עוד כאלה."),
    ("החלטה עסקית", "אם בכל זאת רוצים לגייס לקוחות של מתחרים — בקמפיין נפרד, עם מסר ייעודי, תקציב תחום ומדידה של סגירות בפועל."),
], size=13)

# ---------------------------------------------------------------- 7. Keywords & QS
s = new_slide("מילות מפתח, ציון איכות ודפי נחיתה",
              "הבעיה העקבית: חוויית דף הנחיתה \"מתחת לממוצע\" כמעט בכל מילות המפתח")
rows = [
    ["מילת מפתח", "התאמה", "קבוצה", "הוצאה", "המרות", "QS", "דף נחיתה"],
    ["מוקד אבטחה", "רחבה", "מוקד אבטחה - Phrase", "₪18,109", "196", "7", "ממוצע"],
    ["מצלמות אבטחה", "רחבה", "התקנת מצלמות Broad", "₪12,126", "93", "5", "מתחת לממוצע"],
    ["מצלמות אבטחה לבית כולל התקנה מחיר", "רחבה", "מוקד אבטחה - Phrase", "₪2,645", "23", "7", "מתחת לממוצע"],
    ["מערכת אזעקה", "רחבה", "אזעקה לבית", "₪2,581", "29", "5", "מתחת לממוצע"],
    ["מתקין מצלמות", "ביטוי", "מתקין מצלמות", "₪1,093", "9", "5", "מתחת לממוצע"],
    ["מוקד שמירה", "רחבה", "מוקד אזעקה", "₪572", "2", "7", "מעל הממוצע"],
]
table(s, Inches(0.3), Inches(1.7), Inches(12.7), rows, col_w=[3.6, 0.9, 2.6, 1.2, 1.0, 0.7, 2.7], size=12)
bullets(s, Inches(0.5), Inches(4.45), W - Inches(1.0), Inches(2.5), [
    ("שתי מילים רחבות אוכלות 77% מהקמפיין המרכזי", "\"מוקד אבטחה\" ו\"מצלמות אבטחה\" (רחבה) — ₪30.2K מתוך ₪39.1K."),
    ("חוסר סדר במבנה", "שמות קבוצות לא תואמים לסוג ההתאמה; מילת מצלמות בתוך קבוצת \"מוקד אבטחה\"; קבוצת \"התקנת מצלמות Broad\" מושהית אחרי ₪14K בתקופה."),
    ("המודעה המובילה (₪14.5K) מפנה לעמוד כללי באתר", "team3.co.il/protection-systems — לא לדף נחיתה ייעודי. מודעה טקסט מורחבת ישנה עדיין רצה ל-/lp/hikvision-on-sale."),
    ("95% מהתנועה בחיפוש ממובייל", "דף הנחיתה חייב להיות מהיר, עם כפתור חיוג ו-WhatsApp צמודים וטופס קצר (שם + טלפון)."),
], size=13)

# ---------------------------------------------------------------- 8. PMax / Demand Gen
s = new_slide("Performance Max ו-Demand Gen",
              "\"Remarketing 17/8\" הוא לא קמפיין רימרקטינג — הוא PMax רחב עם אותות קהל בלבד")
bullets(s, Inches(0.5), Inches(1.7), W - Inches(1.0), Inches(5.2), [
    ("PMax \"Remarketing 17/8\": ₪19.9K, 235 המרות, CPA ₪85", "אבל 75% מההמרות הן שיחות (177), ו-61% מכל השיחות בחשבון מגיעות ממנו. CTR של 1.7% ו-10K קליקים מצביעים על הרבה תנועת Display/YouTube."),
    ("קבוצת נכסים \"Website visitors\"", "₪10.7K, 7,880 קליקים, 120 המרות — CPC ₪1.35. סביר שזו תנועה זולה ולא איכותית."),
    ("קבוצת נכסים \"לקוחות בסטטוס נסגר / פגישה / הצעת מחיר\"", "₪9.2K, 116 המרות. רשימת לקוחות קיימים כאות — מושך את האלגוריתם ללקוחות קיימים שמתקשרים לשירות."),
    ("נושאי חיפוש בעייתיים", "\"דרושים סיירים\" (מחפשי עבודה — ואכן נרשמו המרות \"Jobs Thank you\" בקמפיין), \"מה ההבדל בין dvr ל nvr\" (מידע בלבד), \"אינטרקום לבניין\"."),
    ("הסטטוס: Limited — מוגבל תקציב + Learning", "יעד CPA ₪71 לא תואם את ה-CPA בפועל (₪85); הקמפיין הופעל-הושהה ב-5.11 ו-8.11."),
    ("Demand Gen \"מי שומר על הבית והעסק\" (מ-2.11)", "₪391, 231 קליקים, 0 המרות ראשיות. מוקדם לשפוט, אבל Maximize Conversions בלי המרות ב-₪75 ליום לא ילמד. לוודא טירגוט גיאוגרפי (לא נמצא ברמת קמפיין)."),
], size=14)

# ---------------------------------------------------------------- 9. Settings & hygiene
s = new_slide("הגדרות חשבון וטירגוט", "ממצאים טכניים")
rows = [
    ["נושא", "מצב נוכחי", "חומרה", "המלצה"],
    ["טירגוט מיקום", "נוכחות או עניין בישראל", "גבוה", "לשנות ל\"נוכחות\" בלבד בכל הקמפיינים"],
    ["ניהול זמנים", "השהיה/הפעלה ידנית של כל הקמפיינים", "גבוה", "לוח זמנים למודעות במקום השהיה; לעצור את מחזורי ה-Learning"],
    ["רשת שותפי חיפוש ו-Display בחיפוש", "כבויים", "תקין", "להשאיר"],
    ["תוספי שיחה", "קיימים (073-8010665) בכל הקמפיינים", "בינוני", "\"אזעקה לבית\" על הגדרת המרה ברמת חשבון והשאר ברמת משאב — לאחד"],
    ["תוספים", "Sitelinks, Callouts, Snippets, לוגו, תמונות", "תקין", "לרענן נוסח ולהוסיף מבצעים/מחירים"],
    ["מודעות", "4 RSA בדירוג \"חלש\"; מודעות טקסט מורחבות ישנות עדיין פעילות", "בינוני", "לשפר כותרות; לנקות מודעות טקסט מורחבות"],
    ["קמפיין \"ניסוי מחיר יעד - מתחרים 4.17\"", "מופעל אבל הסתיים (קמפיין ישן)", "בינוני", "להסיר — רעש בחשבון"],
    ["קמפיינים מושהים", "45 קמפיינים מושהים", "בינוני", "לארכב את מה שלא יחזור"],
]
table(s, Inches(0.3), Inches(1.6), Inches(12.7), rows, col_w=[2.9, 3.8, 1.0, 5.0], size=12, color_col=2)

# ---------------------------------------------------------------- 10. Action plan
s = new_slide("תוכנית פעולה — לפי סדר עדיפות", "שבוע 1 = מדידה. בלי זה כל שאר האופטימיזציה נבנית על נתונים שגויים")
rows = [
    ["#", "פעולה", "איפה", "השפעה צפויה", "מתי"],
    ["1", "להעלות סף שיחה ל-90 שנ׳ (או 60 + פילוח); טופס ל\"אחת\"; להסיר Android installs ו-Click to call 27/8 מהיעדים", "יעדי המרה", "הפסקת הלמידה משיחות לא רלוונטיות", "שבוע 1"],
    ["2", "ייבוא המרות אופליין מה-CRM (פגישה נקבעה / עסקה נסגרה) עם GCLID + Enhanced Conversions for Leads", "CRM ← Google Ads", "בידינג לפי עסקאות ולא לפי קליקים לטלפון", "שבועות 1–3"],
    ["3", "לתקן מספר מעקב באתר (Website calls) — 3 המרות ב-90 יום", "תג / דפי נחיתה", "מדידת שיחות מהאתר", "שבוע 1"],
    ["4", "להוסיף שמות מתחרים + \"טלפון\", \"תמיכה\", \"אזור אישי\" לרשימה השלילית; להחליף \"מוקד אבטחה\" רחבה בביטוי/מדויקת", "מוקד אבטחה- Search", "חיסכון של ~₪2–2.5K בחודש", "שבוע 1"],
    ["5", "להעביר תקציב ל\"אזעקה לבית\" (₪105 לטופס, 74% אבד בדירוג)", "אזעקה לבית", "+30–50 טפסים בחודש באותו תקציב כולל", "שבוע 2"],
    ["6", "לפצל את \"מוקד אבטחה- Search\" ל-2 קמפיינים: מוקד/ניטור ומצלמות, כל אחד עם דף נחיתה ייעודי", "מבנה", "שליטה בתקציב ובמסר", "שבוע 2–3"],
    ["7", "PMax: להוציא רשימת לקוחות קיימים, להפעיל \"לקוחות חדשים בלבד\", למחוק \"דרושים סיירים\" ונושאי מידע", "Remarketing 17/8", "פחות שיחות שירות, יותר לידים חדשים", "שבוע 2"],
    ["8", "דף נחיתה למובייל: מהירות, טופס קצר, חיוג ו-WhatsApp צמודים; לבדוק בדיקות A/B", "team3.co.il/lp2", "שיפור ציון האיכות מ-5 ל-7 ← CPC נמוך יותר", "שבועות 2–4"],
    ["9", "טירגוט \"נוכחות\"; לוח זמנים במקום השהיה; ניקוי קמפיינים ומודעות ישנים", "חשבון", "יציבות למידה", "שבוע 1"],
]
table(s, Inches(0.2), Inches(1.6), Inches(12.9), rows, col_w=[0.4, 6.2, 2.0, 3.2, 1.1], size=11,
      row_h=Inches(0.52))

# ---------------------------------------------------------------- 11. Budget proposal
s = new_slide("הצעת חלוקת תקציב (לאחר תיקון המדידה)", "באותו תקציב חודשי של ~₪22–23K (ממוצע אוג׳–אוק׳)")
rows = [
    ["קמפיין", "היום (חודשי)", "מוצע (חודשי)", "שינוי", "נימוק"],
    ["מוקד אבטחה- Search (מפוצל)", "~₪13,000", "~₪9,500", "-27%", "ניקוי מתחרים וחיפושי ניווט; התאמות מדויקות"],
    ["אזעקה לבית", "~₪1,500", "~₪4,500", "+200%", "הקמפיין היעיל ביותר; יש מלאי חשיפות"],
    ["PMax (לקוחות חדשים בלבד)", "~₪6,600", "~₪5,500", "-17%", "לצמצם עד שיש ייבוא אופליין"],
    ["Demand Gen", "~₪2,250", "~₪1,500", "-33%", "בדיקה מוגבלת; לבנות קהל לרימרקטינג"],
    ["רזרבה לבדיקות (מתחרים / אזעקה לעסק)", "—", "~₪1,000", "חדש", "רק עם מדידת סגירות"],
]
table(s, Inches(0.3), Inches(1.7), Inches(12.7), rows, col_w=[3.4, 1.6, 1.6, 1.0, 5.1], size=13)
add_text(s, Inches(0.5), Inches(4.6), W - Inches(1.0), Inches(1.6), [
    "יעד ל-60 יום: לחזור ל-110–130 לידים מטפסים בחודש (₪170–200 לטופס) ולמדוד עלות לפגישה ולעסקה מתוך ה-CRM.",
    "ההערכה מבוססת על ה-CPA ההיסטורי של כל קמפיין, ולכן גסה. לבחון מחדש אחרי שבועיים של נתונים נקיים.",
], size=14, color=INK)

# ---------------------------------------------------------------- 12. Methodology
s = new_slide("מתודולוגיה והערות", None)
bullets(s, Inches(0.5), Inches(1.5), W - Inches(1.0), Inches(5.4), [
    "מקור: Google Ads API, חשבון 4598680211 (תחת MCC 4305746867), שנמשך ב-09.11.2026.",
    "תקופה עיקרית: 11.08.2026–08.11.2026. מגמה: 01.11.2025–08.11.2026. נתוני נובמבר 2026 חלקיים (8 ימים).",
    "\"המרות\" = עמודת Conversions (פעולות ראשיות בלבד). \"טפסים\" = Submit lead form Thank you- Sales. ייחוס: מבוסס נתונים, חלון 30 יום.",
    "ניתוח מונחי חיפוש: 300 המונחים המובילים לפי הוצאה (₪18.1K). הסיווג למתחרים / ניווט נעשה לפי רשימת שמות ידנית ולכן הוא הערכה.",
    "פילוח השיחות לפי משך: call_view, 30 הימים האחרונים (344 שיחות).",
    "לא נבדקו: Auction Insights (לא זמין ב-API), איכות הלידים ב-CRM, מהירות דפי הנחיתה. מומלץ להשלים.",
    "לא בוצעו שינויים בחשבון. כל ההמלצות דורשות אישור לפני ביצוע.",
], size=14)

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
