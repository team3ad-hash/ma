# קטעי קוד לאופטימיזציה

הכנס קוד ב-**mu-plugin** (`wp-content/mu-plugins/speed.php`) או ב-child theme / Code Snippets —
לעולם לא בתבנית אב או בליבה. בדוק כל קטע על staging, והימנע מכפילות עם מה שתוסף הקאש כבר עושה.

## ביטול נכסים מיותרים
```php
<?php
/**
 * Plugin Name: Site Speed Tweaks
 */

// Emojis
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
remove_action( 'admin_print_styles', 'print_emoji_styles' );
add_filter( 'emoji_svg_url', '__return_false' );

// oEmbed discovery + wp-embed
remove_action( 'wp_head', 'wp_oembed_add_discovery_links' );
add_action( 'wp_footer', function () { wp_dequeue_script( 'wp-embed' ); } );

// Dashicons for logged-out visitors
add_action( 'wp_enqueue_scripts', function () {
	if ( ! is_user_logged_in() ) {
		wp_dequeue_style( 'dashicons' );
	}
} );

// jQuery Migrate (verify nothing depends on it first)
add_action( 'wp_default_scripts', function ( $scripts ) {
	if ( ! is_admin() && isset( $scripts->registered['jquery'] ) ) {
		$scripts->registered['jquery']->deps = array_diff( $scripts->registered['jquery']->deps, array( 'jquery-migrate' ) );
	}
} );
```

## Heartbeat ו-revisions
```php
add_filter( 'heartbeat_settings', function ( $settings ) {
	$settings['interval'] = 60;
	return $settings;
} );
add_action( 'init', function () {
	if ( ! is_admin() ) {
		wp_deregister_script( 'heartbeat' );
	}
}, 1 );
```
ב-`wp-config.php`:
```php
define( 'WP_POST_REVISIONS', 5 );
define( 'AUTOSAVE_INTERVAL', 120 );
define( 'DISABLE_WP_CRON', true ); // only with a real server cron: */5 * * * * wget -q -O - https://example.com/wp-cron.php?doing_wp_cron
```

## תמונות
```php
// Lower the auto-resize threshold for huge uploads (default 2560)
add_filter( 'big_image_size_threshold', fn() => 1920 );

// Default JPEG/WebP quality for generated sizes
add_filter( 'wp_editor_set_quality', fn() => 80 );

// Generate WebP sub-sizes from JPEG uploads (WP 5.8+; AVIF: 'image/avif' on 6.5+ if supported)
add_filter( 'image_editor_output_format', function ( $formats ) {
	$formats['image/jpeg'] = 'image/webp';
	return $formats;
} );

// Drop image sizes the theme never uses (check the list first: wp media image-size)
add_filter( 'intermediate_image_sizes_advanced', function ( $sizes ) {
	unset( $sizes['1536x1536'], $sizes['2048x2048'] );
	return $sizes;
} );

// Don't lazy-load the first content image (likely the LCP)
add_filter( 'wp_omit_loading_attr_threshold', fn() => 1 );
```

## Preload לתמונת LCP / פונט
```php
add_action( 'wp_head', function () {
	if ( is_front_page() ) {
		echo '<link rel="preload" as="image" href="' . esc_url( content_url( '/uploads/2026/01/hero-1200.webp' ) ) . '" fetchpriority="high">' . "\n";
	}
	echo '<link rel="preload" as="font" type="font/woff2" href="' . esc_url( get_stylesheet_directory_uri() . '/fonts/heebo-400.woff2' ) . '" crossorigin>' . "\n";
}, 1 );
```
החלף נתיבים לקבצים האמיתיים. ל-hero רספונסיבי השתמש ב-`imagesrcset` + `imagesizes`.

## WooCommerce cart fragments מחוץ לחנות
```php
add_action( 'wp_enqueue_scripts', function () {
	if ( function_exists( 'is_woocommerce' ) && ! is_woocommerce() && ! is_cart() && ! is_checkout() ) {
		wp_dequeue_script( 'wc-cart-fragments' );
	}
}, 99 );
```
אל תשתמש בזה אם יש מיני-קארט בהדר שחייב להתעדכן בכל עמוד.

## טעינה מותנית — Contact Form 7
```php
add_filter( 'wpcf7_load_js', '__return_false' );
add_filter( 'wpcf7_load_css', '__return_false' );
add_action( 'wp_enqueue_scripts', function () {
	if ( is_singular() && has_shortcode( get_post()->post_content ?? '', 'contact-form-7' ) ) {
		wpcf7_enqueue_scripts();
		wpcf7_enqueue_styles();
	}
} );
```

## .htaccess (Apache / LiteSpeed) — אם תוסף הקאש לא מגדיר כבר
```apache
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/webp "access plus 1 year"
  ExpiresByType image/avif "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
</IfModule>
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
```

## WP-CLI שימושי
```bash
wp plugin list --status=active
wp media image-size                      # registered image sizes
wp media regenerate --only-missing --yes # after changing sizes
wp transient delete --expired
wp post delete $(wp post list --post_type=revision --format=ids) --force   # backup first
wp option list --autoload=on --fields=option_name,size_bytes   # biggest ones: see the SQL query in performance-checklist.md
wp cache flush
```
