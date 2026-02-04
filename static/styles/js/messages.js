// Fetch and display messages
$.getJSON('/get_messages', function(messages) {
    var messagesContainer = $('.flashes');
    messagesContainer.empty(); // Clear the container

    $.each(messages, function(i, message) {
        var li = $('<li>').text(message);
        messagesContainer.append(li);
    });
});



