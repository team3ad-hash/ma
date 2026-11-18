---
name: team3-landing-pages
description: Build, fix or update lead-generation landing pages for "צוות 3 מערכות מיגון" (team3.co.il) — home and business security — in WordPress under /lp2/ via the Royal MCP connector, with the theme's dynamic form wired to LeadIM → Priority. Use whenever the user asks for a new Team3 landing page, a design/mobile fix on the lp2 pages (13291 home, 13292 business), testimonials/prices/content changes on them, the accessibility widget or call button position, or restoring a page that broke after editing in wp-admin.
---

# Team3 landing pages (lp2) — build & maintain

Everything here was learned building posts **13291** (`/lp2/home-security/`, מיגון לבית) and **13292** (`/lp2/business-security/`, מיגון לעסק). Both are **drafts**. Never publish (status→publish) unless the user explicitly says so in the current turn.

## Brand
- Colors: navy `#1B3282` / deep navy `#192C77`, cyan `#00ACD2`, light cyan `#5AE1FF`, ink `#171A36`, bg `#F4F6FB`. Font: Assistant. RTL Hebrew.
- Sales phone `073-8010665`, WhatsApp `https://wa.me/972535216650`, address פרופ׳ א.ד. ברגמן 2, רחובות.
- Facts used on pages: since 1990, 52,000 customers, 6,500 employees, 50+ patrol cars, police-approved 24/7 control center, brands Risco/Visonic/Pima/HIKVISION, LUMANA analytics.
- Keep `[placeholder]` spans (class `t3n-placeholder`) for anything unconfirmed (prices, insurance claims) — never invent prices or testimonials.

## How the lp2 template works
- Post type `lp2`, theme `team3`. The page = theme header + `.lpformwrap` (H1 = ACF `form_title`, form from ACF `form` repeater) + `.btmwrap` (ACF `bottom_text`, wysiwyg) + footer.
- ACF fields set per page: `form_title`, `form` (repeater), `banner_image` (13047, hidden by CSS), `bottom_text`. Yoast title/description/OG via `wp_update_seo_meta`.
- **Form repeater (must stay exactly like this — LeadIM/Priority depend on it):**
  1. `*שם מלא` text, mandatory, integration `name` → `#field1`
  2. `*טלפון` tel, mandatory, integration `phone` → `#field2`
  3. `סיווג הפונה` select [לקוח חדש, לקוח קיים], mandatory, `type` → `#field3`
  4. `נושא הפניה` select [מכירות - קבלת הצעת מחיר], mandatory, `subject` → `#field4`
  5. `*יישוב` mandatory, `city` → `#field5` (theme renders select2 with the Israeli localities list, default value "0")
  6. submit (placeholder = button text, e.g. "שלחו לי הצעת מחיר" / "תאמו לי סקר חינם")
- Only leads whose subject is **"מכירות - קבלת הצעת מחיר"** sync to Priority. The bottom_text ends with a script that forces it:
  `<script>(function(){var s=document.getElementById("field4");if(s){s.value="מכירות - קבלת הצעת מחיר";}var t=document.getElementById("field3");if(t&&!t.value){t.value="לקוח חדש";}})();</script>`
- Submission: theme `dynamicForm` → `/wp-json/t3/v1/sendForm` with `formExtra=webhook` → LeadIM (`leadim('setforms',{selector:'input.lm_serfer',create:false})`) → Priority. Don't build a custom form. Reference snippet: `assets/leadim-form-snippet.html`.

## Page layout technique (bottom_text)
- `bottom_text` holds one `<style>` + `<div class="t3n-root t3n-home|t3n-business">…</div>` + the script. All classes prefixed `t3n-`; everything scoped with `body:has(.t3n-root)`.
- `#wrapper` becomes a CSS grid; theme wrappers (`.lpformwrap`, `.btmwrap`, …, `.t3n-root`) get `display:contents` so the H1, form card and our hero pieces share grid rows (hero navy bg row 2–4, form card right column on desktop, below hero on mobile; rest in row 5/6).
- Theme header trimmed to 76px (64px mobile) with a tagline after the logo via `--t3n-tag`; theme menu/WhatsApp/phone buttons hidden; floating `.t3n-hphone` call button; mobile sticky bottom bar `.t3n-mbar` (two full-width buttons).
- Form labels are CSS `::before` on `.field:has(#fieldN)`; subject row styled as a read-only tag; city select2 gets a magnifier and "הקלידו שם יישוב" placeholder.
- Current full versions: `assets/home-bottom_text.html`, `assets/business-bottom_text.html`. Start any new page from one of them.
- Testimonials: `.t3n-quotes` grid of `figure.t3n-quote` (quote mark, blockquote, avatar initial `.t3n-av`, `.t3n-who` name + optional `small`); business page has a featured `.t3n-qfeat` card. Horizontal scroll-snap on mobile. Names as first name + last initial; no stars unless the user supplies ratings.

## Theme Custom CSS (post 8957)
- `wp_update_custom_css` **replaces the entire CSS**. Always `wp_get_custom_css` first, keep all other site rules (gallery slider, LP 13231/13046 block…), and replace only the "Team3 LP v2" block — `assets/theme-custom-css-block.css`. Add new post ids to the `:is(.postid-…)` lists.
- That block handles: hiding the old layout until `.t3n-root` exists (no 2-second flash of the old LP design), logo sizing, city field border reset, call-button pill with ring/wiggle animation on mobile, accessibility widget shift, and `blockquote p` reset.
- Accessibility widget (TabNav) on mobile: `#tr-button-mobile` / `button.tr-button.small-viewport`; shift it with `translate:16px 0` (user wanted it kept as-is, just moved right — no restyling, keep the bottom bar full width).
- Each update returns a 72h undo token (`mcp_undo_last_operation`).

## Pitfalls (all hit in practice)
1. **wpautop/TinyMCE**: the wysiwyg adds `<p>` around inline content, and saving in wp-admin's *Visual* tab strips `<svg>`, `<span>`s and `<script>`. Use block `div`s instead of loose inline elements, hide `p:empty`, reset `blockquote p`. Tell the user to edit only in the **Text** tab, refresh the edit screen first, or ask Claude to edit.
2. **Stale edit tab**: a wp-admin tab opened before our API updates will overwrite them on "Update". If a page "reverts" (tall header, broken form, overlapping stats), compare `wp_get_post_meta(bottom_text)` with the asset file and re-push the asset (applying the user's intended small edit).
3. Before overwriting `bottom_text`, read the live value to make sure the user hasn't edited it since.
4. Stats overlapping labels: `b`/`span` inside stats must be `display:block` with explicit line-heights.
5. Publishing was blocked by the safety classifier once — keep drafts; a page that got published by mistake was reverted with undo.
6. team3.co.il has a bot-check; don't loop-retry around it. Use single fetches/search.

## Workflow for a change
1. Read the live `bottom_text` (and custom CSS if touching it).
2. Edit a local copy (scratchpad) with a script; keep the asset files in this skill in sync.
3. Push with `acf_update_field(post_id, "bottom_text", value)` — full value, unminified-safe.
4. Report what changed, that pages are still drafts, and what the user should check on mobile/desktop.

## Other deliverables made
- Standalone HTML previews for management: `assets/standalone-home.html`, `assets/standalone-business.html` (form is a non-submitting mock).
- Design canvas artifact and management email were produced in chat; recreate on request.
