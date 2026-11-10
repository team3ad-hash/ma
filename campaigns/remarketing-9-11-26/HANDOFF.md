# העברה לסשן חדש: Remarketing 9/11/26 (Demand Gen)

חשבון: **צוות 3 מוקד ומערכות מיגון**, מספר לקוח `4598680211`
עודכן: 10/11/2026

---

## 1. פרומפט להדבקה בסשן החדש

> הכלים של Google Ads מחוברים. אני ממשיך הקמה של קמפיין Demand Gen שחלקו כבר נוצר בחשבון 4598680211.
> קרא את `campaigns/remarketing-9-11-26/HANDOFF.md` במאגר team3ad-hash/ma (בענף claude/compassionate-cannon-xdimds) ופעל לפיו.
> כללים: לפני כל שינוי הרץ validate_only והצג לי את ה-change_items לאישור. כל מה שנוצר נוצר במצב PAUSED. אל תפעיל את הקמפיין ואל תשנה שום דבר אחר בחשבון.
> סדר העבודה: בדיקות ← שלב 1 ← שלב 2 ← סיכום עם IDs ← הצעה לשלב 3.

---

## 2. מה כבר קיים בחשבון (לא ליצור מחדש)

| אובייקט | ID | מצב |
|---|---|---|
| תקציב "Remarketing 9/11/26 - Budget" | `16024156072` | ₪100 ליום, לא משותף |
| קמפיין "Remarketing 9/11/26" | `24448494629` | PAUSED, Demand Gen, מקסום המרות (ללא יעד CPA), PRESENCE, Final URL suffix מוגדר |
| קבוצת מודעות "RMK - מיגון בית ועסק" | `205744008927` | PAUSED, `optimized_targeting_enabled=false` (נבדק) |
| מיקום: ישראל | `205744008927~2376` | ברמת קבוצת המודעות (ברמת הקמפיין ה-API דחה) |
| שפה: עברית | `205744008927~1027` | ברמת קבוצת המודעות |
| Audience "RMK 9/11/26 - מיגון 30 יום ללא לידים ולקוחות" | `364880836` | כולל את 9502190123. מחריג את 7250549130, 9053508459 ו-8572064613 |
| חיבור ה-Audience לקבוצת המודעות (טירגוט) | `205744008927~2511906229897` | |
| לוגו (קיים, BUSINESS_LOGO של החשבון) | asset `40964021471` | "לוגו שקוף.png", 417×417 |

Final URL suffix:
`utm_source=google&utm_medium=cpc&utm_campaign=remarketing_9/11/26&utm_id={campaignid}&utm_term={placement}`

---

## 3. בעיות פתוחות

1. **מגבלת תדירות לא נתמכת:** ה-API דוחה `frequency_caps` בקמפיין Demand Gen, והמשתמש אישר להקים בלעדיה. אם צריך, מגדירים ידנית בממשק.
2. **משך החברות ברשימה 9502190123:** עודכן ל-30 (ה-API החזיר הצלחה), אבל בשתי בדיקות שבוצעו מיד אחרי העדכון הוא עדיין הראה **540**.
   ← בתחילת הסשן הרץ שוב את השאילתה. אם הערך עדיין 540, דווח למשתמש והמלץ לתקן ידנית ב-Audience Manager. אל תנסה שוב בלי אישור.
3. **הרשימות ריקות:** הרשימה 9502190123 בגודל 0 (Display ו-Search). שתי רשימות ה-CRM של ההחרגה (9053508459, 8572064613) בגודל 0. הקמפיין לא יקבל חשיפות עד שהרשימה תתמלא.
4. **יעד ההמרה:** שלב 1 **אושר על ידי המשתמש** אבל לא בוצע, כי החיבור נותק. ה-checksum הקודם כבר לא תקף, לכן צריך להריץ validate מחדש. אם ה-change_items זהים למה שמופיע כאן, מותר לבצע לפי האישור הקיים. אם יש הבדל, הצג למשתמש.

---

## 4. בדיקות בתחילת הסשן (קריאה בלבד)

```
user_list: user_list.id, user_list.membership_life_span, user_list.size_for_display
  WHERE user_list.id = 9502190123

ad_group: campaign.status, ad_group.status, ad_group.optimized_targeting_enabled
  WHERE ad_group.id = 205744008927

ad_group_ad: ad_group_ad.ad.id, ad_group_ad.ad.name, ad_group_ad.status
  WHERE ad_group.id = 205744008927          (מוודא שעדיין לא נוצרו מודעות)

conversion_goal_campaign_config: goal_config_level, custom_conversion_goal
  WHERE campaign.id = 24448494629
```

