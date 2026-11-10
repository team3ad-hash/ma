# העברה לסשן חדש: Remarketing 9/11/26 (Demand Gen)

חשבון: **צוות 3 מוקד ומערכות מיגון**, מספר לקוח `4598680211`
עודכן: 10/11/2026

**סטטוס: שלבים 1, 2 ו-3 בוצעו.** הקמפיין עדיין **PAUSED** ולא הופעל. נותרו רק פעולות ידניות לפני הפעלה (סעיף 4).

---

## 1. פרומפט להדבקה בסשן חדש

> הכלים של Google Ads מחוברים. הקמפיין Demand Gen "Remarketing 9/11/26" בחשבון 4598680211 הוקם במלואו ונמצא במצב PAUSED.
> קרא את `campaigns/remarketing-9-11-26/HANDOFF.md` במאגר team3ad-hash/ma (בענף claude/exciting-pascal-ggtxpd).
> כללים: לפני כל שינוי הרץ validate_only והצג לי את ה-change_items לאישור. אל תפעיל את הקמפיין בלי אישור מפורש ואל תשנה שום דבר אחר בחשבון.
> התחל בבדיקות מסעיף 5 ודווח מה המצב של הפעולות הפתוחות בסעיף 4.

---

## 2. מה קיים בחשבון (לא ליצור מחדש)

### הקמה בסיסית (נוצר בסשן הראשון)

| אובייקט | ID | מצב |
|---|---|---|
| תקציב "Remarketing 9/11/26 - Budget" | `16024156072` | ₪100 ליום, לא משותף |
| קמפיין "Remarketing 9/11/26" | `24448494629` | **PAUSED**, Demand Gen, מקסום המרות (ללא יעד CPA), PRESENCE, Final URL suffix מוגדר |
| קבוצת מודעות "RMK - מיגון בית ועסק" | `205744008927` | PAUSED, `optimized_targeting_enabled=false` |
| מיקום: ישראל | `205744008927~2376` | ברמת קבוצת המודעות (ברמת הקמפיין ה-API דחה) |
| שפה: עברית | `205744008927~1027` | ברמת קבוצת המודעות |
| Audience "RMK 9/11/26 - מיגון 30 יום ללא לידים ולקוחות" | `364880836` | כולל את 9502190123. מחריג את 7250549130, 9053508459 ו-8572064613 |
| חיבור ה-Audience לקבוצת המודעות (טירגוט) | `205744008927~2511906229897` | |
| לוגו (קיים, BUSINESS_LOGO של החשבון) | asset `40964021471` | "לוגו שקוף.png", 417×417 |

Final URL suffix:
`utm_source=google&utm_medium=cpc&utm_campaign=remarketing_9/11/26&utm_id={campaignid}&utm_term={placement}`

### שלב 1: יעד המרה ברמת הקמפיין (בוצע 10/11/2026)

| אובייקט | ID | מצב |
|---|---|---|
| Custom conversion goal "Sales Lead Form only - RMK 9/11/26" | `6459867091` | ENABLED, מכיל רק את `909567596` (Submit lead form Thank you- Sales) |
| conversionGoalCampaignConfigs/`24448494629` | | `goal_config_level=CAMPAIGN`, `custom_conversion_goal=6459867091` (אומת בשאילתה) |

### שלב 2: מודעות (בוצע 10/11/2026)

| אובייקט | ID | מצב |
|---|---|---|
| asset YOUTUBE_VIDEO "RMK 9/11/26 - video 16x9" (`FL8RVVDjBzA`) | `438054745500` | |
| asset YOUTUBE_VIDEO "RMK 9/11/26 - video 9x16" (`mDdxwkxF29I`) | `438054781413` | |
| asset CALL_TO_ACTION "RMK 9/11/26 - CTA GET_QUOTE" | `437978630662` | GET_QUOTE נתמך, לא היה צורך ב-LEARN_MORE |
| מודעה "RMK 9/11/26 - Video 16x9" | `205744008927~831166502135` | **PAUSED**, בבדיקת מדיניות (REVIEW_IN_PROGRESS) בזמן היצירה |
| מודעה "RMK 9/11/26 - Video 9x16" | `205744008927~831166502138` | **PAUSED**, בבדיקת מדיניות (REVIEW_IN_PROGRESS) בזמן היצירה |

