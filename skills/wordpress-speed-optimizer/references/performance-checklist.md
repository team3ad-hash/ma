# צ'קליסט ביצועים לוורדפרס

## תוכן
1. ספי Core Web Vitals ומה משפיע על כל מדד
2. שרת ו-TTFB
3. קאשינג עמודים
4. CSS ו-JavaScript
5. פונטים
6. סקריפטים חיצוניים (צד שלישי)
7. מסד נתונים ו-backend
8. CDN
9. בוני עמודים ותבניות
10. WooCommerce
11. תוספים — איך לזהות כבדים

---

## 1. ספי Core Web Vitals (אחוזון 75, נתוני שדה)
| מדד | טוב | צריך שיפור | גרוע | מה בדרך כלל אשם בוורדפרס |
|---|---|---|---|---|
| LCP | ≤2.5s | ≤4s | >4s | TTFB גבוה, תמונת hero כבדה/lazy, CSS חוסם, סליידר |
| INP | ≤200ms | ≤500ms | >500ms | JS כבד של בוני עמודים/תוספים, סקריפטים חיצוניים, DOM ענק |
| CLS | ≤0.1 | ≤0.25 | >0.25 | תמונות בלי מידות, פונטים (FOUT), באנרי עוגיות, פרסומות |
| TTFB | ≤0.8s | ≤1.8s | >1.8s | אין page cache, אחסון חלש, PHP ישן, שאילתות כבדות |

TBT במעבדה הוא המדד המקורב ל-INP.

## 2. שרת ו-TTFB
- PHP 8.2+ (8.1 לפחות), OPcache פעיל.
- Object cache (Redis/Memcached) — חשוב ב-WooCommerce, אתרי חברות ואתרים עם משתמשים מחוברים.
- HTTP/2 או HTTP/3, דחיסת Brotli/Gzip.
- אחסון שיתופי זול עם TTFB > 1s גם אחרי קאש — המלצה כנה להחליף אחסון היא חלק מהעבודה.
- כבה `WP_DEBUG` בפרודקשן, ובדוק error log (שגיאות חוזרות מאטות).
- WP-Cron: באתרים עם תנועה החלף ל-cron אמיתי של השרת (`DISABLE_WP_CRON`).

## 3. קאשינג עמודים
בחר **תוסף אחד** לפי השרת:
- LiteSpeed server → **LiteSpeed Cache**.
- אחסון מנוהל (Kinsta, WP Engine, SiteGround, Cloudways) → הקאש של האחסון + תוסף אופטימיזציה
  בלי page cache (למשל Perfmatters / FlyingPress / WP Rocket עם page cache כבוי אם האחסון דורש).
- Apache/Nginx רגיל → **WP Rocket** / **FlyingPress** / **W3 Total Cache** / **Cache Enabler**.

הגדרות בסיס: page cache לדסקטופ ומובייל, preload לקאש (sitemap), החרגת עגלה/checkout/חשבון,
browser cache headers לקבצים סטטיים (שנה).

## 4. CSS ו-JavaScript
בסדר סיכון עולה:
1. **Minify** CSS/JS — סיכון נמוך.
2. **Combine** — לרוב מיותר ב-HTTP/2, ולעיתים מזיק. השאר כבוי.
3. **Defer JS** — סיכון בינוני. jQuery לפעמים צריך להחריג.
4. **Delay JS until interaction** — רווח עצום ל-TBT/INP, סיכון גבוה. החרג: סקריפטים של
   תפריט מובייל, סליידר above-the-fold, באנר עוגיות, Woo cart fragments כשצריך.
5. **Remove unused CSS / Critical CSS** — רווח גדול ל-LCP, סיכון גבוה. בדוק כל סוג עמוד,
   מצבי hover, תפריט מובייל, פופאפים.
- **טעינה מותנית של נכסים** (Perfmatters Script Manager / Asset CleanUp / קוד): לא לטעון
  Contact Form 7 / WooCommerce / סליידרים בעמודים שלא משתמשים בהם.
- בטל emojis, embeds, dashicons למבקרים לא מחוברים, jQuery Migrate אם לא נדרש
  (ראה code-snippets).

