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
});
