/* Count how many pics are checked;
 * Hide form UI that doesn't make sense.
 * Maybe some form validation. */

$(document).ready(function() {

    $(".img_select_checkbox").click(function() {
	var checkedCount = $(".img_select_checkbox:checked").length;
	$("#checked-counter").text("" + checkedCount);
    });

    $("#what-to-create").change(function() {
	if ( $(this).val() == "new-gallery" ) {
	    $("#gallery-to-add-to").hide();
	} else {
	    $("#gallery-to-add-to").show();
	}
	if ( $(this).val() == "expand-gallery" ) {
	    $("#new-title").hide();
	} else {
	    $("#new-title").show();
	}
    });
});
