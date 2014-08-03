$('document').ready(function(){
    $('.edit_entry').on('submit', function(event){
          event.preventDefault();

          var id =  $(event.target).attr('id');
          $.ajax(('/edit/'+id),{
              type: 'GET',
              data: {'id': id},
              context: $(event.target),
              success: function(result){
                  var parent = $(this).parent();
                  parent.empty().html(result);

              }
          });
    });
    $('.delete_entry').on('submit', function(event){
          event.preventDefault();

          var id =  $(event.target).attr('id');
          $.ajax(('/delete/'+id),{
              type: 'POST',
              data: {'id': id},
              context: $(event.target),
              success: function(result){
                  var parent = $(this).parent().parent();
                  parent.hide();

              }
          });
    });
})


$(function(){
  $('.edit_entry').click(function(){

    })
})