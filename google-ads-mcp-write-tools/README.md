# כלי כתיבה לשרת ה-MCP של Google Ads

הקוד כאן מוסיף לשרת `google-ads-mcp` (הקוד הפתוח של Google, ‏[googleads/google-ads-mcp](https://github.com/googleads/google-ads-mcp)) קטגוריה בשם `management` עם 13 כלי כתיבה.

**להתקנה משתמשים בקובץ אחד: `write-tools-all.patch`.** הוא כולל את כל הכלים. הקבצים `write-tools.patch` ו-`write-tools-2.patch` הם חבילות חלקיות מוקדמות, ונשמרו רק לתיעוד.

## הכלים

### כלי כללי: כל פעולה שה-API תומך בה
| כלי | מה הוא עושה |
|---|---|
| `management_mutate` | כל אחד מ-62 סוגי הפעולות של `GoogleAdsService.Mutate`, בבקשה אטומית אחת (עד 1000 פעולות): יצירה, עריכה והסרה של קמפיינים (כולל Performance Max ו-Demand Gen), קבוצות מודעות, מודעות, נכסים ושיוכם (sitelinks, callouts, שיחה), קבוצות נכסים ואותות של PMax, התאמות הצעת מחיר, קהלים ורשימות משתמשים, פעולות המרה וכללי ערך, אסטרטגיות בידינג, תוויות, רשימות משותפות, ניסויים, והגדרות חשבון |

### כלים ייעודיים (פשוטים ובטוחים יותר לפעולות נפוצות)
| כלי | מה הוא עושה |
|---|---|
| `management_create_search_campaign` | קמפיין חיפוש שלם בבקשה אחת: תקציב, קמפיין, מיקומים, שפות, מילות שליליות, קבוצת מודעות, מילות מפתח ומודעה רספונסיבית. **תמיד נוצר מושהה** |
| `management_upload_click_conversions` | ייבוא המרות אופליין מה-CRM לפי GCLID (פגישה נקבעה, עסקה נסגרה) |
| `management_update_conversion_action` | ספירה (One / Every), משך שיחה מינימלי, ראשי/משני, סטטוס |
| `management_add_shared_negative_keywords` | הוספת מילות שליליות לרשימה משותפת |
| `management_add_campaign_negative_keywords` | הוספת מילות שליליות לקמפיין |
| `management_add_keywords` | הוספת מילות מפתח לקבוצת מודעות |
| `management_update_keyword_status` | השהיה, הפעלה או מחיקה של מילות מפתח |
| `management_update_campaign_status` | השהיה או הפעלה של קמפיין |
| `management_update_campaign_budget` | שינוי תקציב יומי |
| `management_update_campaign_bidding` | Maximize Conversions עם יעד עלות להמרה, או Maximize Conversion Value עם יעד ROAS |
| `management_update_campaign_location_targeting` | "נוכחות" או "נוכחות או עניין" |
| `management_set_campaign_ad_schedule` | החלפת לוח הזמנים של קמפיין, כולל התאמות הצעת מחיר לפי שעות |

### מה לא נתמך (אין לזה פעולה ב-API של Google Ads)
- חיוב ותשלומים
- ניהול משתמשים והרשאות בחשבון
- קישור חשבונות (MCC, GA4, Merchant Center)

## איך זה שומר עליך
כל כלי עובד בשני שלבים, במנגנון `propose_and_confirm` של Google:
1. **הצעה** (`validate_only=True`): Google Ads בודק את השינוי בלי לבצע אותו. הכלי מחזיר רשימה של מה ישתנה וקוד אימות (checksum).
2. **ביצוע** (`validate_only=False` עם הקוד): קורה רק אחרי האישור שלך. אם משהו בפרמטרים שונה ממה שאושר, הקוד לא יתאים והשינוי יידחה.

הגנות נוספות:
- `management_mutate` דוחה כל משאב ששייך לחשבון אחר מזה שבבקשה.
- פעולות REMOVE מסומנות כבלתי הפיכות ברשימת השינויים.
- `create_search_campaign` יוצר את הקמפיין מושהה, כך שלא מוציא כסף עד שמפעילים אותו במפורש.

ב-claude.ai כדאי להשאיר את כל הכלים האלה על **Needs approval**.

## התקנה (ב-Cloud Shell, הכל בבת אחת)
הפקודות מניחות שהקוד נמצא ב-`~/google-ads-mcp` ושהשירות ב-Cloud Run נקרא `google-ads-mcp`.

**1. נכנסים לתיקייה ומחזירים אותה למצב נקי.** זה מוחק את החבילות החלקיות שהוחלו קודם, אם היו:
```bash
cd ~/google-ads-mcp
```
```bash
git checkout -- . && git clean -fd ads_mcp tests
```

**2. מעדכנים לגרסה האחרונה של Google:**
```bash
git pull
```

**3. מעלים את `write-tools-all.patch`** (⋮ ← Upload) **ומחילים:**
```bash
git apply --check ~/write-tools-all.patch
```
```bash
git apply ~/write-tools-all.patch
```

**4. מריצים את הבדיקות:**
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -q -e . pytest
```
```bash
pytest tests/tools/advanced_mutate_test.py tests/tools/campaign_settings_test.py tests/tools/campaign_management_test.py tests/tools_mounting_test.py tests/config_test.py
```
אם משהו נכשל, עוצרים ולא פורסים.

**5. מנקים ופורסים:**
```bash
deactivate && rm -rf .venv
```
```bash
gcloud run deploy google-ads-mcp --source . --region us-central1
```

**6. ב-claude.ai:** מתנתקים ומתחברים מחדש ל-Connector. בקבוצת Write/delete tools אמורים להופיע 17 כלים: 13 שלנו ועוד 4 של Google ל-Assets ו-Labels.

### חזרה לגרסה הקודמת
```bash
gcloud run revisions list --service google-ads-mcp --region us-central1
```
```bash
gcloud run services update-traffic google-ads-mcp --region us-central1 --to-revisions=PREVIOUS_REVISION=100
```

## מגבלות
- **מכסת פעולות:** ברמת גישה Explorer מותרות 2,880 פעולות API ביום לחשבונות אמיתיים. כל בדיקה מקדימה וכל ביצוע נספרים.
- **הקוד לא נבדק מול חשבון אמיתי.** הבדיקות משתמשות ב-mocks, כך שטעויות בשדות יתגלו בשלב ההצעה, כש-Google Ads מאמת את השינוי.