### שלב 3: observation בקמפייני Search (בוצע 10/11/2026)

לפני הביצוע נבדק ששני הקמפיינים מוגדרים כ-`target_restrictions` = AUDIENCE עם `bid_only=true` (observation). הצעות המחיר לא שונו.

| קמפיין | criterion חדש (רשימה 9502190123) | מצב |
|---|---|---|
| "מוקד אבטחה- Search" `15616397515` | `15616397515~2510588354358` | ENABLED, observation |
| "אזעקה לבית" `14820720469` | `14820720469~2510588354358` | ENABLED, observation |

בשני הקמפיינים כבר הייתה קודם הרשימה `9053508459` (criterion `2418015090929`). היא לא שונתה.

---

## 3. קבצי הפעולות (לתיעוד בלבד, כבר בוצעו)

- [`step1-conversion-goal.json`](step1-conversion-goal.json): בוצע. ב-update_mask חייבים להשתמש ב-camelCase (`goalConfigLevel,customConversionGoal`), כי snake_case נדחה.
- [`step2-ads.json`](step2-ads.json): בוצע.
- [`step3-observation-search.json`](step3-observation-search.json): בוצע.

**אל תריץ אותם שוב.** הרצה חוזרת תיצור כפילויות.

---

## 4. פעולות פתוחות לפני הפעלה

1. ~~משך החברות ברשימה 9502190123~~: **נבדק, אין צורך בתיקון.** זו רשימת Website visitors מבוססת כללים (flexible rule). בסוג הזה חלון הזמן נקבע בכל כלל ב-`lookback_window_days`, וכל 5 הכללים (2 הכללה ו-3 החרגה) מוגדרים על **30**. השדה `membership_life_span=540` ברמת הרשימה לא קובע כאן, ובממשק אין לו שדה לעריכה. אל תנסה לשנות אותו.
2. **הרשימות ריקות.** בבדיקה ב-10/11/2026 הרשימה 9502190123 הייתה בגודל 0 (Display ו-Search). שתי רשימות ה-CRM של ההחרגה (9053508459, 8572064613) בגודל 0. הקמפיין לא יקבל חשיפות עד שהרשימה תתמלא.
3. **מגבלת תדירות:** ה-API דוחה `frequency_caps` בקמפיין Demand Gen. המשתמש אישר להקים בלעדיה. אם צריך, מגדירים ידנית בממשק.
4. **אישור המודעות:** לוודא ש-`approval_status` של שתי המודעות הוא APPROVED.
5. **הפעלה:** רק באישור מפורש של המשתמש. מפעילים את הקמפיין `24448494629`, ואז את קבוצת המודעות ואת שתי המודעות, ולפני כל שינוי מריצים validate_only.

---

## 5. בדיקות לסשן הבא (קריאה בלבד)

```
user_list: user_list.id, user_list.size_for_display, user_list.size_for_search
  WHERE user_list.id = 9502190123        (בודקים אם הרשימה התמלאה; membership_life_span לא רלוונטי, ראה סעיף 4)

ad_group_ad: ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.status,
             ad_group_ad.policy_summary.approval_status, campaign.status
  WHERE ad_group.id = 205744008927

conversion_goal_campaign_config: goal_config_level, custom_conversion_goal
  WHERE campaign.id = 24448494629        (צפוי: CAMPAIGN, customConversionGoals/6459867091)
```

---

## 6. הגדרות שנקבעו (מקור: בקשת המשתמש)

| הגדרה | ערך |
|---|---|
| סוג | Demand Gen |
| תקציב | ₪100 ליום, לא משותף |
| בידינג | מקסום המרות, ללא יעד CPA |
| המרה | 909567596 בלבד (ברמת הקמפיין, דרך custom goal `6459867091`) |
| מיקום ושפה | ישראל (2376) עם PRESENCE, עברית (1027) |
| מגבלת תדירות | לא נתמכת ב-API. המשתמש אישר להקים בלעדיה |
| קהל | 9502190123 בטירגוט, הרחבת קהל כבויה |
| החרגות | 7250549130, 9053508459, 8572064613 |
| CTA | GET_QUOTE (נתמך) |
| Observation ב-Search | 9502190123 ב-15616397515 וב-14820720469 |
