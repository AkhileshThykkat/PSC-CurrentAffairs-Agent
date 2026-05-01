let questions = [];
let currentQuestion = 0;
let score = 0;
let selectedOption = null;

document.addEventListener("DOMContentLoaded", () => {
    loadQuiz();

    const submitBtn = document.getElementById("submit-btn");
    const nextBtn = document.getElementById("next-btn");
    const regenBtn = document.getElementById("regenerate-btn");
    if (submitBtn) submitBtn.addEventListener("click", submitAnswer);
    if (nextBtn) nextBtn.addEventListener("click", nextQuestion);
    if (regenBtn) regenBtn.addEventListener("click", regenerateQuiz);

    const takeAnotherBtn = document.getElementById("take-another-btn");
    if (takeAnotherBtn) takeAnotherBtn.addEventListener("click", regenerateQuiz);

    document.getElementById("options-container").addEventListener("click", (e) => {
        const btn = e.target.closest(".option-btn");
        if (!btn || btn.disabled) return;
        const idx = parseInt(btn.dataset.index);
        selectOption(idx);
    });
});

function selectOption(index) {
    selectedOption = index;
    const buttons = document.querySelectorAll(".option-btn");
    buttons.forEach((btn, i) => {
        if (i === index) {
            btn.classList.add("ring-2", "ring-green-600", "bg-green-50");
        } else {
            btn.classList.remove("ring-2", "ring-green-600", "bg-green-50");
        }
    });
    document.getElementById("submit-btn").disabled = false;
}

function submitAnswer() {
    if (selectedOption === null) return;

    const question = questions[currentQuestion];
    const isCorrect = question.options[selectedOption] === question.correct_answer;
    const buttons = document.querySelectorAll(".option-btn");

    buttons.forEach((btn, i) => {
        btn.disabled = true;
        btn.classList.remove("ring-2", "ring-green-600", "bg-green-50");
        if (question.options[i] === question.correct_answer) {
            btn.classList.add("bg-green-100", "border-green-600");
        } else if (i === selectedOption && !isCorrect) {
            btn.classList.add("bg-red-100", "border-red-400");
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
    document.getElementById("submit-btn").disabled = true;
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
    optionsContainer.innerHTML = "";
    question.options.forEach((option, i) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "option-btn cursor-pointer border border-slate-300 rounded-lg px-4 py-3 text-left text-sm hover:bg-slate-50 transition-colors w-full";
        btn.dataset.index = i;
        btn.textContent = option;
        optionsContainer.appendChild(btn);
    });
}

async function loadQuiz() {
    const loading = document.getElementById("loading");
    const noQuiz = document.getElementById("no-quiz");
    const container = document.getElementById("quiz-container");

    try {
        const response = await fetch("/api/quiz/today");
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

async function regenerateQuiz() {
    const regenBtn = document.getElementById("regenerate-btn");
    const loading = document.getElementById("loading");
    const container = document.getElementById("quiz-container");
    const noQuiz = document.getElementById("no-quiz");

    regenBtn.disabled = true;
    regenBtn.textContent = "Generating...";

    try {
        const response = await fetch("/api/quiz/regenerate", { method: "POST" });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            regenBtn.textContent = "Regenerate";
            regenBtn.disabled = false;
            alert(errData.detail || "Failed to regenerate quiz.");
            return;
        }

        const data = await response.json();
        questions = data.questions;
        currentQuestion = 0;
        score = 0;
        selectedOption = null;

        document.getElementById("answer-reveal").classList.add("hidden");
        document.getElementById("submit-btn").classList.remove("hidden");
        document.getElementById("submit-btn").disabled = true;
        document.getElementById("next-btn").classList.add("hidden");
        document.getElementById("score-card").classList.add("hidden");
        container.classList.remove("hidden");

        document.getElementById("quiz-date").textContent = new Date(data.date).toLocaleDateString("en-IN", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
        });

        renderQuestion();
    } catch (err) {
        alert("Failed to regenerate quiz. Please try again.");
    } finally {
        regenBtn.textContent = "Regenerate";
        regenBtn.disabled = false;
    }
}
