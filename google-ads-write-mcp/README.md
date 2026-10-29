# Google Ads Write MCP — כלי כתיבה לקמפיינים

תוסף לשרת ה-MCP הרשמי של Google ([googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp)),
שמוסיף לו יכולת **ליצור ולערוך קמפיינים מכל הסוגים**: Search, Display, Shopping,
Video, Performance Max, **Demand Gen**, App, Hotel ועוד.

השרת מריץ את השרת הרשמי כמו שהוא (כלי הקריאה `search`, `get_resource_metadata`,
`list_accessible_customers` והמשאבים שלו) ומוסיף לידו כלי כתיבה עם הקידומת `write_`.
הכלים עובדים מול Google Ads API בגרסה v26.

## מנגנוני בטיחות

1. **הרצת ניסיון כברירת מחדל:** בכל כלי `validate_only=true` כברירת מחדל. Google
   בודקת את הבקשה המלאה בלי לשנות שום דבר בחשבון. רק קריאה עם
   `validate_only=false` מבצעת את השינוי.
2. **כתיבה כבויה ברמת השרת:** שינוי אמיתי מתאפשר רק אם השרת הופעל עם
   `GOOGLE_ADS_MCP_ENABLE_WRITES=true`. בלי המשתנה הזה אפשר רק לבדוק בקשות.
3. **הכל נוצר מושהה:** קמפיינים, קבוצות מודעות, מודעות ו-asset groups חדשים
   נוצרים במצב `PAUSED`, אלא אם מבקשים סטטוס אחר במפורש.
4. **מחיקה חסומה:** פעולת remove (בלתי הפיכה) נחסמת אלא אם מעבירים `allow_remove=true`.
5. **תקציב משותף:** שינוי תקציב שמשותף לכמה קמפיינים נחסם אלא אם מעבירים
   `allow_shared_budget=true`.

הרשאת ה-OAuth של Google Ads היא תמיד הרשאה מלאה. אין הרשאה של קריאה בלבד, וזה
נכון גם לשרת הרשמי. לכן ההגנות שלמעלה הן קו ההגנה.

## הכלים

| כלי | מה הוא עושה |
|---|---|
| `write_update_campaign` | עריכת קמפיין מכל סוג: שם, סטטוס, תאריכים, אסטרטגיית בידינג (כולל Target CPA/ROAS), רשתות, מעקב, וכל שדה אחר דרך `extra_fields` |
| `write_update_campaign_budget` | שינוי סכום התקציב (במטבע החשבון, לא ב-micros) |
| `write_set_status` | הפעלה / השהיה / מחיקה של קמפיינים, קבוצות מודעות, מודעות, asset groups ומילות מפתח (כמה בבת אחת) |
| `write_create_campaign` | יצירת קמפיין מכל סוג + תקציב + מיקומים ושפות, בבקשה אטומית אחת |
| `write_update_ad_group` | עריכת קבוצת מודעות: הצעות מחיר, יעדים, ובקרת ערוצים של Demand Gen |
| `write_create_demand_gen_ad_group` | קבוצת מודעות Demand Gen עם בחירת ערוצים (YouTube In-Stream / In-Feed / Shorts, Discover, Gmail, Display, Maps) ומיקוד גיאוגרפי ושפה |
| `write_create_demand_gen_ad` | מודעת Demand Gen: תמונות (Multi-asset) או וידאו (Video responsive) |
| `write_create_image_asset` | העלאת תמונה מ-URL כנכס (asset) |
| `write_create_youtube_video_asset` | יצירת נכס וידאו מסרטון YouTube |
| `write_mutate` | כלי כללי לכל פעולת כתיבה ב-API: asset groups ו-listing groups ב-PMax, מודעות קרוסלה ומוצר ב-Demand Gen, מילות מפתח, קהלים, הרחבות, מיקוד, תוויות, ניסויים ועוד |

`write_mutate` מקבל פעולות בפורמט JSON של ה-API (שמות שדות כמו בתיעוד). את
`update_mask` הוא בונה לבד מהשדות שהועברו, כולל ערכי false ו-0. אפשר לקשר בין
ישויות חדשות באותה בקשה בעזרת מזהים זמניים שליליים, למשל `campaignBudgets/-1`.

## התקנה

דרישות מוקדמות (זהות לשרת הרשמי, ראו
[הוראות ההתקנה שלו](https://github.com/googleads/google-ads-mcp#setup-instructions)):

- Developer token של Google Ads עם הרשאת Basic access לפחות, כדי לכתוב
  לחשבונות אמיתיים. ב-Explorer access אפשר בדרך כלל רק לקרוא.
- Google Ads API מופעל בפרויקט ב-Google Cloud.
- Application Default Credentials עם ה-scope `https://www.googleapis.com/auth/adwords`,
  או OAuth דרך משתני הסביבה של השרת הרשמי.

הרצה עם pipx, מתוך תיקייה זו:

```bash
pipx install .
```

## חיבור ל-Claude (או כל לקוח MCP)

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "google-ads-write-mcp",
      "env": {
        "GOOGLE_ADS_DEVELOPER_TOKEN": "YOUR_DEVELOPER_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "YOUR_MCC_ID_IF_ANY",
        "GOOGLE_PROJECT_ID": "YOUR_GCP_PROJECT",
        "GOOGLE_ADS_MCP_ENABLE_WRITES": "true"
      }
    }
  }
}
```

בלי `GOOGLE_ADS_MCP_ENABLE_WRITES` השרת יבדוק בקשות אבל לא יבצע אותן. מומלץ
להתחיל כך.

## דוגמאות לבקשות

- "תשהה את כל קמפייני ה-Demand Gen שה-CPA שלהם מעל 80 ₪ ב-30 הימים האחרונים"
- "תעלה את התקציב היומי של קמפיין X ל-250 ₪"
- "תעביר את קמפיין ה-PMax ל-Maximize conversion value עם ROAS יעד של 400%"
- "תבנה קמפיין Demand Gen חדש בישראל, בעברית, ב-100 ₪ ליום, עם קבוצת מודעות
  ל-YouTube Shorts ו-Discover בלבד ומודעת תמונה מהקבצים האלה"

בכל בקשה כזאת, Claude יריץ קודם בדיקה (dry run), יציג את השינוי, ויבצע אותו
רק אחרי שתאשרו.

## בדיקות

```bash
pip install -e ".[dev]" && pytest
```

הבדיקות לא קוראות ל-API. הן מוודאות שכל בקשה שכל כלי בונה עוברת פענוח
(parsing) מלא לסוגי ה-proto של API v26, ושמנגנוני הבטיחות עובדים.
