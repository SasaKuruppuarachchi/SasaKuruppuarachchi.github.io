/*
	Strata by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

(function($) {

	var settings = {

		// Parallax background effect?
			parallax: true,

		// Parallax factor (lower = more intense, higher = less intense).
			parallaxFactor: 20

	};

	// Gracefully handle absence of Skel (some pages may not load skel.min.js)
	var S = (typeof skel !== 'undefined') ? skel : null;

	if (S) S.breakpoints({
		xlarge: '(max-width: 1800px)',
		large: '(max-width: 1280px)',
		medium: '(max-width: 980px)',
		small: '(max-width: 736px)',
		xsmall: '(max-width: 480px)'
	});

	$(function() {

		var $window = $(window),
			$body = $('body'),
			$header = $('#header');

		// Disable animations/transitions until the page has loaded.
			$body.addClass('is-loading');

			$window.on('load', function() {
				$body.removeClass('is-loading');
			});

		// Touch?
			if (S && S.vars.mobile) {

				// Turn on touch mode.
					$body.addClass('is-touch');

				// Height fix (mostly for iOS).
					window.setTimeout(function() {
						$window.scrollTop($window.scrollTop() + 1);
					}, 0);

			}

		// Fix: Placeholder polyfill.
			$('form').placeholder();

		// Prioritize "important" elements on medium.
			if (S) {
				S.on('+medium -medium', function() {
					$.prioritize(
						'.important\\28 medium\\29',
						S.breakpoint('medium').active
					);
				});
			}

		// Header.

			// Parallax background.

					// Disable parallax on IE (smooth scrolling is jerky), and on mobile platforms (= better performance).
						if (S) {
							if (S.vars.browser == 'ie' || S.vars.mobile)
								settings.parallax = false;
						} else {
							// Without Skel, avoid parallax to be safe/perf
							settings.parallax = false;
						}

				if (settings.parallax && S) {

						S.on('change', function() {

							if (S.breakpoint('medium').active) {

							$window.off('scroll.strata_parallax');
							$header.css('background-position', 'top left, center center');

						}
						else {

							$header.css('background-position', 'left 0px');

							$window.on('scroll.strata_parallax', function() {
								$header.css('background-position', 'left ' + (-1 * (parseInt($window.scrollTop()) / settings.parallaxFactor)) + 'px');
							});

						}

					});

				}

		// Main Sections: Two.

			// Lightbox gallery.
				$window.on('load', function() {

					var marginSmall = (S && S.breakpoint && S.breakpoint('small').active) ? 0 : 50;
					$('#two').poptrox({
						caption: function($a) { return $a.next('h3').text(); },
						overlayColor: '#2c2c2c',
						overlayOpacity: 0.85,
						popupCloserText: '',
						popupLoaderText: '',
						selector: '.work-item a.image',
						usePopupCaption: true,
						usePopupDefaultStyling: false,
						usePopupEasyClose: false,
						usePopupNav: true,
						windowMargin: marginSmall
					});

				});

	});

})(jQuery);

// Inject last updated date into footer span if present.
(function(){
	var span = document.getElementById('last-updated');
	if(!span) return;
	var meta = document.querySelector('meta[name="last-build"]');
	var d;
	if(meta && meta.content){
		span.textContent = meta.content;
		return;
	}
	d = new Date();
	var m = ('0' + (d.getMonth() + 1)).slice(-2);
	var day = ('0' + d.getDate()).slice(-2);
	span.textContent = d.getFullYear() + '-' + m + '-' + day;
})();