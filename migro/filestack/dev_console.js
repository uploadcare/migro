(function () {

  function b64EncodeUnicode(str) {
    return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,
        function toSolidBytes(match, p1) {
          return String.fromCharCode('0x' + p1);
        }));
  }

  var $btnLoadMore = jQuery('#console-loadmore');
  var handles = [];

  var loadMoreCallback = function (event, jqXHR, options, data) {
    if (options.url.startsWith(window.location.pathname + '/')) {
      if (data) {
        $btnLoadMore.trigger('click', true);
      } else {
        $('a.js_download').each(function (index, item) {
          handles.push($(item).attr('href'));
        });
        var content = (b64EncodeUnicode(handles.join('\n')));
        jQuery('h4.subheading').html('<a id="download-files-list" href="data:application/octet-stream;charset=utf-8;base64,' + content + '">Download files lists</a>')
      }
    }
  };

  jQuery(document).ajaxSuccess(loadMoreCallback);
  $btnLoadMore.trigger('click', true);

})();
