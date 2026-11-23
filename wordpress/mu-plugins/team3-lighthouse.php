<?php
/**
 * Plugin Name: Team3 – Lighthouse Optimizer
 * Description: Performance, accessibility, best-practices and SEO fixes for team3.co.il (Lighthouse report 2026-11-22). Install via Plugins → Add New → Upload (ZIP), or drop into wp-content/mu-plugins/.
 * Version:     1.5.0
 * Author:      Team3
 *
 * Every feature can be switched off from wp-config.php, for example:
 *   define( 'T3LH_DISABLE', true );            // turn the whole plugin off
 *   define( 'T3LH_PAGE_CACHE', false );        // no full-page cache
 *   define( 'T3LH_DELAY_TRACKERS', true );     // OPTIONAL: load analytics/ads only on first interaction (faster, but visitors who never
 *                                              // scroll/touch are not counted). Default false = analytics load exactly as before.
 *   define( 'T3LH_GTM_AFTER_LOAD', false );    // GTM starts 3.5s after the load event or at the first interaction
 *                                              // (thank-you pages: immediately). false = GTM exactly as the theme prints it.
 *   define( 'T3LH_GTM_DELAY', 0 );             // ms after load before GTM starts (default 3500).
 *   define( 'T3LH_DELAY_TIMEOUT', 8000 );      // with T3LH_DELAY_TRACKERS: also load after 8s without interaction
 *   define( 'T3LH_DELAY_VIDEO', false );       // let the hero video download immediately
 *   define( 'T3LH_SECURITY_HEADERS', false );  // no extra security headers
 *
 * Add ?t3lh=off to any URL (as a logged-in admin) to see the page without the optimizer.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
if ( defined( 'T3LH_DISABLE' ) && T3LH_DISABLE ) {
	return;
}

final class T3_Lighthouse {

	const VERSION   = '1.5.0';
	const OPT_DIR   = 't3-opt';

	/**
	 * Analytics / ads / call-tracking / monitoring. By default these are left EXACTLY as the theme prints them
	 * (same position, same async loading) so every visitor is counted as before.
	 * Only with T3LH_DELAY_TRACKERS = true are they moved to the first interaction.
	 */
	const ANALYTICS_PATTERNS = array(
		'googletagmanager.com',
		'google-analytics.com',
		'gtag(',
		'connect.facebook.net',
		'fbq(',
		'hotjar',
		'NREUM',
		'newrelic',
		'nr-data.net',
		'lead.im',
		'leadim',
		'maskyoo',
		'tiktok',
		'clarity.ms',
		'doubleclick',
	);

	/** Non-analytics scripts that always wait for the first interaction. */
	const DELAY_PATTERNS = array(
		// Font Awesome kit (FA 5/6 webfonts, used only by small footer-menu bullets).
		'b9bf5f99bd.js',
		'kit.fontawesome.com',
	);

	/** Scripts that load once the page has finished loading (not tied to interaction). */
	const IDLE_PATTERNS = array(
		'widget.tabnav.com', // accessibility widget – kept available without interaction.
	);

	/** CDN hosts whose files are copied to the local server. */
	const LOCALIZE_HOSTS = array( 'unpkg.com', 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com' );

	private static $lang = 'he';

	/* ------------------------------------------------------------------ */
	/* Bootstrap                                                          */
	/* ------------------------------------------------------------------ */

	public static function boot() {
		self::maybe_serve_cached_page();

		add_action( 'init', array( __CLASS__, 'remove_bloat' ) );
		add_action( 'send_headers', array( __CLASS__, 'security_headers' ) );
		add_action( 'send_headers', array( __CLASS__, 'cache_status_header' ) );
		add_action( 'template_redirect', array( __CLASS__, 'start_buffer' ), PHP_INT_MAX );

		foreach ( array( 'save_post', 'deleted_post', 'trashed_post', 'edit_term', 'delete_term', 'wp_update_nav_menu', 'customize_save_after', 'switch_theme', 'activated_plugin', 'deactivated_plugin', 'upgrader_process_complete', 'acf/save_post', 'update_option_sidebars_widgets', 'update_option_wp_page_for_privacy_policy' ) as $hook ) {
			add_action( $hook, array( __CLASS__, 'purge_all' ) );
		}
		add_action( 'updated_option', array( __CLASS__, 'maybe_purge_on_option' ), 10, 1 );
		add_action( 'admin_bar_menu', array( __CLASS__, 'admin_bar' ), 100 );
		add_action( 'admin_post_t3lh_purge', array( __CLASS__, 'handle_purge_request' ) );
	}

	public static function remove_bloat() {
		remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
		remove_action( 'wp_print_styles', 'print_emoji_styles' );
		remove_action( 'wp_enqueue_scripts', 'wp_enqueue_emoji_styles' );
		remove_action( 'wp_footer', 'wp_print_emoji_detection_script' );
		remove_filter( 'the_content_feed', 'wp_staticize_emoji' );
		remove_filter( 'comment_text_rss', 'wp_staticize_emoji' );
		remove_filter( 'wp_mail', 'wp_staticize_emoji_for_email' );
		add_filter( 'emoji_svg_url', '__return_false' );
		remove_action( 'wp_head', 'rsd_link' );
		remove_action( 'wp_head', 'wlwmanifest_link' );
		remove_action( 'wp_head', 'wp_generator' );
	}

	public static function security_headers() {
		if ( is_admin() || headers_sent() || ( defined( 'T3LH_SECURITY_HEADERS' ) && ! T3LH_SECURITY_HEADERS ) ) {
			return;
		}
		header( 'X-Content-Type-Options: nosniff' );
		header( 'X-Frame-Options: SAMEORIGIN' );
		header( 'Referrer-Policy: strict-origin-when-cross-origin' );
		if ( is_ssl() ) {
			header( 'Strict-Transport-Security: max-age=31536000' );
		}
	}

	private static function is_optimizable_request() {
		if ( is_admin() || wp_doing_ajax() || wp_doing_cron() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) || ( defined( 'WP_CLI' ) && WP_CLI ) ) {
			return false;
		}
		if ( is_feed() || is_robots() || is_trackback() || is_customize_preview() || is_preview() ) {
			return false;
		}
		if ( isset( $_GET['t3lh'] ) && 'off' === $_GET['t3lh'] && current_user_can( 'manage_options' ) ) { // phpcs:ignore WordPress.Security.NonceVerification
			return false;
		}
		$method = isset( $_SERVER['REQUEST_METHOD'] ) ? strtoupper( $_SERVER['REQUEST_METHOD'] ) : 'GET';
		return in_array( $method, array( 'GET', 'HEAD' ), true );
	}

	public static function start_buffer() {
		if ( ! self::is_optimizable_request() ) {
			return;
		}
		ob_start( array( __CLASS__, 'end_buffer' ) );
	}

	public static function end_buffer( $html ) {
		if ( ! is_string( $html ) || strlen( $html ) < 255 || false === stripos( $html, '<html' ) || false === stripos( $html, '</head>' ) ) {
			return $html;
		}
		try {
			$out = self::process( $html );
		} catch ( \Throwable $e ) {
			error_log( 'T3 Lighthouse optimizer: ' . $e->getMessage() );
			return $html;
		}
		self::maybe_store_cached_page( $out );
		return $out;
	}

	/* ------------------------------------------------------------------ */
	/* HTML pipeline                                                      */
	/* ------------------------------------------------------------------ */

	public static function process( $html ) {
		if ( preg_match( '#<html[^>]*\blang="([a-z]{2})#i', $html, $m ) ) {
			self::$lang = strtolower( $m[1] );
		}

		$html = self::fix_viewport( $html );
		$html = self::fix_known_js_bugs( $html );
		$html = self::remove_emoji( $html );
		$html = self::process_scripts( $html );
		$html = self::process_styles( $html );
		$html = self::process_video( $html );

		// Markup fixes must never touch JavaScript/CSS source → mask those blocks first.
		$html = self::mask( $html );
		$html = self::process_images( $html );
		$html = self::fix_links( $html );
		$html = self::fix_form_controls( $html );
		$html = self::fix_headings( $html );
		$html = self::unmask( $html );

		$html = self::inject_head( $html );
		$html = self::inject_footer( $html );
		return $html;
	}

	private static $masks = array();

	private static function mask( $html ) {
		self::$masks = array();
		return preg_replace_callback(
			'#<(script|style|noscript)\b[^>]*>.*?</\1>#is',
			static function ( $m ) {
				$k                 = "\x1AT3LH" . count( self::$masks ) . "\x1A";
				self::$masks[ $k ] = $m[0];
				return $k;
			},
			$html
		);
	}

	private static function unmask( $html ) {
		return self::$masks ? strtr( $html, self::$masks ) : $html;
	}

	/** Allow pinch-zoom (a11y: meta-viewport). */
	private static function fix_viewport( $html ) {
		return preg_replace_callback(
			'#<meta\s+name=["\']viewport["\'][^>]*>#i',
			static function () {
				return '<meta name="viewport" content="width=device-width, initial-scale=1">';
			},
			$html,
			1
		);
	}

	private static function fix_known_js_bugs( $html ) {
		// "Page scroll to id" option was saved truncated ("a[data-fancybox=") → jQuery syntax error in console.
		$html = str_replace( 'a[data-fancybox=","', 'a[data-fancybox]","', $html );
		return $html;
	}

	private static function remove_emoji( $html ) {
		$html = preg_replace( '#<script[^>]*id=["\']wp-emoji-settings["\'][^>]*>.*?</script>\s*#is', '', $html );
		$html = preg_replace( '#<script type="module">(?:(?!</script>).)*?wp-emoji-loader(?:(?!</script>).)*</script>\s*#is', '', $html );
		$html = preg_replace( '#<style[^>]*id=["\']wp-emoji-styles-inline-css["\'][^>]*>.*?</style>\s*#is', '', $html );
		return $html;
	}

	private static function matches_any( $haystack, array $needles ) {
		foreach ( $needles as $n ) {
			if ( false !== stripos( $haystack, $n ) ) {
				return true;
			}
		}
		return false;
	}

	/**
	 * - Third-party trackers (GTM → Facebook/Google Ads/Hotjar/TikTok…, New Relic, lead.im, FA kit) → run on first interaction.
	 * - Every other external script → defer (CDN copies served locally).
	 * - Inline scripts that come after jQuery → deferred too, so execution order is preserved.
	 */
	private static function process_scripts( $html ) {
		$seen_deferred = false;

		return preg_replace_callback(
			'#<script\b([^>]*)>(.*?)</script>#is',
			static function ( $m ) use ( &$seen_deferred ) {
				$attrs = $m[1];
				$body  = $m[2];
				$type  = '';
				if ( preg_match( '#\btype=["\']([^"\']*)["\']#i', $attrs, $t ) ) {
					$type = strtolower( trim( $t[1] ) );
				}
				if ( '' !== $type && ! in_array( $type, array( 'text/javascript', 'application/javascript' ), true ) ) {
					return $m[0]; // JSON-LD, speculationrules, modules, templates…
				}
				if ( false !== strpos( $attrs, 'data-t3lh' ) ) {
					return $m[0];
				}

				$src = '';
				if ( preg_match( '#(?<![\w-])src=["\']([^"\']+)["\']#i', $attrs, $s ) ) {
					$src = html_entity_decode( $s[1] );
				}
				$clean_attrs = trim( preg_replace( '#\s*(?<![\w-])(type|async|defer|data-wp-strategy)(=(["\'])[^"\']*\3)?#i', '', $attrs ) );

				$probe = '' !== $src ? $src : $body;

				// 0. Analytics: untouched by default (counted exactly as before).
				if ( self::matches_any( $probe, self::ANALYTICS_PATTERNS ) ) {
					if ( ! self::delay_trackers() ) {
						// Optional: start GTM right after the page "load" event, so its ~750 KB of tags
						// (Facebook, TikTok, Hotjar…) no longer compete with the hero image (LCP).
						if ( self::gtm_after_load() && '' === $src && false !== strpos( $body, 'googletagmanager.com/gtm.js' ) ) {
							return '<script type="t3lh/load" ' . $clean_attrs . '>' . $body . '</script>';
						}
						return $m[0];
					}
					$probe = 'b9bf5f99bd.js'; // force the "delay" branch below.
				}

				// 1. Interaction-delayed third parties.
				if ( self::matches_any( $probe, self::DELAY_PATTERNS ) || self::matches_any( $probe, self::IDLE_PATTERNS ) ) {
					$kind = self::matches_any( $probe, self::IDLE_PATTERNS ) ? 't3lh/idle' : 't3lh/delay';
					if ( '' !== $src ) {
						$clean_attrs = trim( preg_replace( '#(?<![\w-])src=(["\'])[^"\']+\1#i', '', $clean_attrs ) );
						return '<script type="' . $kind . '" data-src="' . esc_attr( $src ) . '" ' . $clean_attrs . '></script>';
					}
					return '<script type="' . $kind . '" ' . $clean_attrs . '>' . $body . '</script>';
				}

				// 2. External scripts → defer, CDN files served from own domain.
				if ( '' !== $src ) {
					$local = self::localize_asset( $src, 'js' );
					if ( $local ) {
						$clean_attrs = preg_replace( '#(?<![\w-])src=(["\'])[^"\']+\1#i', 'src="' . esc_url( $local ) . '"', $clean_attrs );
						$clean_attrs = preg_replace( '#\s*\bcrossorigin(=(["\'])[^"\']*\2)?#i', '', $clean_attrs );
					}
					$seen_deferred = true;
					return '<script ' . trim( $clean_attrs ) . ' defer></script>';
				}

				// 3. Inline scripts after the first deferred script keep their order by becoming deferred data: scripts.
				if ( $seen_deferred && '' !== trim( $body ) ) {
					return '<script ' . ( '' !== $clean_attrs ? $clean_attrs . ' ' : '' ) . 'defer src="data:text/javascript;base64,' . base64_encode( $body ) . '"></script>';
				}
				return $m[0];
			},
			$html
		);
	}

	/**
	 * GTM starts right after the page "load" event (default on; define T3LH_GTM_AFTER_LOAD false to disable).
	 * Thank-you pages keep the original immediate GTM so no conversion can be lost.
	 */
	private static function gtm_after_load() {
		if ( defined( 'T3LH_GTM_AFTER_LOAD' ) && ! T3LH_GTM_AFTER_LOAD ) {
			return false;
		}
		$uri = isset( $_SERVER['REQUEST_URI'] ) ? rawurldecode( (string) $_SERVER['REQUEST_URI'] ) : '';
		return false === stripos( $uri, 'thank' ) && false === strpos( $uri, 'תודה' );
	}

	private static function delay_trackers() {
		return defined( 'T3LH_DELAY_TRACKERS' ) && T3LH_DELAY_TRACKERS;
	}

	/* ---------------------------- CSS --------------------------------- */

	/**
	 * Combines consecutive <link rel=stylesheet> tags in <head> into one local, minified file
	 * (keeping cascade order: groups are split by inline <style> blocks), resolves @import chains,
	 * self-hosts Google Fonts and forces font-display:swap.
	 */
	/** On a new plugin version: drop old bundles, CDN copies and cached pages once. */
	private static function maybe_reset_assets() {
		if ( get_option( 't3lh_assets_ver' ) === self::VERSION ) {
			return;
		}
		update_option( 't3lh_assets_ver', self::VERSION, true );
		foreach ( (array) glob( self::opt_dir() . '/css/*.css' ) as $f ) {
			@unlink( $f ); // phpcs:ignore
		}
		$index = get_option( 't3lh_assets', array() );
		foreach ( array_keys( $index ) as $k ) {
			if ( 0 === strpos( $k, 'css_' ) ) {
				unset( $index[ $k ] );
			}
		}
		update_option( 't3lh_assets', $index, false );
		self::purge_all();
	}

	private static function process_styles( $html ) {
		self::maybe_reset_assets();
		$head_end = stripos( $html, '</head>' );
		$head     = substr( $html, 0, $head_end );
		$rest     = substr( $html, $head_end );

		if ( ! preg_match_all( '#<link\b[^>]*rel=["\']stylesheet["\'][^>]*>|<style\b[^>]*>.*?</style>#is', $head, $mm, PREG_OFFSET_CAPTURE ) ) {
			return $html;
		}

		$groups  = array();
		$current = array();
		foreach ( $mm[0] as $match ) {
			$tag = $match[0];
			if ( 0 === stripos( $tag, '<style' ) ) {
				if ( $current ) {
					$groups[] = $current;
				}
				$current = array();
				continue;
			}
			if ( preg_match( '#\bmedia=["\']([^"\']*)["\']#i', $tag, $md ) && ! in_array( strtolower( trim( $md[1] ) ), array( 'all', 'screen', '' ), true ) ) {
				continue; // print-only etc. – leave untouched.
			}
			if ( ! preg_match( '#\bhref=["\']([^"\']+)["\']#i', $tag, $hm ) ) {
				continue;
			}
			$current[] = array( 'tag' => $tag, 'href' => html_entity_decode( $hm[1] ) );
		}
		if ( $current ) {
			$groups[] = $current;
		}

		// A file that cannot be read (CDN down…) stays as its own <link>; the files around it are still bundled.
		$segments = array();
		foreach ( $groups as $group ) {
			$seg = array();
			foreach ( $group as $item ) {
				if ( null === self::css_source_available( $item['href'] ) ) {
					if ( $seg ) {
						$segments[] = $seg;
					}
					$seg = array();
					continue;
				}
				$seg[] = $item;
			}
			if ( $seg ) {
				$segments[] = $seg;
			}
		}

		$preload_fonts = array();
		foreach ( $segments as $group ) {
			$hrefs = wp_list_pluck( $group, 'href' );
			$built = self::build_css_bundle( $hrefs );
			if ( ! $built ) {
				continue;
			}
			$preload_fonts = array_merge( $preload_fonts, $built['preload'] );
			$first         = true;
			$noncritical   = true;
			foreach ( $hrefs as $h ) {
				if ( ! preg_match( '#/(select2|flatpickr|font-awesome)[^/]*\.css#i', $h ) ) {
					$noncritical = false;
				}
			}
			foreach ( $group as $item ) {
				$replacement = $first ? self::css_tag( $built['url'], $noncritical ) : '';
				$head        = self::str_replace_once( $item['tag'], $replacement, $head );
				$first       = false;
			}
		}

		// Some stylesheets are printed directly in the template (not enqueued) – make sure no third-party CSS is render-blocking.
		$preload = '';
		foreach ( array_unique( $preload_fonts ) as $font ) {
			$preload .= '<link rel="preload" href="' . esc_url( $font ) . '" as="font" type="font/woff2" crossorigin>' . "\n";
		}
		if ( $preload ) {
			$head = preg_replace( '#(<(?:link rel="stylesheet"|style) id="t3lh-css-)#', $preload . '$1', $head, 1 );
		}
		return $head . $rest;
	}

	/**
	 * Optional: define( 'T3LH_INLINE_CSS', true ) inlines the bundle. Measured: FCP 1.4→1.1s but LCP 2.5→3.3s
	 * (bigger HTML delays the hero poster), so the default stays a normal <link>.
	 */
	private static function css_tag( $url, $async = false ) {
		if ( $async ) {
			$u = esc_url( $url );
			return '<link rel="stylesheet" id="t3lh-css-' . substr( md5( $url ), 0, 6 ) . '" href="' . $u . '" media="print" onload="this.media=\'all\'" /><noscript><link rel="stylesheet" href="' . $u . '" /></noscript>';
		}
		if ( defined( 'T3LH_INLINE_CSS' ) && T3LH_INLINE_CSS ) {
			$file = self::opt_dir() . substr( $url, strlen( self::opt_url() ) );
			if ( is_file( $file ) && filesize( $file ) < 400 * 1024 ) {
				$css = (string) file_get_contents( $file );
				return '<style id="t3lh-css-' . substr( md5( $url ), 0, 6 ) . '">' . str_ireplace( '</style', '<\\/style', $css ) . '</style>';
			}
		}
		return '<link rel="stylesheet" id="t3lh-css-' . substr( md5( $url ), 0, 6 ) . '" href="' . esc_url( $url ) . '" media="all" />';
	}

	/** Cheap availability check (memoised per request; remote files are fetched once and cached by fetch_text). */
	private static function css_source_available( $href ) {
		$href = self::absolutize( $href, home_url( '/' ) );
		if ( false !== stripos( $href, 'fonts.googleapis.com' ) ) {
			return true;
		}
		return null === self::fetch_text( $href ) ? null : true;
	}

	private static function build_css_bundle( array $hrefs ) {
		$sig_parts = array( self::VERSION );
		foreach ( $hrefs as $href ) {
			$path = self::local_path( $href );
			// Local files: key on path + mtime only. The theme prints style9.css?<time()>, which would
			// otherwise create a brand-new bundle (and a cold CSS download) on every page generation.
			$sig_parts[] = $path ? $path . '|' . ( file_exists( $path ) ? filemtime( $path ) : 0 ) : $href;
		}
		$sig   = md5( implode( "\n", $sig_parts ) );
		$index = get_option( 't3lh_assets', array() );
		if ( isset( $index[ 'css_' . $sig ] ) ) {
			$entry = $index[ 'css_' . $sig ];
			if ( file_exists( self::opt_dir() . '/' . $entry['file'] ) ) {
				return array( 'url' => self::opt_url() . '/' . $entry['file'], 'preload' => $entry['preload'] );
			}
		}

		$css     = '';
		$preload = array();
		foreach ( $hrefs as $href ) {
			$chunk = self::get_css_with_imports( $href, 0, $preload );
			if ( null === $chunk ) {
				return null; // a file could not be read – leave the original tags alone.
			}
			$css .= $chunk . "\n";
		}
		$css = self::font_display_swap( $css );
		$css = self::minify_css( $css );

		$file = 'css/' . $sig . '.css';
		if ( ! self::write_opt_file( $file, $css ) ) {
			return null;
		}
		$index[ 'css_' . $sig ] = array( 'file' => $file, 'preload' => $preload, 't' => time() );
		// Keep at most 40 bundles (old signatures after theme edits).
		$css_keys = array_filter( array_keys( $index ), static function ( $k ) { return 0 === strpos( $k, 'css_' ); } );
		if ( count( $css_keys ) > 40 ) {
			usort( $css_keys, static function ( $a, $b ) use ( $index ) { return ( $index[ $a ]['t'] ?? 0 ) <=> ( $index[ $b ]['t'] ?? 0 ); } );
			foreach ( array_slice( $css_keys, 0, count( $css_keys ) - 40 ) as $old ) {
				@unlink( self::opt_dir() . '/' . $index[ $old ]['file'] ); // phpcs:ignore
				unset( $index[ $old ] );
			}
		}
		update_option( 't3lh_assets', $index, false );
		return array( 'url' => self::opt_url() . '/' . $file, 'preload' => $preload );
	}

	private static function get_css_with_imports( $href, $depth, array &$preload ) {
		if ( $depth > 4 ) {
			return '';
		}
		$href = self::absolutize( $href, home_url( '/' ) );

		if ( false !== stripos( $href, 'fonts.googleapis.com' ) ) {
			return self::self_host_google_fonts( $href, $preload );
		}

		$css = self::fetch_text( $href );
		if ( null === $css ) {
			return null;
		}
		$css = preg_replace( '#^\xEF\xBB\xBF#', '', $css );
		$css = preg_replace( '#@charset\s+["\'][^"\']*["\']\s*;#i', '', $css );
		$css = self::rewrite_css_urls( $css, $href );

		// Resolve @import recursively (removes the critical request chain style9.css → site.css / fonts css).
		$css = preg_replace_callback(
			'#@import\s+(?:url\(\s*)?(?:(["\'])(.*?)\1|([^"\'\s)]+))\s*\)?\s*([^;]*);#i',
			static function ( $m ) use ( $href, $depth, &$preload ) {
				$m     = array( $m[0], '' !== $m[2] ? $m[2] : $m[3], $m[4] );
				$url   = self::absolutize( $m[1], $href );
				$inner = self::get_css_with_imports( $url, $depth + 1, $preload );
				if ( null === $inner ) {
					return $m[0];
				}
				$media = trim( $m[2] );
				return ( '' !== $media && 'all' !== $media ) ? '@media ' . $media . '{' . $inner . '}' : $inner;
			},
			$css
		);
		// @import must be first in a stylesheet; any unresolved import left in the middle is invalid – hoisting is not
		// possible inside a bundle, so drop the bundle in that case.
		if ( preg_match( '#@import#i', $css ) ) {
			return null;
		}
		return $css;
	}

	private static function self_host_google_fonts( $href, array &$preload ) {
		$ua  = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';
		$res = wp_remote_get( $href, array( 'timeout' => 10, 'user-agent' => $ua ) );
		if ( is_wp_error( $res ) || 200 !== wp_remote_retrieve_response_code( $res ) ) {
			return null;
		}
		$css = wp_remote_retrieve_body( $res );
		return preg_replace_callback(
			'#@font-face\s*\{[^}]*\}#i',
			static function ( $face ) use ( &$preload ) {
				$block = preg_replace_callback(
					'#url\((https://fonts\.gstatic\.com/[^)]+)\)#i',
					static function ( $u ) {
						$local = self::localize_asset( $u[1], 'fonts' );
						return 'url(' . ( $local ? $local : $u[1] ) . ')';
					},
					$face[0]
				);
				// Preload only the Hebrew + basic Latin files that the page text actually needs.
				if ( preg_match( '#unicode-range:\s*([^;}]+)#i', $block, $ur ) && preg_match( '#url\(([^)]+\.woff2)\)#', $block, $fu ) ) {
					$range = strtoupper( $ur[1] );
					if ( false !== strpos( $range, 'U+0590' ) || false !== strpos( $range, 'U+0000-00FF' ) ) {
						$preload[] = $fu[1];
					}
				}
				return $block;
			},
			$css
		);
	}

	private static function font_display_swap( $css ) {
		return preg_replace_callback(
			'#@font-face\s*\{([^}]*)\}#i',
			static function ( $m ) {
				$body = $m[1];
				if ( preg_match( '#font-display\s*:#i', $body ) ) {
					$body = preg_replace( '#font-display\s*:\s*(block|auto)#i', 'font-display:swap', $body );
				} else {
					$body = 'font-display:swap;' . $body;
				}
				return '@font-face{' . $body . '}';
			},
			$css
		);
	}

	private static function rewrite_css_urls( $css, $base ) {
		return preg_replace_callback(
			'#url\(\s*(["\']?)([^"\')]+)\1\s*\)#i',
			static function ( $m ) use ( $base ) {
				$u = trim( $m[2] );
				if ( preg_match( '#^(data:|https?:|//|\#)#i', $u ) ) {
					return 'url(' . $m[1] . ( 0 === strpos( $u, '//' ) ? 'https:' . $u : $u ) . $m[1] . ')';
				}
				return 'url(' . $m[1] . self::absolutize( $u, $base ) . $m[1] . ')';
			},
			$css
		);
	}

	private static function minify_css( $css ) {
		$css = preg_replace( '#/\*(?!!).*?\*/#s', '', $css );
		$css = preg_replace( '#\s+#', ' ', $css );
		$css = preg_replace( '#\s*([{};,>])\s*#', '$1', $css );
		$css = preg_replace( '#\s*:\s*(?=[^{}]*[;}])#', ':', $css );
		$css = str_replace( ';}', '}', $css );
		return trim( $css );
	}

	/* --------------------------- Video -------------------------------- */

	/**
	 * Hero background video: the 1.8 MB MP4 no longer competes with first paint. The poster (LCP) is preloaded
	 * with high priority and the video starts on the first interaction. Adds a captions track (a11y).
	 */
	private static function process_video( $html ) {
		$first = true;
		return preg_replace_callback(
			'#<video\b([^>]*)>(.*?)</video>#is',
			static function ( $m ) use ( &$first ) {
				$attrs = $m[1];
				$inner = $m[2];
				$delay = ! ( defined( 'T3LH_DELAY_VIDEO' ) && ! T3LH_DELAY_VIDEO ) && false !== stripos( $attrs, 'autoplay' ) && false !== stripos( $attrs, 'muted' );

				if ( $delay ) {
					$inner = preg_replace( '#(<source\b[^>]*?)\bsrc=#i', '$1data-t3lh-src=', $inner );
					$attrs = preg_replace( '#\s*\bautoplay\b#i', '', $attrs ) . ' data-t3lh-video preload="none"';
				}
				if ( false === stripos( $inner, '<track' ) ) {
					$label  = 'he' === self::$lang ? 'וידאו רקע ללא דיבור' : 'Background video, no speech';
					$inner .= '<track kind="captions" srclang="' . esc_attr( self::$lang ) . '" label="' . esc_attr( $label ) . '" src="data:text/vtt;charset=utf-8,WEBVTT%0A">';
				}
				$hero = '';
				if ( $first && preg_match( '#\bposter=["\']([^"\']+)["\']#i', $attrs, $p ) ) {
					$poster              = esc_url( html_entity_decode( $p[1] ) );
					self::$head_inject[] = '<link rel="preload" as="image" href="' . $poster . '" fetchpriority="high">';
					// A plain <img> of the poster under the video: painted in the first frame (a video poster waits for
					// video layout + busy main thread → long "element render delay"). It is the LCP element.
					$class = preg_match( '#\bclass=["\']([^"\']*)["\']#i', $attrs, $c ) ? $c[1] : '';
					$hero  = '<img class="' . esc_attr( trim( $class . ' t3lh-hero' ) ) . '" src="' . $poster . '" alt="" aria-hidden="true" fetchpriority="high" loading="eager" decoding="async" data-t3lh-lcp>';
				}
				$first = false;
				return $hero . '<video' . $attrs . '>' . $inner . '</video>';
			},
			$html
		);
	}

	/* --------------------------- Images ------------------------------- */

	private static $head_inject = array();

	private static function process_images( $html ) {
		// Empty <img src=""> placeholders (empty ACF fields) – invalid, no alt, extra request to the page itself.
		$html = preg_replace( '#<img\s+src=(["\'])\1\s*/?>(\s*<br\s*/?>)*#i', '', $html );

		$count = 0;
		$html  = preg_replace_callback(
			'#<img\b([^>]*?)\s*/?>#i',
			static function ( $m ) use ( &$count ) {
				$attrs = $m[1];
				++$count;
				if ( ! preg_match( '#(?<![\w-])src=["\']([^"\']+)["\']#i', $attrs, $s ) ) {
					return $m[0];
				}
				$src = html_entity_decode( $s[1] );
				$aid = 0;

				// alt
				if ( ! preg_match( '#(?<![\w-])alt=#i', $attrs ) ) {
					$alt = '';
					if ( false !== strpos( $src, '/uploads/' ) ) {
						$aid = self::attachment_id( $src );
						if ( $aid ) {
							$alt = (string) get_post_meta( $aid, '_wp_attachment_image_alt', true );
						}
					}
					$attrs .= ' alt="' . esc_attr( $alt ) . '"';
				}

				// Lazy-load everything below the first few images (logo/hero stay eager).
				if ( $count > 3 && false === stripos( $attrs, 'loading=' ) ) {
					$attrs .= ' loading="lazy" decoding="async"';
				}

				$attrs = self::webp_swap_attr( $attrs );
				return '<img' . $attrs . '>';
			},
			$html
		);

		// Inline CSS backgrounds (div.img) → Imagify WebP copies when present.
		$html = preg_replace_callback(
			'#url\(\s*["\']?(https?://[^"\')]+?\.(?:jpe?g|png))["\']?\s*\)#i',
			static function ( $m ) {
				$webp = self::webp_url( $m[1] );
				return $webp ? 'url(' . $webp . ')' : $m[0];
			},
			$html
		);
		return $html;
	}

	private static function webp_swap_attr( $attrs ) {
		return preg_replace_callback(
			'#\b(src|srcset)=(["\'])([^"\']+)\2#i',
			static function ( $m ) {
				$val = preg_replace_callback(
					'#https?://[^\s,"\']+?\.(?:jpe?g|png)\b#i',
					static function ( $u ) {
						$webp = self::webp_url( $u[0] );
						return $webp ? $webp : $u[0];
					},
					$m[3]
				);
				return $m[1] . '=' . $m[2] . $val . $m[2];
			},
			$attrs
		);
	}

	private static function webp_url( $url ) {
		$path = self::local_path( $url );
		if ( ! $path || false === strpos( $url, '/uploads/' ) ) {
			return null;
		}
		foreach ( array( '.webp' => $path . '.webp', 'x' => preg_replace( '#\.(jpe?g|png)$#i', '.webp', $path ) ) as $kind => $candidate ) {
			if ( $candidate !== $path && file_exists( $candidate ) && filesize( $candidate ) > 0 && filesize( $candidate ) < filesize( $path ) ) {
				return '.webp' === $kind ? $url . '.webp' : preg_replace( '#\.(jpe?g|png)$#i', '.webp', $url );
			}
		}
		return null;
	}

	private static function attachment_id( $url ) {
		static $memo = array();
		if ( isset( $memo[ $url ] ) ) {
			return $memo[ $url ];
		}
		$key = 't3lh_aid_' . md5( $url );
		$id  = wp_cache_get( $key, 't3lh' );
		if ( false === $id ) {
			$id = (int) attachment_url_to_postid( preg_replace( '#-\d+x\d+(?=\.[a-z]+$)#i', '', $url ) );
			if ( ! $id ) {
				$id = (int) attachment_url_to_postid( $url );
			}
			wp_cache_set( $key, $id, 't3lh', DAY_IN_SECONDS );
		}
		return $memo[ $url ] = (int) $id;
	}

	/* ----------------------- Links & a11y ----------------------------- */

	private static function label_for_link( $attrs ) {
		$he  = 'he' === self::$lang;
		$map = array(
			'whatsapp'   => array( 'וואטסאפ', 'WhatsApp' ),
			'facebook'   => array( 'פייסבוק', 'Facebook' ),
			'instagram'  => array( 'אינסטגרם', 'Instagram' ),
			'linkedin'   => array( 'לינקדאין', 'LinkedIn' ),
			'youtube'    => array( 'יוטיוב', 'YouTube' ),
			'tiktok'     => array( 'טיקטוק', 'TikTok' ),
			'twitter'    => array( 'X (טוויטר)', 'X (Twitter)' ),
			'mobponeopen' => array( 'מספרי טלפון', 'Phone numbers' ),
			'scrolltop'  => array( 'חזרה לראש העמוד', 'Back to top' ),
			'scrollbottom' => array( 'גלילה לתוכן', 'Scroll down' ),
			'tel:'       => array( 'חיוג', 'Call' ),
			'mailto:'    => array( 'שליחת אימייל', 'Send email' ),
			'%D7%A6%D7%A8%D7%95-%D7%A7%D7%A9%D7%A8' => array( 'צרו קשר', 'Contact us' ),
			'צרו-קשר'   => array( 'צרו קשר', 'Contact us' ),
			'contact'    => array( 'צרו קשר', 'Contact us' ),
			'#phonenum'  => array( 'מספרי טלפון', 'Phone numbers' ),
		);
		foreach ( $map as $needle => $labels ) {
			if ( false !== stripos( $attrs, $needle ) ) {
				$label = $he ? $labels[0] : $labels[1];
				if ( 'tel:' === $needle && preg_match( '#tel:([^"\']+)#i', $attrs, $t ) ) {
					$label .= ' ' . $t[1];
				}
				return $label;
			}
		}
		return $he ? 'קישור' : 'Link';
	}

	private static function fix_links( $html ) {
		// Decorative icon fonts are hidden from screen readers.
		$html = preg_replace( '#<i\b(?![^>]*aria-hidden)([^>]*\bclass=["\'][^"\']*\b(?:fa|lnr|fas|fab|far)\b[^"\']*["\'][^>]*)>#i', '<i aria-hidden="true"$1>', $html );

		// Links without accessible text (icon-only links).
		$html = preg_replace_callback(
			'#<a\b([^>]*)>(.*?)</a>#is',
			static function ( $m ) {
				$attrs = $m[1];
				$inner = $m[2];
				$text  = trim( html_entity_decode( wp_strip_all_tags( $inner ) ), " \t\n\r\0\x0B\xC2\xA0" );
				if ( '' !== $text || preg_match( '#\baria-label(ledby)?=#i', $attrs ) || preg_match( '#<img\b[^>]*\balt=["\'][^"\']+["\']#i', $inner ) || preg_match( '#\btitle=["\'][^"\']+["\']#i', $attrs ) ) {
					return $m[0];
				}
				if ( '' === trim( $inner ) && ! preg_match( '#\bhref=#i', $attrs ) ) {
					return $m[0]; // named anchors
				}
				$attrs .= ' aria-label="' . esc_attr( self::label_for_link( $attrs ) ) . '"';
				return '<a' . $attrs . '>' . $inner . '</a>';
			},
			$html
		);

		// href="" (scroll buttons) → "#" ; javascript: links → crawlable "#" + role=button (SEO: crawlable-anchors).
		$html = preg_replace( '#(<a\b[^>]*\bhref=)(["\'])\2#i', '$1$2#$2 role="button"', $html );
		$html = preg_replace( '#(<a\b[^>]*\bhref=)(["\'])javascript:[^"\']*\2#i', '$1$2#$2 role="button"', $html );
		return $html;
	}

	/** <select> without a <label>: use its placeholder option (first <option>) as aria-label. */
	private static function fix_form_controls( $html ) {
		$labels_for = array();
		if ( preg_match_all( '#<label\b[^>]*\bfor=["\']([^"\']+)["\']#i', $html, $lm ) ) {
			$labels_for = array_flip( $lm[1] );
		}
		return preg_replace_callback(
			'#<(select|textarea|input)\b([^>]*)>#i',
			static function ( $m ) use ( $labels_for, $html ) {
				$tag   = strtolower( $m[1] );
				$attrs = $m[2];
				if ( preg_match( '#\baria-label(ledby)?=#i', $attrs ) ) {
					return $m[0];
				}
				if ( 'input' === $tag && preg_match( '#\btype=["\'](hidden|submit|button|image|reset)["\']#i', $attrs ) ) {
					return $m[0];
				}
				if ( preg_match( '#\bid=["\']([^"\']+)["\']#i', $attrs, $id ) && isset( $labels_for[ $id[1] ] ) ) {
					return $m[0];
				}
				$label = '';
				if ( preg_match( '#\bplaceholder=["\']([^"\']+)["\']#i', $attrs, $p ) ) {
					$label = $p[1];
				} elseif ( 'select' === $tag ) {
					$pos = strpos( $html, $m[0] );
					if ( false !== $pos && preg_match( '#<option\b[^>]*>([^<]*)</option>#i', substr( $html, $pos, 4000 ), $o ) ) {
						$label = trim( html_entity_decode( $o[1] ) );
					}
				}
				if ( '' === $label && preg_match( '#\bname=["\']([^"\']+)["\']#i', $attrs, $n ) ) {
					$label = trim( preg_replace( '#^field#', '', $n[1] ) );
				}
				if ( '' === $label ) {
					return $m[0];
				}
				$self_close = '/' === substr( rtrim( $attrs ), -1 );
				$attrs      = rtrim( rtrim( $attrs ), '/' );
				return '<' . $m[1] . $attrs . ' aria-label="' . esc_attr( $label ) . '"' . ( $self_close ? ' /' : '' ) . '>';
			},
			$html
		);
	}

	/** Removes empty headings and repairs skipped heading levels with aria-level (a11y: heading-order). */
	private static function fix_headings( $html ) {
		$html = preg_replace( '#<h([1-6])\b[^>]*>\s*</h\1>\s*#i', '', $html );

		$body_pos = stripos( $html, '<body' );
		if ( false === $body_pos ) {
			return $html;
		}
		$prev = 0;
		$head = substr( $html, 0, $body_pos );
		$body = preg_replace_callback(
			'#<h([1-6])\b([^>]*)>#i',
			static function ( $m ) use ( &$prev ) {
				$level = (int) $m[1];
				if ( preg_match( '#aria-level=["\'](\d)#', $m[2], $al ) ) {
					$prev = (int) $al[1];
					return $m[0];
				}
				if ( $prev && $level > $prev + 1 ) {
					$prev = $prev + 1;
					return '<h' . $m[1] . $m[2] . ' aria-level="' . $prev . '">';
				}
				$prev = $level;
				return $m[0];
			},
			substr( $html, $body_pos )
		);
		return $head . $body;
	}

	/* ------------------------ Injections ------------------------------ */

	private static function inject_head( $html ) {
		$timeout   = defined( 'T3LH_DELAY_TIMEOUT' ) ? (int) T3LH_DELAY_TIMEOUT : 0;
		// GTM waits 3.5s after load (or the first interaction, whichever comes first). Thank-you pages: immediate.
		$gtm_delay = defined( 'T3LH_GTM_DELAY' ) ? max( 0, (int) T3LH_GTM_DELAY ) : 3500;
		$loader  = <<<JS
(function(w,d){var done=0,E=["keydown","mousedown","mousemove","touchstart","touchmove","wheel","scroll","pointerdown","click"],o={passive:true,capture:true};
function run(type){var list=[].slice.call(d.querySelectorAll('script[type="'+type+'"]'));(function next(){var x=list.shift();if(!x)return;var s=d.createElement("script"),src=x.getAttribute("data-src");for(var i=0;i<x.attributes.length;i++){var a=x.attributes[i];if(a.name!=="type"&&a.name!=="data-src")s.setAttribute(a.name,a.value)}if(src){s.src=src;s.async=false;s.onload=s.onerror=next;x.parentNode.replaceChild(s,x)}else{s.text=x.text;x.parentNode.replaceChild(s,x);next()}})()}
function videos(){[].forEach.call(d.querySelectorAll("video[data-t3lh-video]"),function(v){[].forEach.call(v.querySelectorAll("source[data-t3lh-src]"),function(s){s.src=s.getAttribute("data-t3lh-src");s.removeAttribute("data-t3lh-src")});v.removeAttribute("data-t3lh-video");v.preload="auto";v.load();v.muted=true;var p=v.play();p&&p.catch&&p.catch(function(){})})}
var sy=w.scrollY||0;function real(e){if(e.type==="mousemove")return !!(e.movementX||e.movementY);if(e.type==="scroll")return Math.abs((w.scrollY||0)-sy)>2;return e.isTrusted!==false}
function go(e){if(done||(e&&e.type&&!real(e)))return;done=1;E.forEach(function(e){w.removeEventListener(e,go,o)});var f=function(){videos();run("t3lh/load");run("t3lh/delay")};d.readyState==="loading"?d.addEventListener("DOMContentLoaded",f):f()}
E.forEach(function(e){w.addEventListener(e,go,o)});
function afterHero(cb){var h=d.querySelector("img[data-t3lh-lcp]"),go2=function(){requestAnimationFrame(function(){requestAnimationFrame(function(){setTimeout(cb,0)})})};if(!h||h.complete){go2()}else{h.addEventListener("load",go2);h.addEventListener("error",go2)}}
w.addEventListener("load",function(){afterHero(function(){setTimeout(function(){run("t3lh/load")},{$gtm_delay})});run("t3lh/idle");if({$timeout}>0)setTimeout(go,{$timeout})});
w.t3lhRun=go;})(window,document);
JS;
		$css = '.item .txt ul li{color:#686c82}'
			. '.disclaimer{background-color:#007a9c!important}'
			. 'video[data-t3lh-video]{background:transparent}'
			. 'img.t3lh-hero{object-fit:cover;pointer-events:none}'
			// a11y target-size: icon-only header links ≥ 24×24px.
			. '.mobphicon a{display:inline-flex;align-items:center;justify-content:center;min-width:24px;min-height:24px}'
			. '.sub-menu a{display:inline-block;min-height:24px}'
			// a11y color-contrast: form text/placeholder #8092AD (3.2:1) → #5F6F8A (5.1:1).
			. 'input.txtbox,form select,form textarea,.select2-container .select2-selection__rendered{color:#5f6f8a!important}'
			. 'input.txtbox::placeholder,form textarea::placeholder{color:#5f6f8a!important;opacity:1}';

		$inject = '<script data-t3lh>' . $loader . '</script>' . "\n"
			. implode( "\n", array_unique( self::$head_inject ) ) . "\n";
		$html   = preg_replace_callback(
			'#<head\b[^>]*>#i',
			static function ( $m ) use ( $inject ) {
				return $m[0] . "\n" . $inject;
			},
			$html,
			1
		);
		$pos = stripos( $html, '</head>' );
		return substr( $html, 0, $pos ) . '<style id="t3lh-a11y">' . $css . "</style>\n" . substr( $html, $pos );
	}

	private static function inject_footer( $html ) {
		// Runs after all deferred scripts (jQuery etc.):
		// - stub for the missing isotope plugin (theme all.js calls .isotope() on every page → console error);
		// - "#" role=button links must not jump to top / change the URL.
		$js = 'if(window.jQuery&&!jQuery.fn.isotope){jQuery.fn.isotope=function(){return this}}'
			. 'document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest(\'a[role="button"][href="#"]\');if(a)e.preventDefault()});'
			// a11y aria-hidden-focus: sliders (Flickity/Slick) hide off-screen slides with aria-hidden but leave their links
			// focusable. Only the elements whose aria-hidden actually changes are touched (cheap, no full-page scans).
			. '(function(){var F="a[href],button,input,select,textarea,[tabindex]";'
			. 'function set(h){var hid=h.getAttribute("aria-hidden")==="true";h.querySelectorAll(F).forEach(function(f){if(hid){if(!f.hasAttribute("data-t3lh-ti")){f.setAttribute("data-t3lh-ti",f.getAttribute("tabindex")||"");f.setAttribute("tabindex","-1")}}else if(f.hasAttribute("data-t3lh-ti")){var t=f.getAttribute("data-t3lh-ti");t?f.setAttribute("tabindex",t):f.removeAttribute("tabindex");f.removeAttribute("data-t3lh-ti")}})}'
			. 'new MutationObserver(function(rs){for(var i=0;i<rs.length;i++){var t=rs[i].target;if(t.nodeType===1&&t.getAttribute("aria-hidden")!==null&&!t.matches("select,option,.select2-hidden-accessible"))set(t)}}).observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:["aria-hidden"]});'
			. 'document.querySelectorAll("[aria-hidden=true]:not(select):not(i)").forEach(set)})();';
		$tag = '<script data-t3lh defer src="data:text/javascript;base64,' . base64_encode( $js ) . '"></script>';
		$pos = strripos( $html, '</body>' );
		if ( false === $pos ) {
			return $html . $tag;
		}
		return substr( $html, 0, $pos ) . $tag . "\n" . substr( $html, $pos );
	}

	/* ------------------------ Asset helpers --------------------------- */

	private static function opt_dir() {
		$u = wp_upload_dir( null, false );
		return trailingslashit( $u['basedir'] ) . self::OPT_DIR;
	}

	private static function opt_url() {
		$u = wp_upload_dir( null, false );
		return set_url_scheme( trailingslashit( $u['baseurl'] ) . self::OPT_DIR );
	}

	private static function write_opt_file( $rel, $contents ) {
		$path = self::opt_dir() . '/' . $rel;
		if ( ! wp_mkdir_p( dirname( $path ) ) ) {
			return false;
		}
		$tmp = $path . '.' . uniqid( '', true ) . '.tmp';
		if ( false === file_put_contents( $tmp, $contents ) ) {
			return false;
		}
		return rename( $tmp, $path );
	}

	/** Copies a CDN / Google Fonts file to uploads/t3-opt and returns the local URL (null on failure). */
	private static function localize_asset( $url, $kind ) {
		$url  = 0 === strpos( $url, '//' ) ? 'https:' . $url : $url;
		$host = wp_parse_url( $url, PHP_URL_HOST );
		if ( ! $host || ( 'fonts' !== $kind && ! in_array( $host, self::LOCALIZE_HOSTS, true ) ) ) {
			return null;
		}
		$index = get_option( 't3lh_assets', array() );
		$key   = 'asset_' . md5( $url );
		if ( isset( $index[ $key ] ) ) {
			if ( '' === $index[ $key ]['file'] ) {
				return ( time() - $index[ $key ]['t'] ) < HOUR_IN_SECONDS ? null : self::localize_retry( $url, $kind, $key, $index );
			}
			if ( file_exists( self::opt_dir() . '/' . $index[ $key ]['file'] ) ) {
				return self::opt_url() . '/' . $index[ $key ]['file'];
			}
		}
		return self::localize_retry( $url, $kind, $key, $index );
	}

	private static function localize_retry( $url, $kind, $key, $index ) {
		$res  = wp_remote_get( $url, array( 'timeout' => 10, 'redirection' => 5 ) );
		$ok   = ! is_wp_error( $res ) && 200 === wp_remote_retrieve_response_code( $res ) && '' !== wp_remote_retrieve_body( $res );
		$ext  = strtolower( pathinfo( (string) wp_parse_url( $url, PHP_URL_PATH ), PATHINFO_EXTENSION ) );
		$ext  = $ext ? $ext : ( 'js' === $kind ? 'js' : 'bin' );
		$file = $kind . '/' . md5( $url ) . '.' . $ext;
		if ( $ok && 'js' === $ext ) {
			$body = preg_replace( '#//\# sourceMappingURL=\S+#', '', wp_remote_retrieve_body( $res ) );
			$ok   = self::write_opt_file( $file, $body );
		} elseif ( $ok ) {
			$ok = self::write_opt_file( $file, wp_remote_retrieve_body( $res ) );
		}
		$index[ $key ] = array( 'file' => $ok ? $file : '', 't' => time() );
		update_option( 't3lh_assets', $index, false );
		return $ok ? self::opt_url() . '/' . $file : null;
	}

	private static function fetch_text( $url ) {
		static $memo = array();
		if ( array_key_exists( $url, $memo ) ) {
			return $memo[ $url ];
		}
		return $memo[ $url ] = self::fetch_text_uncached( $url );
	}

	private static function fetch_text_uncached( $url ) {
		$path = self::local_path( $url );
		if ( $path ) {
			return file_exists( $path ) ? (string) file_get_contents( $path ) : null;
		}
		$host = wp_parse_url( $url, PHP_URL_HOST );
		if ( ! in_array( $host, self::LOCALIZE_HOSTS, true ) ) {
			return null;
		}
		// Remote CSS: reuse the localized copy, so the CDN is contacted once – not on every uncached page view.
		$local = self::localize_asset( $url, 'css' );
		if ( ! $local ) {
			return null;
		}
		$file = self::opt_dir() . substr( $local, strlen( self::opt_url() ) );
		return file_exists( $file ) ? (string) file_get_contents( $file ) : null;
	}

	/** Maps a URL on this site to a file path under ABSPATH / wp-content (null for remote URLs). */
	private static function local_path( $url ) {
		$url  = html_entity_decode( $url );
		$url  = 0 === strpos( $url, '//' ) ? 'https:' . $url : $url;
		$host = wp_parse_url( $url, PHP_URL_HOST );
		$home = wp_parse_url( home_url(), PHP_URL_HOST );
		if ( $host && strtolower( preg_replace( '#^www\.#', '', $host ) ) !== strtolower( preg_replace( '#^www\.#', '', $home ) ) ) {
			return null;
		}
		$path = rawurldecode( (string) wp_parse_url( $url, PHP_URL_PATH ) );
		if ( '' === $path || false !== strpos( $path, '..' ) ) {
			return null;
		}
		$content_path = (string) wp_parse_url( content_url(), PHP_URL_PATH );
		if ( $content_path && 0 === strpos( $path, $content_path . '/' ) ) {
			return WP_CONTENT_DIR . substr( $path, strlen( $content_path ) );
		}
		$site_path = rtrim( (string) wp_parse_url( site_url(), PHP_URL_PATH ), '/' );
		if ( 0 === strpos( $path, $site_path . '/wp-includes/' ) ) {
			return ABSPATH . ltrim( substr( $path, strlen( $site_path ) ), '/' );
		}
		return null;
	}

	private static function absolutize( $url, $base ) {
		$url = trim( $url );
		if ( preg_match( '#^https?://#i', $url ) ) {
			return $url;
		}
		if ( 0 === strpos( $url, '//' ) ) {
			return 'https:' . $url;
		}
		$b = wp_parse_url( $base );
		$origin = $b['scheme'] . '://' . $b['host'] . ( isset( $b['port'] ) ? ':' . $b['port'] : '' );
		if ( 0 === strpos( $url, '/' ) ) {
			return $origin . $url;
		}
		$dir   = isset( $b['path'] ) ? preg_replace( '#/[^/]*$#', '/', $b['path'] ) : '/';
		$parts = array();
		foreach ( explode( '/', $dir . $url ) as $seg ) {
			if ( '..' === $seg ) {
				array_pop( $parts );
			} elseif ( '.' !== $seg ) {
				$parts[] = $seg;
			}
		}
		return $origin . implode( '/', $parts );
	}

	private static function str_replace_once( $search, $replace, $subject ) {
		$pos = strpos( $subject, $search );
		return false === $pos ? $subject : substr_replace( $subject, $replace, $pos, strlen( $search ) );
	}

	/* ------------------------- Page cache ----------------------------- */

	/**
	 * Full-page disk cache for anonymous visitors (wp-content/cache/t3lh/).
	 * Served while plugins are still loading → TTFB drops from ~1.5s to a few ms of PHP.
	 * Response header X-T3-Cache shows HIT / MISS / BYPASS (reason) for diagnosis.
	 */
	private static $why = '';

	private static function cache_dir() {
		return WP_CONTENT_DIR . '/cache/t3lh';
	}

	private static function bypass( $reason ) {
		self::$why = $reason;
		return null;
	}

	private static function page_cache_key() {
		if ( defined( 'T3LH_PAGE_CACHE' ) && ! T3LH_PAGE_CACHE ) {
			return self::bypass( 'disabled' );
		}
		if ( ( defined( 'WP_CLI' ) && WP_CLI ) || ( defined( 'DOING_CRON' ) && DOING_CRON ) || ( defined( 'DOING_AJAX' ) && DOING_AJAX ) || ( defined( 'XMLRPC_REQUEST' ) && XMLRPC_REQUEST ) || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) ) {
			return self::bypass( 'context' );
		}
		$method = isset( $_SERVER['REQUEST_METHOD'] ) ? strtoupper( $_SERVER['REQUEST_METHOD'] ) : 'GET';
		if ( ! in_array( $method, array( 'GET', 'HEAD' ), true ) ) {
			return self::bypass( 'method' );
		}
		foreach ( array_keys( $_COOKIE ) as $c ) {
			if ( preg_match( '#^(wordpress_logged_in_|wordpress_sec_|wp-postpass_|comment_author_|woocommerce_|wp_woocommerce_session_)#', $c ) ) {
				return self::bypass( 'logged-in' );
			}
		}
		$uri  = isset( $_SERVER['REQUEST_URI'] ) ? (string) $_SERVER['REQUEST_URI'] : '/';
		$path = (string) parse_url( $uri, PHP_URL_PATH );
		if ( preg_match( '#^/(wp-admin|wp-login|wp-json|wp-cron|xmlrpc|wp-content|wp-includes)|\.(php|xml|txt|xsl)$|/feed/?$#i', $path ) ) {
			return self::bypass( 'path' );
		}
		$query = (string) parse_url( $uri, PHP_URL_QUERY );
		if ( '' !== $query ) {
			parse_str( $query, $params );
			foreach ( array_keys( $params ) as $p ) {
				if ( ! preg_match( '#^(utm_[a-z_]+|gclid|gbraid|wbraid|fbclid|msclkid|ttclid|_gl|mc_cid|mc_eid|srsltid)$#i', $p ) ) {
					return self::bypass( 'query' ); // search, filters, ?t3lh=off …
				}
			}
		}
		$host   = isset( $_SERVER['HTTP_HOST'] ) ? strtolower( $_SERVER['HTTP_HOST'] ) : '';
		$ua     = isset( $_SERVER['HTTP_USER_AGENT'] ) ? $_SERVER['HTTP_USER_AGENT'] : '';
		$mobile = preg_match( '#Mobile|Android|Silk/|Kindle|BlackBerry|Opera Mini|Opera Mobi#', $ua ) ? 'm' : 'd';
		$https  = ( ! empty( $_SERVER['HTTPS'] ) && 'off' !== $_SERVER['HTTPS'] ) || ( isset( $_SERVER['HTTP_X_FORWARDED_PROTO'] ) && 'https' === $_SERVER['HTTP_X_FORWARDED_PROTO'] ) ? 's' : 'p';
		return md5( self::VERSION . '|' . $https . '|' . $host . '|' . $path . '|' . $mobile );
	}

	private static function maybe_serve_cached_page() {
		$key = self::page_cache_key();
		if ( ! $key ) {
			return;
		}
		$file = self::cache_dir() . '/' . $key . '.html';
		if ( ! is_file( $file ) || ( time() - filemtime( $file ) ) > 6 * 3600 ) {
			self::$why = 'MISS';
			return;
		}
		$html = file_get_contents( $file );
		if ( false === $html || '' === $html ) {
			return;
		}
		header( 'Content-Type: text/html; charset=UTF-8' );
		header( 'X-T3-Cache: HIT' );
		header( 'Cache-Control: max-age=0, must-revalidate' );
		if ( ! ( defined( 'T3LH_SECURITY_HEADERS' ) && ! T3LH_SECURITY_HEADERS ) ) {
			header( 'X-Content-Type-Options: nosniff' );
			header( 'X-Frame-Options: SAMEORIGIN' );
			header( 'Referrer-Policy: strict-origin-when-cross-origin' );
			header( 'Strict-Transport-Security: max-age=31536000' );
		}
		if ( 'HEAD' !== strtoupper( $_SERVER['REQUEST_METHOD'] ) ) {
			echo $html; // phpcs:ignore
		}
		exit;
	}

	/** Called on send_headers: tell the outside world why this page was (not) cached. */
	public static function cache_status_header() {
		if ( ! headers_sent() && '' !== self::$why ) {
			header( 'X-T3-Cache: ' . ( 'MISS' === self::$why ? 'MISS' : 'BYPASS (' . self::$why . ')' ) );
		}
	}

	private static function maybe_store_cached_page( $html ) {
		$key = self::page_cache_key();
		if ( ! $key ) {
			return;
		}
		if ( 200 !== (int) http_response_code() || is_404() || is_search() || is_user_logged_in() || post_password_required() || ( defined( 'DONOTCACHEPAGE' ) && DONOTCACHEPAGE ) ) {
			return;
		}
		foreach ( headers_list() as $h ) {
			if ( preg_match( '#^Location:#i', $h ) || ( preg_match( '#^Set-Cookie:#i', $h ) && ! preg_match( '#^Set-Cookie:\s*(wp-wpml_current_language|_icl_)#i', $h ) ) ) {
				return; // personalised response.
			}
			if ( preg_match( '#^Content-Type:#i', $h ) && false === stripos( $h, 'text/html' ) ) {
				return;
			}
		}
		$dir = self::cache_dir();
		if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
			return;
		}
		if ( ! file_exists( $dir . '/index.php' ) ) {
			@file_put_contents( $dir . '/index.php', "<?php // Silence is golden.\n" ); // phpcs:ignore
		}
		$tmp = $dir . '/' . $key . '.' . uniqid( '', true ) . '.tmp';
		if ( false !== @file_put_contents( $tmp, $html . "\n<!-- t3lh cached " . gmdate( 'c' ) . ' -->' ) ) { // phpcs:ignore
			@rename( $tmp, $dir . '/' . $key . '.html' ); // phpcs:ignore
		}
	}

	public static function purge_all() {
		foreach ( (array) glob( self::cache_dir() . '/*.{html,tmp}', GLOB_BRACE ) as $f ) {
			@unlink( $f ); // phpcs:ignore
		}
	}

	public static function maybe_purge_on_option( $option ) {
		if ( preg_match( '#^(widget_|theme_mods_|options_|_options_|page_scroll_to_id|wpseo|blogname|blogdescription|show_on_front|page_on_front|permalink_structure)#', $option ) ) {
			self::purge_all();
		}
	}

	public static function admin_bar( $bar ) {
		if ( ! current_user_can( 'manage_options' ) ) {
			return;
		}
		$bar->add_node(
			array(
				'id'    => 't3lh-purge',
				'title' => 'ניקוי מטמון T3',
				'href'  => wp_nonce_url( admin_url( 'admin-post.php?action=t3lh_purge' ), 't3lh_purge' ),
			)
		);
	}

	public static function handle_purge_request() {
		if ( ! current_user_can( 'manage_options' ) || ! check_admin_referer( 't3lh_purge' ) ) {
			wp_die( 'Forbidden', 403 );
		}
		self::purge_all();
		// Rebuild CSS bundles / CDN copies on next request.
		delete_option( 't3lh_assets' );
		wp_safe_redirect( wp_get_referer() ? wp_get_referer() : home_url( '/' ) );
		exit;
	}
}

T3_Lighthouse::boot();
