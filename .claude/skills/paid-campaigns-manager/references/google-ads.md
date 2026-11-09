# Google Ads — פלייבוק

## סוגי קמפיינים — מתי מה

| סוג | מתי להשתמש | הערות |
|---|---|---|
| **Search** | ביקוש קיים, כוונה גבוהה. בסיס כמעט לכל עסק לידים | הגרעין של החשבון. מותג בנפרד מגנרי |
| **Performance Max** | יש המרות אמינות (30+/חודש), נכסים קריאייטיביים טובים, או פיד מוצרים (איקומרס) | חובה: Brand exclusions, מילות שליליות ברמת חשבון, אותות קהל, בדיקת דוח Search terms/Insights |
| **AI Max for Search** | הרחבת Search לשאילתות שהמילים לא מכסות, כשיש Smart Bidding יציב | הפעל כניסוי מול הקמפיין הקיים; עקוב אחרי שאילתות ו-URLs שנבחרו |
| **Demand Gen** | יצירת ביקוש ב-YouTube/Discover/Gmail, רימרקטינג ויזואלי | חלופה "מטא-ית" בתוך גוגל; צריך קריאייטיב חזק |
| **Shopping (Standard)** | איקומרס עם שליטה הדוקה במוצרים/מחירים | לעיתים לצד PMax למוצרים ספציפיים |
| **Video (YouTube)** | מודעות, הסבר מוצר מורכב | מדוד עם Brand Lift / המרות view-through בזהירות |
| **Display** | בעיקר רימרקטינג בתקציב נמוך | Prospecting בדיספליי לרוב לא יעיל לעסקי לידים |

## מבנה חשבון מומלץ לעסק לידים

```
חשבון
├─ Search | Brand            (מילות מותג, Exact/Phrase, הגנה על המותג)
├─ Search | Generic – שירות A (Ad groups לפי כוונה, לא לפי מילה בודדת)
├─ Search | Generic – שירות B
├─ Search | Competitors       (אופציונלי, תקציב מוגבל, מדוד בנפרד)
├─ PMax | Leads               (אחרי שיש 30+ המרות/חודש; Brand excluded)
└─ Demand Gen | Remarketing / Prospecting (אופציונלי)
```

עקרונות: Ad group = נושא/כוונה אחת עם 5–20 מילים קרובות; RSA אחד-שניים חזקים לכל קבוצה;
רשימות מילות שליליות משותפות (עבודה/דרושים, חינם, DIY, "איך לעשות", מתחרים לא רלוונטיים).

## התאמות מילות מפתח ובידינג

- **Broad match + Smart Bidding** עובד היטב כשיש נתוני המרה איכותיים; בלי זה — Phrase/Exact.
- **מסלול בידינג טיפוסי**:
  1. חשבון חדש / מעט נתונים → Maximize Clicks עם Max CPC cap, או Manual CPC (קצר).
  2. 15–30 המרות → Maximize Conversions.
  3. 30–50+ המרות יציבות → Target CPA (התחל ב-CPA בפועל של 30 הימים האחרונים, הורד ב-10–15% בכל פעם).
  4. ערכי המרה אמיתיים (ליד איכותי=X, עסקה=Y) → Maximize Conversion Value / Target ROAS.
- **Value-based bidding ללידים**: העבר ערכים שונים לפי איכות (טופס מלא > שיחה קצרה), ואם אפשר —
  ייבא סגירות מה-CRM (Offline conversion import / Enhanced Conversions for Leads).
- לא לשנות tCPA/tROAS ביותר מ-15–20% בפעם; לחכות ~1–2 מחזורי המרה (או שבוע) בין שינויים.

## מדידה

- Google Tag / GTM, **Enhanced Conversions** (גם ללידים), המרה ראשית אחת ברורה לבידינג.
- שיחות: Call assets + שיחות מהאתר (Google forwarding number) עם סף משך (60–90 שניות).
- ייבוא סגירות: GCLID/GBRAID/WBRAID נשמרים בטופס → CRM → ייבוא offline. זה משדרג משמעותית
  את איכות הלידים ב-Smart Bidding.
