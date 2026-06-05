$(document).ready(function() {
  $('.card-product-grid').each(function(i) {
    var delay = i * 0.07;
    $(this).addClass('stagger-item').css('animation-delay', delay + 's');
  });
});
