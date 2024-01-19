function validateTrivia(event) {
    var selectedAnswer = document.getElementById('answers').value;
    var correctAnswer = document.getElementById('correct').value;

    if (selectedAnswer !== correctAnswer) {
        alert('Are you sure?');
        event.preventDefault();
    }
}