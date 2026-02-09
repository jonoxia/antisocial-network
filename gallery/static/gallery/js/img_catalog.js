/* Count how many pics are checked;
 * Hide form UI that doesn't make sense.
 * Maybe some form validation. */

$(document).ready(function() {

    $(".img_select_checkbox").click(function() {
        var checkedCount = $(".img_select_checkbox:checked").length;
        $("#status-message").text(checkedCount + " images selected");
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


    $("#create-button").click(function() {
        var checked_ids = [];
        $(".img_select_checkbox:checked").each(function() {
            checked_ids.push( $(this).attr("id") );
        });
        $("#status-message").text("Creating.... ");

        var form_data = new FormData( $("#creation-form")[0]);

        form_data.append("selected-doc-ids", checked_ids.join(","))

	var response = await fetch(url, {
	    method: "POST",
	    body: form_data
	});
	var result = await response.json();
	$("#status-messge").text(result.message);
    });
});
