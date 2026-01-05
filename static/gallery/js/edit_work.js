$(document).ready(function() {
    appUtils.enableCsrfForAjax();
    
    var previewTimer = null;
    $("#id_body").keyup(function() {
	if (previewTimer != null) {
	    window.clearTimeout(previewTimer);
	}
	previewTimer = window.setTimeout(function() {
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

  
  // Because setting widget=TextArea(attrs={"rows": 50, "cols": 80}) in
  // forms.py doesn't seem to work:
  $("textarea").attr({"rows": "50",
		      "cols": "80"
		     });

  $("#insert-image").click(function() {
    console.log("You clicked insert-image")
    // do an AJAX post of the selected image, get back media URL, insert <img src=media URL>

    var form = $("#insert-image-form");
    
    $.ajax({url: form.attr("action"),
	    method: form.attr("method"),
	    data: new FormData(form[0]),
	    processData: false,
	    contentType: false,
	    success: function(data, result, xhr) {
	      console.log("Data img_url is " + data.img_url);
	      // this append sued to work butu stopped?
	      $("#id_body").append("\n\n&lt;img src=\"" + data.img_url + "\"&gt;\n");
	    },
	    failure: function() {
	    },
	    dataType: "json"
	   }
	  );
  });
});
