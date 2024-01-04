function rafflesubject() {
    var selectedAnswer = document.getElementById("answers");
    var subjectField = document.getElementById("selectedAnswer");
    
    selectedAnswer.addEventListener('change', function() {
        subjectField.value = selectedAnswer.value;
    });
}