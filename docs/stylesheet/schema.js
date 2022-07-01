$(document).ready(function () {
  $("#schema a").mouseover(function(e){
    var selected = $(e.target);
    $("h4#title").text(selected.text());
    
    if (selected.attr("description")) {
      $("p#description").html(selected.attr("description"));
    }
  });


  //var ids = [];
  var terms = [];

  $('#schema a').each(function () {
    if (this.id != "") {
      var href = $(this).attr('href');
      if (href) {
        //console.log($(href).attr('id'));
        terms.push({
          label: this.text,
          value: $(href).attr('id')
        });
      }
      else {
        terms.push({
          label: this.text,
          value: this.id
        });
      }
    }
  });

  //console.log(terms);

  $('#termSearch').autocomplete({
    source: terms,
    minLength: 1,
    scroll: true,
    select: function( event, ui ) {
      var selected = $('#'+ui.item.value);
      //console.log(selected);

      var tags = [];
      var curr = selected.parent();
      while (curr.attr('id') != "schema") {
        //console.log(curr.attr('id'));
        tags.push(curr.attr('id'));
        curr = curr.parent();
      }

      //console.log(tags);

      $.each(tags, function(key, value){
        var tag = $('#'+value);
        tag.addClass("show");
      });
      
      var highlight = selected;

      if (selected.prop('tagName') == "DIV") {
        highlight = $('#'+ui.item.value+"_");
      }

      $('html, body').animate({ scrollTop: selected.offset().top-300 }, 10);
      highlight.effect("highlight", {}, 4000);

    }
  });

  // .focus(function() {
  //     $(this).autocomplete("search", "");
  // });
  

});