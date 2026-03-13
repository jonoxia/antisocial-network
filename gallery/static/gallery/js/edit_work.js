$(document).ready(function() {
    appUtils.enableCsrfForAjax();
    
    var previewTimer = null;
    $("#id_body").keyup(function() {
	if (previewTimer != null) {
	    window.clearTimeout(previewTimer);
	}
	previewTimer = window.setTimeout(function() {
	    console.log("U changed the text box");
	    previewTimer = null;
	    $.ajax({url: "/preview",
		    method: "POST",
		    data: {"body": $("#id_body").val()},
		    success: function(data, result, xhr) {
                        $("#preview-box").html(data.html);
		    },
		    error: function(a, b, c) {
			console.log("2nd func A is " + a);
			console.log("2nd func B is " + b);
			console.log("2nd func C is " + c);
			//$("#preview-box").html(data);
		    },
		    dataType: "json"
		   }
		  );
	}, 500);
    });

    console.log("I loaded edit_work.js");
    $("#insert-image").click(function() {
	console.log("You clicked the insert-image button.");

	const form = $('#insert-image-form');
	const formData = new FormData(form[0]);
	$("#id_docfile_helptext").text("Uploading, don't click again...");

	$.ajax({
	    url: form.attr('action') || window.location.href,
	    method: 'POST',
	    data: formData,
	    processData: false,  // prevent jQuery from serializing FormData
	    contentType: false,  // let browser set Content-Type with boundary
	    success: function(response) {
		// Response should be JSON including field "img_placeholder"
		var placeholder = response["img_placeholder"];
		console.log(placeholder);
		$("#id_docfile_helptext").text("Successfully uploaded image " + placeholder);

		$("#id_body").text( $("#id-body").text() + "\n\n{{" + placeholder + "}}\n\n");
	    },
	    error: function(xhr, status, error) {
		console.log(xhr.responseText);
		$("#id_docfile_helptext").text("Error: " + xhr.responseText);
	    }
	});

	// this needs to upload the file, create the document, insert placeholder text into
	// the document being edited...

	// TODO we also want a way to open a sidebar browser of unaffiliated images to browse
	// through and include into the body text...
    });
});
