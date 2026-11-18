---
name: landing-page-skill
description: Plan, build, upgrade and maintain high-converting lead landing pages for "צוות 3 מערכות מיגון" (team3.co.il) in WordPress under /lp2/ via the Royal MCP connector, with the theme form wired to LeadIM → Priority. Use for any new or improved Team3 landing page — especially pages for Google Ads / Meta campaigns targeting a specific keyword or audience (e.g. "מצלמות אבטחה לבית", "אזעקה לעסק", "מוקד 24/7", a city or a sector), A/B variants, CRO upgrades of existing LPs, testimonials/prices/content edits, mobile fixes, and restoring an LP that broke after editing in wp-admin. Trigger on: דף נחיתה, דפי נחיתה, landing page, LP, קמפיין גוגל, מילת מפתח, המרות, lp2.
---

# Landing page skill — Team3 lp2 conversion pages

Proven build: posts **13291** (`/lp2/home-security/`, מיגון לבית) and **13292** (`/lp2/business-security/`, מיגון לעסק). Their full current code is in `assets/` and is the starting template for every new page.

**Hard rules**
- New pages are created as **draft**. Publish only when the user explicitly says so in the current turn.
- The form must stay identical to the LeadIM spec below, or leads won't reach Priority.
- Never invent prices, testimonials, ratings, certifications or numbers. Use `<span class="t3n-placeholder">[…]</span>` and list them for the user.
- Before overwriting `bottom_text` or the theme CSS, read the live value first.

---

## 1. New keyword / campaign landing page — workflow

### 1a. Brief (ask only what is missing)
- Target keyword(s) and match intent (e.g. "מצלמות אבטחה לבית" → home + cameras, transactional).
- Audience: home / business / sector (מסעדות, משרדים, מפעלים, מוסדות חינוך…) / city or region.
- Campaign channel (Google Search, PMax, Meta) and the ad headlines, so the page matches the ad copy.
- Offer and CTA (הצעת מחיר / סקר חינם / שיחת ייעוץ) and any price or promo that is approved.
- Optionally use the `keyword-research-seo` skill or Ahrefs for related terms and volumes.

