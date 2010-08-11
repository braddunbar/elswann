(function( $, undefined ){

function relDate( s ){
	var date = new Date( (s || "").replace(/-/g,"/") ),
		diff = ((new Date()).getTime() - date.getTime()) / 1000,
		day_diff = Math.floor(diff / 86400);
			
	if ( isNaN(day_diff) || day_diff < 0 || day_diff >= 31 )
		return;
			
	return day_diff == 0 && (
			diff < 60 && "just now" ||
			diff < 120 && "1 minute ago" ||
			diff < 3600 && Math.floor( diff / 60 ) + " minutes ago" ||
			diff < 7200 && "1 hour ago" ||
			diff < 86400 && Math.floor( diff / 3600 ) + " hours ago"
		) ||
		day_diff == 1 && "Yesterday" ||
		day_diff < 7 && day_diff + " days ago" ||
		day_diff < 31 && Math.ceil( day_diff / 7 ) + " weeks ago";
}

function twitterDate( s ){
	return s.replace( /^\w+ (\w+) (\d+) ([\d:]+) \+\d{4} (\d+)$/, "$1 $2 $4 $3 UTC" );
}

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
						relDate( twitterDate(s.created_at) ) +
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

	var content = false;
	$( "#qsearch" ).focus( function( event ){
		if ( !content ){
			$( this ).val( "" );
		}
	})
	.blur( function( event ){
		content = !!$.trim( $( this ).val() );
		if ( !content ) {
			$( this ).val( "Search This Site..." );
		}
	});
});


})( jQuery );