## 5. פונטים
- אחסן Google Fonts מקומית (גם מהירות וגם GDPR/פרטיות).
- רק המשקלים בשימוש בפועל (לרוב 400/600/700), WOFF2 בלבד, subset לעברית+לטינית.
- `font-display: swap` + preload לפונט העיקרי בלבד.
- Font Awesome / ספריות אייקונים מלאות — להחליף ב-SVG או לטעון subset.
- Elementor: Settings → Performance → "Load Google Fonts locally"; לכבות פונטים לא בשימוש.

## 6. סקריפטים חיצוניים
אנליטיקס, פיקסלים (Meta, TikTok), Hotjar, צ'אטים (WhatsApp/Tawk), reCAPTCHA, YouTube:
- איחוד דרך GTM אחד במקום 5 תגיות נפרדות.
- Delay עד אינטראקציה לצ'אטים ולפיקסלים לא קריטיים (תאם עם מנהל הקמפיינים — עיכוב
  פיקסל עלול להוריד אירועי PageView ממבקרים שלא מבצעים אינטראקציה).
- reCAPTCHA רק בעמודים עם טופס, או Turnstile/Honeypot.
- `preconnect` לדומיינים קריטיים בלבד (2–3).

## 7. מסד נתונים ו-backend
- ניקוי: revisions (והגבלה `WP_POST_REVISIONS`), טיוטות אוטומטיות, פח, spam, transients שפגו.
- **autoload**: בדוק את סך האופציות ב-autoload (יעד < 800KB). תוספים שהוסרו משאירים זבל:
  ```sql
  SELECT option_name, LENGTH(option_value) AS size FROM wp_options
  WHERE autoload IN ('yes','on','auto-on','auto') ORDER BY size DESC LIMIT 20;
  ```
- Heartbeat API — להגביל ל-60s או לכבות ב-frontend.
- כלים: WP-Optimize / Advanced Database Cleaner / WP-CLI (`wp transient delete --expired`).
- Query Monitor לאיתור שאילתות איטיות ו-hooks כבדים.
- **גבה את המסד לפני כל ניקוי.**

## 8. CDN
- Cloudflare (חינם) — DNS + קאש סטטי; APO לוורדפרס משתלם ל-HTML caching.
- BunnyCDN / QUIC.cloud — זולים ויעילים, כוללים אופטימיזציית תמונות.
- לקהל ישראלי — וודא שיש נקודת נוכחות קרובה (תל אביב / אירופה) ושה-TTFB אכן משתפר.

## 9. בוני עמודים ותבניות
**Elementor**: Settings → Features: הפעל "Optimized DOM Output", "Improved Asset Loading",
"Improved CSS Loading", "Inline Font Icons", "Lazy Load Background Images"; כבה Font Awesome 4 shim;
CSS Print Method = External file; הימנע מקונטיינרים מקוננים מיותרים (DOM גדול → INP גרוע).
**Divi**: Theme Options → Performance — הפעל Dynamic Modules/CSS/JS, Critical CSS, Defer jQuery.
תבניות כבדות (multipurpose עם 30 תוספים מובנים) — לשקול מעבר ל-GeneratePress / Kadence /
Astra / Blocksy / תבנית בלוקים.

## 10. WooCommerce
- `wc-cart-fragments` — לטעון רק כשיש עגלה בהדר/מיני-קארט; אחרת לבטל בעמודים שאינם חנות.
- להחריג עגלה/checkout/חשבון מקאש ומ-Delay JS.
- HPOS (High-Performance Order Storage) פעיל.
- Object cache כמעט חובה.
- חיפוש מוצרים/פילטרים כבדים — לשקול פתרון ייעודי (FiboSearch, אינדקס).
- להגביל מוצרים בעמוד קטגוריה ותמונות גלריה שנטענות מראש.

## 11. תוספים — איך לזהות כבדים
- Query Monitor: זמן לפי רכיב (component).
- השבתה הדרגתית על staging ומדידה.
- חשודים נפוצים: תוספי סליידרים, social share, related posts שמריצים שאילתות כבדות,
  סטטיסטיקות מקומיות (שכותבות למסד בכל צפייה), תוספי אבטחה עם סריקות תכופות,
  תוספי "הכל-באחד" שלא בשימוש.
- מספר תוספים לבדו אינו בעיה — איכות התוספים היא הבעיה.
