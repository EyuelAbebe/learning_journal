$('document').ready(function(){
    $('.edit_entry').on('submit', function(event){
          event.preventDefault();

          var id =  $(event.target).attr('id');
          console.log(id, $('form').attr('action'))
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
})