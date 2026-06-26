$(document).ready(function(){
  $('.thumb a').click(function(e){
    e.preventDefault();
    $('.mainImage img').attr('src', $(this).attr("href"));
  });
});