---

## 5. שלב 1: יעד המרה ברמת הקמפיין (אושר, ממתין לביצוע)

קובץ: [`step1-conversion-goal.json`](step1-conversion-goal.json). אלה ה-`operations` ל-`management_mutate`, customer_id=4598680211.

- CREATE custom_conversion_goal "Sales Lead Form only - RMK 9/11/26" שמכיל רק את `909567596` (Submit lead form Thank you- Sales)
- UPDATE `conversionGoalCampaignConfigs/24448494629`, עם `goal_config_level=CAMPAIGN` ויעד ההמרה המותאם
- הערה: ב-update_mask חייבים להשתמש ב-camelCase (`goalConfigLevel,customConversionGoal`). snake_case נדחה.

---

## 6. שלב 2: מודעות (צריך אישור מהמשתמש)

קובץ: [`step2-ads.json`](step2-ads.json). כל הפעולות באצווה אחת:

| # | פעולה |
|---|---|
| 1 | asset YOUTUBE_VIDEO `FL8RVVDjBzA` (16:9) |
| 2 | asset YOUTUBE_VIDEO `mDdxwkxF29I` (9:16, Shorts) |
| 3 | asset CALL_TO_ACTION `GET_QUOTE` |
| 4 | Demand Gen Video Responsive Ad "RMK 9/11/26 - Video 16x9" במצב PAUSED, עם Final URL `…/lp2/security-remarketing/?utm_content=video_16x9` |
| 5 | Demand Gen Video Responsive Ad "RMK 9/11/26 - Video 9x16" במצב PAUSED, עם Final URL `…/lp2/security-remarketing/?utm_content=video_9x16` |

בשתי המודעות: 5 כותרות, 2 כותרות ארוכות, 5 תיאורים, שם העסק "צוות 3" והלוגו `40964021471`. כל האורכים נבדקו ועומדים במגבלות (כותרות עד 25/40, ארוכות עד 74/90, תיאורים עד 77/90).

**אם ה-validate נכשל:**
- אם GET_QUOTE לא נתמך, החלף ל-`LEARN_MORE` (לפי ההנחיה של המשתמש) והצג למשתמש.
- אם מזהה סרטון לא תקין או שהסרטון לא זמין (למשל פרטי), עצור ובקש מהמשתמש קישור מתוקן. המזהים נלקחו מהקישורים `https://youtu.be/FL8RVVDjBzA` ו-`https://youtube.com/shorts/mDdxwkxF29I`, שהגיעו מודבקים יחד.
- שמות שדות: בדוק מול metadata של `ad_group_ad` (השדה `ad_group_ad.ad.demand_gen_video_responsive_ad.*`). אל תנחש.

---

## 7. אחרי שלב 2

1. הצג סיכום של כל ה-IDs (מסעיף 2, משלב 1 ומשלב 2).
2. הצע את **שלב 3** לאישור **בנפרד**.
3. **אל תפעיל** את הקמפיין בלי אישור מפורש.

### שלב 3 (הצעה, דורש אישור נפרד): observation בקמפייני Search

קובץ: [`step3-observation-search.json`](step3-observation-search.json). מוסיף את הרשימה 9502190123 לקמפיינים "מוקד אבטחה- Search" (`15616397515`) ו"אזעקה לבית" (`14820720469`), בלי שינוי בהצעות המחיר.

**לפני כן:** בדוק את `campaign.targeting_setting.target_restrictions` של שני הקמפיינים. מצב observation מחייב `AUDIENCE` עם `bid_only=true`. אם ההגדרה שונה (targeting), **אל תשנה**. הצג למשתמש ושאל, כי שינוי כזה ישפיע על כל הקהלים בקמפיין.

---

## 8. הגדרות שנקבעו (מקור: בקשת המשתמש)

| הגדרה | ערך |
|---|---|
| סוג | Demand Gen |
| תקציב | ₪100 ליום, לא משותף |
| בידינג | מקסום המרות, ללא יעד CPA |
| המרה | 909567596 בלבד (ברמת הקמפיין) |
| מיקום ושפה | ישראל (2376) עם PRESENCE, עברית (1027) |
| מגבלת תדירות | לא נתמכת ב-API. המשתמש אישר להקים בלעדיה |
| קהל | 9502190123 בטירגוט, הרחבת קהל כבויה |
| החרגות | 7250549130, 9053508459, 8572064613 |
| CTA | GET_QUOTE, ואם לא נתמך LEARN_MORE |
