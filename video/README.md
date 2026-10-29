# סרטון מושן גרפיקס — צוות 3 מיגון ומוקד (Google Demand Gen)

סרטון לידים של 22 שניות לשירותי המיגון של team3.co.il: אזעקה, מצלמות אבטחה וחיבור למוקד מבצעי 24/7.

## קבצים מוכנים להעלאה (`out/`)
| קובץ | יחס | שימוש ב-Demand Gen |
|---|---|---|
| `team3-demandgen-portrait.mp4` | 9:16 · 1080×1920 | YouTube Shorts |
| `team3-demandgen-landscape.mp4` | 16:9 · 1920×1080 | YouTube In-Stream / In-Feed, Discover |
| `team3-demandgen-square.mp4` | 1:1 · 1080×1080 | Gmail / Discover / Feed |

H.264 + AAC, 30fps, סאונד מקורי מסונתז (ללא זכויות יוצרים של צד ג').

## מבנה הסרטון
| זמן | סצנה | טקסט |
|---|---|---|
| 0–3.4 | בית בלילה, דמות מתקרבת | מי שומר על הבית והעסק כשאתם לא שם? |
| 3.4–6.8 | חיישן, גלי התראה, הבהוב אדום | מערכת אזעקה שמזהה כל חדירה |
| 6.8–10.6 | מצלמה סורקת + צפייה חיה בנייד | מצלמות אבטחה חכמות |
| 10.6–14.6 | מוקד מרכזי מחובר לבתים, עסקים וסיור | מחוברים למוקד מבצעי 24/7 |
| 14.6–17.8 | מונה לקוחות 52,000+ / מאז 1990 | ניסיון של עשרות שנים בביטחון |
| 17.8–22 | לוגו + כפתור | מגנים עליכם מכל כיוון · לקבלת הצעת מחיר · team3.co.il · 073-8010665 |

הלוגו מופיע בפינה מהשנייה הראשונה (המלצת גוגל: מותג ב-5 השניות הראשונות).

## עריכה ורינדור מחדש
- `team3-demandgen.html` — הקומפוזיציה. פתיחה בדפדפן מנגנת תצוגה חיה (`?format=portrait|landscape|square`). כל הטקסטים בקובץ זה.
- `soundtrack.py` — מייצר את `out/soundtrack.wav`.
- `render.js` — רינדור פריים-אחר-פריים ל-MP4 (Playwright + ffmpeg):

```bash
python3 soundtrack.py && node render.js portrait && node render.js landscape && node render.js square
```

## גרסת HyperFrames (`hyperframes/`)

אותו סרטון, בנוי מחדש כפרויקט [HyperFrames](https://hyperframes.heygen.com) (HTML + GSAP, נפתח לעריכה ב-Studio / באפליקציית HyperFrames).

| קובץ | יחס |
|---|---|
| `hyperframes/renders/team3-demandgen-portrait.mp4` | 9:16 |
| `hyperframes/renders/team3-demandgen-landscape.mp4` | 16:9 |
| `hyperframes/renders/team3-demandgen-square.mp4` | 1:1 |

- `index.html` — הקומפוזיציה הראשית (9:16): רקע, 6 סצנות ופס הסאונד.
- `compositions/` — סצנה לכל קובץ: `house` (פתיח + אזעקה), `cameras`, `center` (מוקד 24/7), `trust`, `cta`, `brand` (לוגו בפינה). כל סצנה מסדרת את עצמה לפי יחס המסך (container queries), כך שאותם קבצים משמשים לשלושת הפורמטים.
- טקסטים ניתנים לעריכה כמשתנים (Variables) בכל סצנה: שורות משנה, טקסט הכפתור, האתר והטלפון.
- סאונד: פס מוזיקה (`assets/audio/bed.wav`, נוצר ב-`soundtrack.py --bed`) + אפקטים מספריית HyperFrames (Pixabay License, מותר לשימוש מסחרי — `assets/sfx/CREDITS.md`) על כל פעולה במסך.

```bash
cd hyperframes
npx hyperframes preview      # תצוגה ועריכה ב-Studio
npm run check                # בדיקות lint / layout / contrast
./render-formats.sh          # רינדור 9:16 + 16:9 + 1:1 אל renders/
```

## גרסה עם מוזיקת רקע (`out/*-music.mp4`)

אותם סרטונים מהגרסה הראשונה, עם פסקול מוזיקלי מקורי במקום פס הרקע המסונתז. האפקטים (אזעקה, מכות, צלילי התראה) נשארו כמו שהיו.

| קובץ | יחס |
|---|---|
| `out/team3-demandgen-portrait-music.mp4` | 9:16 |
| `out/team3-demandgen-landscape-music.mp4` | 16:9 |
| `out/team3-demandgen-square-music.mp4` | 1:1 |

- `music.py` — הלחן (MIDI) בסגנון קולנועי-טכנולוגי בלה מינור, ~106 BPM, מתוזמן לסצנות: פיציקטו ומתח בפתיח, אוסטינטו כלי קשת ומכת כלי נשיפה באזעקה (3.4 שנ'), גרוב עם בס, ארפג'יו ותופים מהמצלמות (6.8 שנ'), בנייה ופתרון לדו מז'ור על מסך ה-CTA (18.1 שנ'). מנוגן ב-FluidSynth עם הסאונדפונט FluidR3 GM (רישיון MIT — מותר לשימוש מסחרי).
- `mix-music.sh` — מערבב מוזיקה + אפקטים, מנרמל ל-‎-15 LUFS (שיא ‎-1.5 dBTP) ומחליף את פס הקול בשלושת הסרטונים בלי לרנדר מחדש את התמונה.
