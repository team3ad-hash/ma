<?php
/**
 * Plugin Name: Team3 Lazy Loading
 * Description: Adds native lazy loading to every image and iframe on the front end, except the first images (logo / above the fold).
 * Install: upload to wp-content/mu-plugins/ (create the folder if missing). Remove the file to undo.
 */

defined( 'ABSPATH' ) || exit;

// Number of <img> tags at the top of the page to keep eager (header logo, first visible image).
const TEAM3_LAZY_SKIP_FIRST = 1;

add_action( 'template_redirect', function () {
	if ( is_admin() || wp_doing_ajax() || is_feed() || wp_is_json_request() || is_customize_preview() ) {
		return;
	}
	ob_start( 'team3_lazy_load_filter_html' );
}, 0 );

function team3_lazy_load_filter_html( $html ) {
	if ( stripos( $html, '<html' ) === false ) {
		return $html;
	}

	$count = 0;
	$html  = preg_replace_callback( '/<img\b[^>]*>/i', function ( $m ) use ( &$count ) {
		$tag = $m[0];
		$count++;

		// Leave alone: first images, tags that already decide, empty placeholders, and explicitly excluded ones.
		if ( $count <= TEAM3_LAZY_SKIP_FIRST
			|| preg_match( '/\sloading\s*=/i', $tag )
			|| preg_match( '/\sfetchpriority\s*=\s*["\']?high/i', $tag )
			|| preg_match( '/\ssrc\s*=\s*(""|\'\')/i', $tag )
			|| preg_match( '/\bno-lazy\b/i', $tag ) ) {
			return $tag;
		}

		$attrs = ' loading="lazy"';
		if ( ! preg_match( '/\sdecoding\s*=/i', $tag ) ) {
			$attrs .= ' decoding="async"';
		}
		return preg_replace( '/^<img\b/i', '<img' . $attrs, $tag );
	}, $html );

	// iframes (maps, YouTube) are always below the fold on this site.
	$html = preg_replace( '/<iframe\b(?![^>]*\sloading\s*=)/i', '<iframe loading="lazy"', $html );

	return $html;
}
