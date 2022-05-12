$(document).ready(function () {
  $("a").mouseover(function(e){
    var selected = $(e.target);
    $("h4#title").text(selected.text());
    
    if (selected.attr("description")) {
      $("p#description").html(selected.attr("description"));
    }
  });

});