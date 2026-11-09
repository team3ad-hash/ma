# כלי כתיבה לשרת ה-MCP של Google Ads

הקוד כאן מוסיף לשרת `google-ads-mcp` (הקוד הפתוח של Google, ‏[googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp)) קטגוריה חדשה בשם `management` עם 7 כלי כתיבה:

| כלי (כפי שיופיע ב-Claude) | מה הוא עושה |
|---|---|
| `management_update_conversion_action` | שינוי ספירה (One / Every), משך שיחה מינימלי, ראשי/משני, סטטוס |
| `management_add_shared_negative_keywords` | הוספת מילות שליליות לרשימה משותפת |
| `management_add_campaign_negative_keywords` | הוספת מילות שליליות לקמפיין אחד |
| `management_add_keywords` | הוספת מילות מפתח לקבוצת מודעות |
| `management_update_keyword_status` | השהיה / הפעלה / מחיקה של מילות מפתח |
| `management_update_campaign_status` | השהיה / הפעלה של קמפיין (אין מחיקת קמפיינים) |
| `management_update_campaign_budget` | שינוי תקציב יומי |

### חבילה 2 (`write-tools-2.patch`)
| כלי | מה הוא עושה |
|---|---|
| `management_update_campaign_bidding` | Maximize Conversions עם יעד עלות להמרה, או Maximize Conversion Value עם יעד ROAS (כולל הסרת יעד) |
| `management_update_campaign_location_targeting` | "נוכחות" או "נוכחות או עניין" |
| `management_set_campaign_ad_schedule` | החלפת לוח הזמנים של קמפיין (כולל התאמות הצעת מחיר לשעות) |

חבילה 2 מוסיפה רק שני קבצים חדשים, ודורשת שחבילה 1 כבר תהיה מותקנת.

