// DOM Elements
const form = document.getElementById('postForm');
const generateBtn = document.getElementById('generateBtn');
const outputArea = document.getElementById('outputArea');
const generatedPostDiv = document.getElementById('generatedPost');
const loadingState = document.getElementById('loadingState');
const errorMsgDiv = document.getElementById('errorMsg');
const copyBtn = document.getElementById('copyBtn');
const regenerateBtn = document.getElementById('regenerateBtn');
const topicInput = document.getElementById('topicInput');
const charCountSpan = document.getElementById('charCount');
const languageInput = document.getElementById('languageInput');
const userTypeInput = document.getElementById('userTypeInput');
const toneInput = document.getElementById('toneInput');
const lengthInput = document.getElementById('lengthInput');

// Language buttons
document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        languageInput.value = btn.dataset.lang;
    });
});

// User type buttons
document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        userTypeInput.value = btn.dataset.type;
    });
});

// Tone pills
document.querySelectorAll('.pill').forEach(pill => {
    pill.addEventListener('click', () => {
        document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        toneInput.value = pill.dataset.tone;
    });
});

// Length slider
const slider = document.getElementById('lengthSlider');
slider.addEventListener('input', (e) => {
    const val = parseInt(e.target.value);
    const map = {0: 'short', 1: 'medium', 2: 'long'};
    lengthInput.value = map[val];
});

// Character counter
topicInput.addEventListener('input', () => {
    charCountSpan.textContent = topicInput.value.length;
});

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('click', () => {
    const current = document.body.getAttribute('data-theme');
    if (current === 'light') {
        document.body.setAttribute('data-theme', 'dark');
    } else {
        document.body.setAttribute('data-theme', 'light');
    }
});

// Helper: loading state
function setLoading(loading) {
    if (loading) {
        generateBtn.querySelector('.btn-text').classList.add('hidden');
        generateBtn.querySelector('.loader').classList.remove('hidden');
        generateBtn.disabled = true;
        loadingState.classList.remove('hidden');
        generatedPostDiv.classList.add('hidden');
        errorMsgDiv.classList.add('hidden');
    } else {
        generateBtn.querySelector('.btn-text').classList.remove('hidden');
        generateBtn.querySelector('.loader').classList.add('hidden');
        generateBtn.disabled = false;
        loadingState.classList.add('hidden');
        generatedPostDiv.classList.remove('hidden');
    }
}

function showError(msg) {
    errorMsgDiv.textContent = msg;
    errorMsgDiv.classList.remove('hidden');
    setTimeout(() => errorMsgDiv.classList.add('hidden'), 6000);
}

// Typing animation
async function typeText(element, text, speed = 20) {
    element.textContent = '';
    for (let i = 0; i < text.length; i++) {
        element.textContent += text[i];
        await new Promise(r => setTimeout(r, speed));
    }
}

async function generatePost(isRegenerate = false) {
    const topic = topicInput.value.trim();
    if (!topic) {
        showError('Please enter a topic.');
        return;
    }
    const payload = {
        topic: topic,
        user_type: userTypeInput.value,
        tone: toneInput.value,
        length: lengthInput.value,
        language: languageInput.value
    };
    setLoading(true);
    try {
        const res = await fetch('/generate-post', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'API error');
        await typeText(generatedPostDiv, data.generated_post, 15);
        if (!isRegenerate) {
            document.querySelector('.output-panel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    } catch (err) {
        showError(err.message);
        generatedPostDiv.textContent = '✨ Failed to generate. Please try again.';
    } finally {
        setLoading(false);
    }
}

form.addEventListener('submit', (e) => {
    e.preventDefault();
    generatePost(false);
});

regenerateBtn.addEventListener('click', () => {
    if (topicInput.value.trim()) generatePost(true);
    else showError('Topic is empty, cannot regenerate.');
});

copyBtn.addEventListener('click', async () => {
    const text = generatedPostDiv.innerText;
    if (!text || text.includes('Your post will appear here')) return;
    try {
        await navigator.clipboard.writeText(text);
        const original = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => { copyBtn.innerHTML = original; }, 1500);
    } catch {
        showError('Manual copy needed');
    }
});

// Initial placeholder
generatedPostDiv.textContent = '✨ Your post will appear here...';