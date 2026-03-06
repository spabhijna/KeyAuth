let REQUIRED_PHRASE = '';
const keystrokes = [];
const input = document.getElementById('typingInput');
const verifyBtn = document.getElementById('verifyBtn');
const matchStatus = document.getElementById('matchStatus');
const phraseDisplay = document.getElementById('phraseDisplay');

// Fetch phrase from API on page load
async function loadPhrase() {
  try {
    const res = await fetch('http://localhost:8000/phrase');
    const data = await res.json();
    REQUIRED_PHRASE = data.phrase;
    phraseDisplay.textContent = REQUIRED_PHRASE;
  } catch (err) {
    REQUIRED_PHRASE = 'secure login verification';
    phraseDisplay.textContent = REQUIRED_PHRASE;
    console.error('Failed to fetch phrase, using default');
  }
}

loadPhrase();

input.addEventListener('keydown', (e) => {
  keystrokes.push({
    key: e.key,
    type: 'down',
    time: performance.now()
  });
});

input.addEventListener('keyup', (e) => {
  keystrokes.push({
    key: e.key,
    type: 'up',
    time: performance.now()
  });
  updateMatchStatus();
});

function updateMatchStatus() {
  const typed = input.value;
  if (typed === REQUIRED_PHRASE) {
    matchStatus.textContent = '✓ Phrase matches';
    matchStatus.className = 'match-status match';
    verifyBtn.disabled = false;
  } else {
    matchStatus.textContent = typed.length > 0 ? '✗ Phrase does not match yet' : '';
    matchStatus.className = 'match-status no-match';
    verifyBtn.disabled = true;
  }
}

verifyBtn.addEventListener('click', async () => {
  if (input.value !== REQUIRED_PHRASE) return;

  const userId = localStorage.getItem('user_id');
  if (!userId) {
    alert('Session expired. Please login again.');
    window.location.href = 'login.html';
    return;
  }

  verifyBtn.disabled = true;
  verifyBtn.textContent = 'Verifying...';

  try {
    const res = await fetch('http://localhost:8000/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: parseInt(userId), 
        keystrokes 
      })
    });
    const data = await res.json();
    
    if (!res.ok) {
      // Handle error responses (e.g., model not trained)
      alert(data.detail || 'Verification failed');
      verifyBtn.disabled = false;
      verifyBtn.textContent = 'Verify';
      return;
    }
    
    localStorage.setItem('verificationResult', JSON.stringify(data));
    window.location.href = 'dashboard.html';
  } catch (err) {
    alert('Cannot connect to server');
    verifyBtn.disabled = false;
    verifyBtn.textContent = 'Verify';
  }
});
