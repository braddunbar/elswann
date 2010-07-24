(function( $, undefined ){

var rLink = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
function linkify( s ){
	return s.replace( rLink, "<a href='$1'>$1</a>" );
}

jQuery(function( $ ) {

	var url = "http://api.twitter.com/1/statuses/user_timeline/elswann.json?count=8&callback=?";

	$.getJSON( url, function( data ) {
		var list = $.map(data, function( s ) {
			return "<li>" +
				linkify( s.text ) +
				"<br>" +
				"<span>" +
					"<a href='http://twitter.com/elswann/status/" + s.id + "'>" +
						prettyDate( s.created_at ) +
					"</a>" +
					" via " + s.source +
				"</span>" +
			"</li>";
		});
		$( ".tweets" ).html( list.join( "" ) );

		twttr.anywhere( function( t ) {
			t.hovercards();
			t( ".follow-button" ).followButton( "elswann" );
		});
	});

	$( "a[rel=photo]" ).lightbox({ fitToScreen: true });
});


})( jQuery );