- Consent Mode — רלוונטי למבקרים מהאיחוד האירופי; בדוק אם יש תנועה כזו.
- סמן המרות משניות (צפייה בדף, קליק על מייל) כ-Secondary כדי שלא ינפחו את הבידינג.

## שגרת אופטימיזציה

**יומי (5 דק')**: חריגות הוצאה, קמפיינים מוגבלים בתקציב, מודעות שנדחו, המרות שנעלמו (תג שבור).
**שבועי**: Search terms → שליליות + מילים חדשות; ביצועי Ad groups; Impression share (Lost to budget vs rank);
Assets עם "Low"; התאמות מכשיר/מיקום/שעות רק אם יש מובהקות.
**חודשי**: מבנה חשבון, יעדי בידינג, ניסויים (Experiments), דפי נחיתה, Auction insights, הקצאת תקציב בין קמפיינים.

## אבחון מהיר — מדדים ספציפיים לגוגל

- **Search IS נמוך + Lost IS (budget) גבוה** → מוגבל בתקציב: העלה תקציב או צמצם מילים/אזורים.
- **Lost IS (rank) גבוה** → Ad Rank: איכות מודעה, רלוונטיות דף נחיתה, בידינג.
- **Quality Score ≤ 5** → פרק לרכיבים: Expected CTR / Ad relevance / Landing page experience.
- **CTR טוב, המרה נמוכה** → דף נחיתה / התאמת מסר / שאילתות לא רלוונטיות.
- **CPC עולה** → Auction insights (מתחרה חדש?), שינוי בידינג, עונתיות.

## שאילתות GAQL מוכנות (ל-`mcp__Google_Ads__search_search`)

ביצועי קמפיינים (30 יום):
```sql
SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type,
       campaign.bidding_strategy_type, metrics.cost_micros, metrics.impressions,
       metrics.clicks, metrics.ctr, metrics.average_cpc, metrics.conversions,
       metrics.cost_per_conversion, metrics.conversions_value,
       metrics.search_impression_share, metrics.search_budget_lost_impression_share,
       metrics.search_rank_lost_impression_share
FROM campaign
WHERE segments.date DURING LAST_30_DAYS AND campaign.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC
```

מונחי חיפוש עם הוצאה וללא המרות:
```sql
SELECT search_term_view.search_term, campaign.name, ad_group.name,
       metrics.cost_micros, metrics.clicks, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS AND metrics.conversions = 0
  AND metrics.cost_micros > 50000000
ORDER BY metrics.cost_micros DESC
LIMIT 200
```

ציון איכות מילות מפתח:
```sql
SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
       ad_group_criterion.quality_info.quality_score,
       ad_group_criterion.quality_info.creative_quality_score,
       ad_group_criterion.quality_info.post_click_quality_score,
       ad_group_criterion.quality_info.search_predicted_ctr,
       metrics.cost_micros, metrics.conversions
FROM keyword_view
WHERE segments.date DURING LAST_30_DAYS AND ad_group_criterion.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
LIMIT 200
```

פעולות המרה (בדיקת מדידה):
```sql
SELECT conversion_action.name, conversion_action.status, conversion_action.type,
       conversion_action.category, conversion_action.primary_for_goal,
       conversion_action.counting_type, conversion_action.include_in_conversions_metric
FROM conversion_action
```

מגמה יומית:
```sql
SELECT segments.date, metrics.cost_micros, metrics.clicks, metrics.conversions,
       metrics.cost_per_conversion
FROM customer
WHERE segments.date DURING LAST_30_DAYS
ORDER BY segments.date
```

פילוח מכשירים / שעות: הוסף `segments.device` או `segments.hour`, `segments.day_of_week` לשאילתת campaign.

הערות: `cost_micros` ÷ 1,000,000 = מטבע החשבון. אם שם שדה לא מתקבל — בדוק עם
`mcp__Google_Ads__metadata_get_resource_metadata`.
