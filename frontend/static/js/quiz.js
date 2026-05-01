let questions = [];
let currentQuestion = 0;
let score = 0;
let selectedOption = null;

document.addEventListener("DOMContentLoaded", () => {
    loadQuiz();
});

function selectOption(index) {
    selectedOption = index;
    const buttons = document.querySelectorAll(".option-btn");
    buttons.forEach((btn, i) => {
        btn.classList.toggle("selected", i === index);
    });
    document.getElementById("submit-btn").disabled = false;
}

function submitAnswer() {
    if (selectedOption === null) return;

    const question = questions[currentQuestion];
    const isCorrect = question.options[selectedOption] === question.correct_answer;
    const buttons = document.querySelectorAll(".option-btn");

    buttons.forEach((btn, i) => {
        btn.classList.remove("selected");
        btn.onclick = null;
        if (question.options[i] === question.correct_answer) {
            btn.classList.add("correct");
        } else if (i === selectedOption && !isCorrect) {
            btn.classList.add("incorrect");
        }
    });

    if (isCorrect) score++;

    document.getElementById("correct-answer-text").textContent = `Correct Answer: ${question.correct_answer}`;
    document.getElementById("explanation-text").textContent = question.explanation;
    document.getElementById("answer-reveal").classList.remove("hidden");
    document.getElementById("submit-btn").classList.add("hidden");
    document.getElementById("next-btn").classList.remove("hidden");
}

function nextQuestion() {
    currentQuestion++;

    if (currentQuestion >= questions.length) {
        showScore();
        return;
    }

    document.getElementById("answer-reveal").classList.add("hidden");
    document.getElementById("submit-btn").classList.remove("hidden");
    document.getElementById("next-btn").classList.add("hidden");
    selectedOption = null;

    renderQuestion();
}

function showScore() {
    document.getElementById("quiz-container").classList.add("hidden");
    document.getElementById("score-card").classList.remove("hidden");
    document.getElementById("score-text").textContent = `${score} / ${questions.length}`;

    const percentage = (score / questions.length) * 100;
    let message = "";
    if (percentage >= 80) message = "Excellent! You're well prepared.";
    else if (percentage >= 60) message = "Good effort! Keep studying.";
    else message = "Keep revising. You'll improve!";

    document.getElementById("score-message").textContent = message;
}

function renderQuestion() {
    const question = questions[currentQuestion];

    document.getElementById("question-number").textContent = `Question ${currentQuestion + 1} of ${questions.length}`;
    document.getElementById("question-text").textContent = question.question;
    document.getElementById("progress-bar").style.width = `${((currentQuestion + 1) / questions.length) * 100}%`;

    const optionsContainer = document.getElementById("options-container");
    optionsContainer.innerHTML = question.options.map((option, i) => `
        <button class="option-btn" onclick="selectOption(${i})">${escapeHtml(option)}</button>
    `).join("");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function loadQuiz() {
    const loading = document.getElementById("loading");
    const noQuiz = document.getElementById("no-quiz");
    const container = document.getElementById("quiz-container");

    try {
        const response = await fetch("/quiz/today");
        if (!response.ok) {
            loading.classList.add("hidden");
            noQuiz.classList.remove("hidden");
            return;
        }

        const data = await response.json();
        questions = data.questions;

        if (questions.length === 0) {
            loading.classList.add("hidden");
            noQuiz.classList.remove("hidden");
            return;
        }

        document.getElementById("quiz-date").textContent = new Date(data.date).toLocaleDateString("en-IN", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
        });

        loading.classList.add("hidden");
        container.classList.remove("hidden");
        renderQuestion();
    } catch (err) {
        loading.classList.add("hidden");
        noQuiz.textContent = "Failed to load quiz. Please try again.";
        noQuiz.classList.remove("hidden");
    }
}

window.selectOption = selectOption;
window.submitAnswer = submitAnswer;
window.nextQuestion = nextQuestion;

document.getElementById("submit-btn").addEventListener("click", submitAnswer);
document.getElementById("next-btn").addEventListener("click", nextQuestion);
