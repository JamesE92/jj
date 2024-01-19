function rafflesubject() {
    var selectedAnswer = document.getElementById("answers");
    var subjectField = document.getElementById("selectedAnswer");

    selectedAnswer.addEventListener('change', function() {
        subjectField.value = selectedAnswer.value;
    });
}

function validateTrivia(correctAnswer, answer1, answer2, answer3) {
    var form = document.getElementById('raffleForm');
    form.addEventListener('submit', function(event) {
        var selectedAnswer = document.getElementById('answers').value;

        if (selectedAnswer !== correctAnswer) {
            alert('Wrong answer!');
            event.preventDefault();
        }
    });
}
