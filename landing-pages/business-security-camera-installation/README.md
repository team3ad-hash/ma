# התקנת מצלמות אבטחה לעסק ולמשרד — דף נחיתה lp2

- **WordPress post:** `lp2` #13138 (Draft)
- **Slug:** `/lp2/business-security-camera-installation/`
- **Source of truth:** `lp2` #13046 — "התקנת מצלמות אבטחה מקצועית לבית ולבניין" (לא שונה)

## מה כבר מוגדר ב-WordPress (דרך ה-API)

| שדה | ערך |
|---|---|
| `form_title` (H1) | התקנת מצלמות אבטחה לעסק ולמשרד |
| `banner_image` / `banner_image_mobile` | 12675 — "מצלמות אבטחה לעסק" (1200×675, אותם ממדים כמו תמונת המקור 13047) |
| `form` repeater | העתק 1:1 מ-#13046 (6 שדות, אותם placeholders / required / integration names) |
| Yoast | Title, Meta Description, OG, focus keyword |

## גוף הדף (`bottom_text`)

נכתב דרך `acf_update_field` של Royal MCP (שדה ACF מסוג wysiwyg), שמשמר `<style>` ו-`<svg>` כמו שמירה מ-wp-admin.
`bottom_text.html` כאן הוא העותק המקומי של אותו תוכן.
(הערה: `wp_update_post_meta` מסנן `<style>`/`<svg>` — לא להשתמש בו לשדה הזה.)

## הבדלים מכוונים מול דף המקור

- טקסט הטופס (`:before` / `:after` ב-CSS): "קבלו הצעה להתקנת מצלמות בעסק" / "נציג צוות 3 יחזור אליכם להתאמת הפתרון לעסק."
- נוספו שני modifiers קטנים באותו style: `.t3-cards-4` (4 כרטיסים בשורה) ו-`.t3-trust2-3` (3 פריטים בשורה).
- הוסרו כללי CSS של `.t3-offer` ו-`.t3-steps` שאינם בשימוש בדף.
