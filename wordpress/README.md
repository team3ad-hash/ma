# team3.co.il – Lighthouse optimizer (mu-plugin)

קובץ אחד: `mu-plugins/team3-lighthouse.php`.

## התקנה
1. העלו את הקובץ ל־`wp-content/mu-plugins/` (צרו את התיקייה אם אינה קיימת). פלאגין mu נטען אוטומטית – אין צורך בהפעלה.
2. גלשו לדף הבית פעם אחת כגולש לא מחובר (הבקשה הראשונה בונה את קבצי ה־CSS/JS ל־`wp-content/uploads/t3-opt/`).
3. הריצו PageSpeed Insights שוב.

ביטול מיידי: מחיקת הקובץ, או `define( 'T3LH_DISABLE', true );` ב־wp-config.php.
תצוגה ללא אופטימיזציה (מנהל מחובר): הוסיפו `?t3lh=off` לכתובת.
ניקוי מטמון: כפתור "ניקוי מטמון T3" בסרגל הניהול (מתבצע גם אוטומטית בשמירת פוסט/תפריט/הגדרות).

## מה הוא עושה
| תחום | תיקון |
|---|---|
| אנליטיקס | GTM (ודרכו Facebook, Google Ads, Hotjar, TikTok, maskyoo), New Relic ו־lead.im נשארים **בדיוק כמו קודם** – כל גולש נספר. רק ערכת Font Awesome נטענת באינטראקציה ראשונה |
| ביצועים | כל ה־JS ב־`defer`; קבצי unpkg / jsdelivr / cdnjs מוגשים מהשרת שלכם |
| ביצועים | איחוד וכיווץ CSS, פירוק שרשרת ה־`@import`, אירוח עצמי של גופן Assistant + preload, `font-display:swap` |
| ביצועים | וידאו ה־Hero (1.8MB) נטען באינטראקציה; תמונת ה־poster ב־preload עם עדיפות גבוהה |
| ביצועים | תמונות רקע JPG ← WebP של Imagify; lazy-load; הסרת emoji ו־`<img src="">` ריקים |
| ביצועים | מטמון עמודים על הדיסק (wp-content/cache/t3lh) לגולשים לא מחוברים; כותרת X-T3-Cache מציגה HIT / MISS / BYPASS |
| נגישות | viewport עם זום; aria-label לקישורי אייקונים ול־select; ניגודיות; סדר כותרות; alt; track לווידאו; target-size; פוקוס בשקופיות מוסתרות |
| שיטות מומלצות | תיקון שגיאת הסלקטור של Page scroll to id; stub ל־isotope; כותרות אבטחה (HSTS, XFO, COOP, nosniff) |
| SEO | קישור "אישור" עוגיות ניתן לסריקה; alt לתמונות |

## הגדרות (wp-config.php)
```php
define( 'T3LH_PAGE_CACHE', false );       // ביטול מטמון עמודים
define( 'T3LH_DELAY_TRACKERS', true );    // אופציונלי: תגיות אנליטיקס רק באינטראקציה (מהיר יותר, אך גולש שלא גולל/נגע לא נספר)
define( 'T3LH_DELAY_TIMEOUT', 8000 );     // יחד עם הקודם: טעינה גם אחרי 8 שנ' ללא אינטראקציה
define( 'T3LH_DELAY_VIDEO', false );      // וידאו Hero נטען מיד
define( 'T3LH_SECURITY_HEADERS', false );
```