### 1b. Message match & CRO checklist (Google Ads Quality Score + conversion)
- **H1 (`form_title`) contains the exact keyword** or its closest natural Hebrew form, and answers the searcher's intent in one line.
- Hero pill + lead paragraph repeat the keyword/benefit; the first screen shows H1, 3–4 benefit bullets, and the form (desktop: form on the side; mobile: form directly under the hero).
- One goal per page: every button goes to `#field1` or `tel:`. No site menu, no external links except WhatsApp/privacy.
- Sections in this order (drop what's irrelevant): trust bar → problem/"what happens when…" → how it works (3 steps) → offer/packages (keyword-specific) → why Team3 → testimonials → FAQ (objections for this keyword) → final CTA → mini footer.
- Keyword-specific FAQ and package names (e.g. camera page: resolution, night vision, phone viewing, recording retention).
- Social proof close to the form, concrete numbers (1990, 52,000 customers, 50+ patrols).
- Mobile: sticky two-button bar (primary CTA + call/WhatsApp), call pill in the header, fast load (inline SVG only, no heavy images).
- Yoast: SEO title = keyword + brand, meta description with the offer, OG tags. Campaign-only pages: set noindex if the user doesn't want them in organic search (ask).
- Slug: short Latin keyword slug, e.g. `/lp2/home-cameras/`, `/lp2/business-alarm-tel-aviv/`.
- Give the user the final URL for the ad plus a suggested UTM template: `?utm_source=google&utm_medium=cpc&utm_campaign={campaign}&utm_term={keyword}`.

### 1c. Build steps (Royal MCP)
1. `wp_create_post` → `{title, content:"", post_type:"lp2", status:"draft"}` (title = keyword-led page title). Note the new id.
2. `acf_update_field`:
   - `form` → the repeater in §2 (change only the submit button text).
   - `form_title` → the H1.
   - `banner_image` → `13047` (hidden by our CSS but expected by the template).
3. Build `bottom_text` from `assets/home-bottom_text.html` or `assets/business-bottom_text.html` (scratchpad copy, edited with a script):
   - root class `t3n-root t3n-home` (home look) or `t3n-business`; the form card title is CSS `content:` on `body:has(.t3n-…) .lpformwrap .fromwrap:before` — change it per page. For a new variant add a new modifier class (e.g. `t3n-cams`) and its own `--t3n-tag` / form-title rules.
   - rewrite hero pill, lead, bullets, sections, FAQ, final CTA, mobile bar labels for the keyword.
   - keep the `<style>` block, the testimonials, and the closing field4/field3 script.
   - push with `acf_update_field(post_id, "bottom_text", value)`.
4. Theme Custom CSS (post 8957): add the new post id to every `:is(.postid-13291,.postid-13292)` list in the "Team3 LP v2" block (`assets/theme-custom-css-block.css`). `wp_update_custom_css` replaces the whole CSS → `wp_get_custom_css` first, keep all other rules, replace only this block, keep the undo token.
5. `wp_update_seo_meta` (Yoast title/description/OG, noindex if requested).
6. Report: draft URL, what to verify (desktop + mobile, a test lead reaching LeadIM with subject "מכירות - קבלת הצעת מחיר"), list of placeholders, and that it's a draft.
7. Save the new page's final `bottom_text` into `assets/` (name by slug) and commit, so the skill keeps every page.

### 1d. Upgrading an existing LP
Read live `bottom_text` + form → audit against the checklist in 1b → propose changes (short list) → apply → report. For A/B tests, create a second draft page rather than editing the live one.

---

## 2. Form & LeadIM → Priority (do not change)
ACF `form` repeater, in this order:
1. `*שם מלא` · text · mandatory · integration `name` → `#field1`
2. `*טלפון` · tel · mandatory · `phone` → `#field2`
3. `סיווג הפונה` · select [לקוח חדש, לקוח קיים] · mandatory · `type` → `#field3`
4. `נושא הפניה` · select [מכירות - קבלת הצעת מחיר] · mandatory · `subject` → `#field4`
5. `*יישוב` · text · mandatory · `city` → `#field5` (theme renders select2 with the Israeli localities list, type-to-search, default "0")
6. submit · placeholder = button text ("שלחו לי הצעת מחיר", "תאמו לי סקר חינם"…)

Only subject **"מכירות - קבלת הצעת מחיר"** syncs to Priority; `bottom_text` must end with:
`<script>(function(){var s=document.getElementById("field4");if(s){s.value="מכירות - קבלת הצעת מחיר";}var t=document.getElementById("field3");if(t&&!t.value){t.value="לקוח חדש";}})();</script>`

Flow: theme `dynamicForm` → `/wp-json/t3/v1/sendForm` (`formExtra=webhook`) → LeadIM (`leadim('setforms',{selector:'input.lm_serfer',create:false})`) → Priority. Never replace with a custom form. Reference: `assets/leadim-form-snippet.html`.

---

## 3. Brand & content facts
- Colors: navy `#1B3282`, deep navy `#192C77`, cyan `#00ACD2`, light cyan `#5AE1FF`, ink `#171A36`, bg `#F4F6FB`. Font Assistant. Hebrew RTL.
- Sales `073-8010665` · WhatsApp `https://wa.me/972535216650` · פרופ׳ א.ד. ברגמן 2, רחובות.
- Facts: since 1990 · 52,000 customers · 6,500 employees · 50+ patrol cars and motorcycles · police-approved 24/7 control center · own technicians (not subcontractors) · Risco, Visonic, Pima, HIKVISION · LUMANA camera analytics · RFID/face-recognition access control.
- Testimonials available (edited, first name + last initial): אלכס א., לקוח צוות 3 (anonymous), משה ה., דניאל מ., בני ג., נתי ש., יניב מ. (בעל עסק – best for business pages). No star ratings unless supplied.

---

## 4. Layout technique (how bottom_text overrides the template)
- One `<style>` + `<div class="t3n-root …">` + script; all classes `t3n-`; scoped by `body:has(.t3n-root)`.
- `#wrapper` → CSS grid; theme wrappers (`.lpformwrap`, `.btmwrap`, inner `.wrap/.flex/.text`, `.t3n-root`) get `display:contents` so H1, form card and hero share rows (navy hero rows 2–4, form card right column on desktop / under hero on mobile, rest in row 5/6).
- Header 76px (64px mobile), tagline after logo via `--t3n-tag`, theme menu/phone/WhatsApp hidden, `.t3n-hphone` floating call pill, `.t3n-mbar` mobile bottom bar (two full-width buttons).
- Form labels via `.field:has(#fieldN)::before`; subject row rendered as a read-only tag; city select2 with magnifier + "הקלידו שם יישוב".
- Components ready to reuse: trust bar, 3-step boxes, packages (`t3n-pkg`, `t3n-featured`), why-grid, tiles, steps, big stats, testimonials (`t3n-quotes`, `t3n-quote`, featured `t3n-qfeat`), FAQ (`details`), final CTA, mini footer.
- Theme CSS block (`assets/theme-custom-css-block.css`): hides old layout until `.t3n-root` exists (no flash), logo fix, city border reset, animated call pill, TabNav accessibility button shift (`#tr-button-mobile`, `translate:16px 0` — keep its look, only move it), `blockquote p` reset.

## 5. Pitfalls (all happened)
1. wpautop/TinyMCE adds `<p>` and the Visual tab strips `<svg>`, `<span>`, `<script>` on save → use block `div`s, hide `p:empty`, reset nested `p`; tell the user to edit only in the **Text** tab or ask Claude.
2. A wp-admin edit tab opened before an API update overwrites it on "Update" (page "reverts": tall header, broken form, overlapping stats) → re-push the asset version with the user's intended edit applied.
3. Stats must be `display:block` with explicit line-height or numbers overlap labels.
4. Publishing via the connector may be blocked; keep drafts and let the user publish.
5. team3.co.il has a bot-check — no retry loops; use single fetches/search.

## Assets
- `assets/home-bottom_text.html`, `assets/business-bottom_text.html` — current page code (templates).
- `assets/theme-custom-css-block.css` — theme Custom CSS block.
- `assets/leadim-form-snippet.html` — form spec + city list.
- `assets/standalone-home.html`, `assets/standalone-business.html` — standalone previews for management.
