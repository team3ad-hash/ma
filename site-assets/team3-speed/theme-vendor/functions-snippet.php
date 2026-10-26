<?php
// Serve Flickity, Fancybox and Waypoints from the theme instead of external CDNs.
// Paste at the end of wp-content/themes/team3/functions.php (without the opening <?php line).
add_action( 'wp_enqueue_scripts', function () {
	$base = get_template_directory_uri() . '/assets/vendor/';
	$local = array(
		'styles'  => array(
			'flickity' => array( 'flickity/flickity.min.css', '2.3.0' ),
			'fancybox' => array( 'fancybox/jquery.fancybox.min.css', '3.5.7' ),
		),
		'scripts' => array(
			'flickity'  => array( 'flickity/flickity.pkgd.min.js', '2.3.0' ),
			'fancybox'  => array( 'fancybox/jquery.fancybox.min.js', '3.5.7' ),
			'waypoints' => array( 'waypoints/jquery.waypoints.min.js', '4.0.1' ),
		),
	);
	foreach ( array( 'styles' => wp_styles(), 'scripts' => wp_scripts() ) as $type => $registry ) {
		foreach ( $local[ $type ] as $handle => list( $file, $ver ) ) {
			if ( isset( $registry->registered[ $handle ] ) ) {
				$registry->registered[ $handle ]->src = $base . $file;
				$registry->registered[ $handle ]->ver = $ver;
			}
		}
	}
}, 100 );