**התקנה ב-Cloud Shell** (מתוך התיקייה `google-ads-mcp`, אחרי העלאת הקובץ דרך ⋮ ← Upload):
```bash
git apply --check ~/write-tools-2.patch
```
```bash
git apply ~/write-tools-2.patch
```
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -q -e . pytest
```
```bash
pytest tests/tools/campaign_settings_test.py tests/tools/campaign_management_test.py
```
```bash
deactivate && rm -rf .venv
```
```bash
gcloud run deploy google-ads-mcp --source . --region us-central1
```
ואז להתנתק ולהתחבר מחדש ל-Connector ב-claude.ai.

## איך זה שומר עליך
כל כלי עובד בשני שלבים, באותו מנגנון שבו Google משתמשת בכלים הקיימים (`propose_and_confirm`):
1. **הצעה**: הקריאה הראשונה רצה עם `validate_only=True`. Google Ads בודק את השינוי בלי לבצע אותו, והכלי מחזיר רשימה של מה שישתנה (כולל הערך הנוכחי) וקוד אימות (checksum).
2. **ביצוע**: רק אחרי שאתה מאשר, הקריאה השנייה עם `validate_only=False` והקוד מבצעת את השינוי. אם משהו בפרמטרים שונה ממה שאושר, הקוד לא יתאים והשינוי יידחה.

בנוסף, בהגדרות ה-Connector ב-claude.ai כדאי להשאיר את כל הכלים האלה על **Needs approval**.

## הקבצים
- `write-tools.patch` – הפאץ' המלא: הקובץ החדש, הבדיקות, ורישום הקטגוריה ב-`config.py` וב-`tools_config.yaml`. נבנה מול commit ‏`84aebf8` של המאגר הרשמי (5.11.2026).
- `ads_mcp/tools/campaign_management.py` – הכלים עצמם, אם מעדיפים להעתיק ידנית.
- `tests/tools/campaign_management_test.py` – בדיקות יחידה (עם mocks, בלי פנייה לחשבון אמיתי).

> **חשוב:** הקוד עבר רק בדיקת תחביר. בסביבה שבה נכתב לא הייתה הרשאה להתקין ולהריץ את השרת, כך שהבדיקות **לא הורצו**. צריך להריץ אותן (שלב 3) לפני הפריסה.

## העלאה לשרת (Cloud Run)

### 1. להשיג את קוד השרת
אם יש לכם כבר את התיקייה שממנה פרסתם, עבדו בה. אחרת:
```bash
git clone https://github.com/googleads/google-ads-mcp.git
```
```bash
cd google-ads-mcp
```

### 2. להחיל את הפאץ'
```bash
git apply --check /path/to/write-tools.patch
```
```bash
git apply /path/to/write-tools.patch
```
אם `--check` נכשל (הגרסה שלכם ישנה או חדשה מדי), מעתיקים ידנית:
- את `campaign_management.py` אל `ads_mcp/tools/`
- את הבדיקה אל `tests/tools/`
- מוסיפים `"management"` לרשימה `ALL_CATEGORIES` ב-`ads_mcp/config.py`
- מוסיפים `management: true` תחת `namespaces:` ב-`ads_mcp/tools_config.yaml`

הקובץ דורש את `ads_mcp/propose_and_confirm.py`, שקיים רק בגרסאות האחרונות של המאגר. אם אין אותו אצלכם, עדכנו קודם לגרסה האחרונה (`git pull`).

### 3. להריץ בדיקות
```bash
uv venv && . .venv/bin/activate && uv pip install -e . pytest
```
```bash
pytest tests/tools/campaign_management_test.py tests/tools_mounting_test.py tests/config_test.py
```

### 4. לבדוק את הגדרות השירות הקיים
השרת שלכם חושף היום רק 3 כלים. ייתכן שזה בגלל קובץ הגדרות שמגביל קטגוריות, ולא רק בגלל גרסה ישנה. בודקים את משתני הסביבה:
```bash
gcloud projects describe 425389734224 --format='value(projectId)'
```
```bash
gcloud run services describe google-ads-mcp --region us-central1 --project PROJECT_ID --format='yaml(spec.template.spec.containers[0].env)'
```
- אם מוגדר `GOOGLE_ADS_MCP_TOOLS_CONFIG`, צריך להוסיף `management: true` לקובץ שהוא מצביע עליו.
- לוודא ש-`GOOGLE_ADS_DEVELOPER_TOKEN` מוגדר, ושרמת הגישה שלו היא **Basic** או **Standard**. טוקן ברמת Test יכול לשנות רק חשבונות בדיקה.

### 5. לפרוס
```bash
gcloud run deploy google-ads-mcp --source . --region us-central1 --project PROJECT_ID
```
הפקודה בונה image חדש ושומרת את משתני הסביבה ואת ההגדרות הקיימות של השירות. שם השירות `google-ads-mcp` נלקח מכתובת ה-Connector. אם הוא שונה אצלכם, החליפו אותו.

### 6. לחבר מחדש ב-Claude
1. ב-https://claude.ai/customize/connectors פותחים את **Google Ads**.
2. מתנתקים ומתחברים מחדש, כדי שרשימת הכלים תתעדכן.
3. בודקים שמופיעה קבוצת כלים חדשה עם כלי `management_*`, ומשאירים אותם על **Needs approval**.
4. המשתמש שמתחבר צריך הרשאת **Standard** או **Admin** בחשבון Google Ads. עם הרשאת Read-only השינויים ייכשלו.

### חזרה לגרסה הקודמת
```bash
gcloud run revisions list --service google-ads-mcp --region us-central1 --project PROJECT_ID
```
```bash
gcloud run services update-traffic google-ads-mcp --region us-central1 --project PROJECT_ID --to-revisions=PREVIOUS_REVISION=100
```

## הערה על גרסת המאגר
הגרסה האחרונה של המאגר הרשמי כבר כוללת שתי קטגוריות כתיבה משלה: `labels` (תוויות) ו-`assets` (נכסים ווידאו). אם תעדכנו לגרסה האחרונה, גם הן יופיעו. אפשר לכבות אותן ב-`tools_config.yaml` עם `labels: false` ו-`assets: false`.
