$(document).ready(function () {
  $("a").mouseover(function(e){
    var selected = $(e.target);
    $("h4#title").text(selected.text());
    
    if (selected.attr("description")) {
      $("p#description").text(selected.attr("description"));
    }
    else {
      $("p#description").text("");
    }

    if ($("p#description").text() == "") {
      $("p#description").html("<i>Description not found</i>");
    }
  });

});