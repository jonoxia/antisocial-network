var appUtils = appUtils || {};

appUtils.stickydiv = function(div_id, stick_class, offset) {
  // Reference: http://blog.yjl.im/2010/01/stick-div-at-top-after-scrolling.html
  //
  // div_id: string of the element that needs to move down the page
  // stick_class: the CSS class that governs sticking
  //
  // put a <div id="sticky-anchor"></div> where, when you scroll past this div,
  // the element will start scrolling down as you scroll down the page
  if (typeof offset === 'undefined') { offset = 0; }

  var window_top = window.scrollY;
  var div_top = ($('#sticky-anchor').offset().top) - offset;
  if (window_top > div_top) {
    $('#'+div_id).addClass(stick_class);
  } else {
    $('#'+div_id).removeClass(stick_class);
  }
}

appUtils.csrfIsSetup = false;
appUtils.enableCsrfForAjax = function() {
  /* Call this once before attempting any AJAX posts.
   * from http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request
   * Causes CSRF cookie to be sent along with AJAX post so we get past Django's
   * anti- cross-site-scripting protection.
   * Without the CSRF cookie, we get 403: Forbidden on each submit. */

  if (appUtils.csrfIsSetup) {
    return; // Only do this once even if called multiple times.
  }

  $.ajaxSetup({ 
    beforeSend: function(xhr, settings) {
      function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }
      xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    } 
  });
  appUtils.csrfIsSetup = true;
}
