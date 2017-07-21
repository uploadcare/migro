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
      if ($btnLoadMore.attr('disabled') !== 'disabled'){
        console.log('Downloading more data for files list...');
        $btnLoadMore.trigger('click', true);
      } else {
        console.log('Done collect your files links!');
        console.log('Preparing file for download...');
        $('a.js_download').each(function (index, item) {
          handles.push($(item).attr('href'));
        });
        var content = (b64EncodeUnicode(handles.join('\n')));
        jQuery('h4.subheading').html(
            '<a id="download_files-list" '
            + 'download="filestack_files_list.txt" '
            + 'href="data:application/octet-stream;charset=utf-8;base64,' + content
            + '">' + 'Download files list' + '</a>'
        );
        console.log('Done preparing file for download!\n' +
                    'Now simply click on \'Download files list\' link in the header of the page!');
      }
    }
  };
  jQuery(document).ajaxSuccess(loadMoreCallback);
  console.log('Staring collect your files links...');
  $btnLoadMore.trigger('click', true);
})();
