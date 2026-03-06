// KeyAuth Extension - Registration Script

const REQUIRED_SAMPLES = 20;
let REQUIRED_PHRASE = '';
let samples = [];
let currentKeystrokes = [];

// Account details
let accountData = {
  username: '',
  email: '',
  password: ''
};

// DOM Elements
const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');
const step3 = document.getElementById('step3');

const usernameInput = document.getElementById('username');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const nextStepBtn = document.getElementById('nextStepBtn');
const step1Message = document.getElementById('step1Message');

const phraseDisplay = document.getElementById('phraseDisplay');
const typingInput = document.getElementById('typingInput');
const matchStatus = document.getElementById('matchStatus');
const submitSampleBtn = document.getElementById('submitSampleBtn');
const registerBtn = document.getElementById('registerBtn');
const step2Message = document.getElementById('step2Message');
const sampleCount = document.getElementById('sampleCount');
const progressFill = document.getElementById('progressFill');
const backBtn = document.getElementById('backBtn');

const goToLoginBtn = document.getElementById('goToLoginBtn');

// Initialize
async function init() {
  await loadPhrase();
}

// Load phrase from API
async function loadPhrase() {
  try {
    const data = await chrome.runtime.sendMessage({ action: 'getPhrase' });
    REQUIRED_PHRASE = data.phrase;
    phraseDisplay.textContent = REQUIRED_PHRASE;
  } catch (err) {
    REQUIRED_PHRASE = 'secure login verification';
    phraseDisplay.textContent = REQUIRED_PHRASE;
    console.error('Failed to fetch phrase:', err);
  }
}

// Step 1: Validate account details
nextStepBtn.addEventListener('click', () => {
  const username = usernameInput.value.trim();
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  const confirmPassword = confirmPasswordInput.value;
  
  // Validation
  if (!username || username.length < 3) {
    showMessage(step1Message, 'Username must be at least 3 characters', 'error');
    return;
  }
  
  if (!email || !isValidEmail(email)) {
    showMessage(step1Message, 'Please enter a valid email address', 'error');
    return;
  }
  
  if (!password || password.length < 6) {
    showMessage(step1Message, 'Password must be at least 6 characters', 'error');
    return;
  }
  
  if (password !== confirmPassword) {
    showMessage(step1Message, 'Passwords do not match', 'error');
    return;
  }
  
  // Store account data
  accountData = { username, email, password };
  
  // Move to step 2
  step1.style.display = 'none';
  step2.style.display = 'block';
  typingInput.focus();
});

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Step 2: Keystroke capture
typingInput.addEventListener('keydown', (e) => {
  currentKeystrokes.push({
    key: e.key,
    type: 'down',
    time: performance.now()
  });
});

typingInput.addEventListener('keyup', (e) => {
  currentKeystrokes.push({
    key: e.key,
    type: 'up',
    time: performance.now()
  });
  updateMatchStatus();
});

function updateMatchStatus() {
  const typed = typingInput.value;
  if (typed === REQUIRED_PHRASE) {
    matchStatus.textContent = '✓ Phrase matches - Click Submit Sample';
    matchStatus.className = 'match-status match';
    submitSampleBtn.disabled = false;
  } else {
    matchStatus.textContent = typed.length > 0 ? '✗ Keep typing...' : '';
    matchStatus.className = 'match-status no-match';
    submitSampleBtn.disabled = true;
  }
}

// Submit sample
submitSampleBtn.addEventListener('click', () => {
  if (typingInput.value !== REQUIRED_PHRASE) return;
  
  // Store the sample
  samples.push([...currentKeystrokes]);
  
  // Update progress
  const count = samples.length;
  sampleCount.textContent = count;
  progressFill.style.width = `${(count / REQUIRED_SAMPLES) * 100}%`;
  
  // Reset for next sample
  typingInput.value = '';
  currentKeystrokes = [];
  matchStatus.textContent = '';
  submitSampleBtn.disabled = true;
  
  // Show success message briefly
  showMessage(step2Message, `Sample ${count} recorded!`, 'success');
  setTimeout(() => {
    step2Message.textContent = '';
  }, 1500);
  
  // Check if enough samples
  if (count >= REQUIRED_SAMPLES) {
    submitSampleBtn.style.display = 'none';
    registerBtn.style.display = 'block';
    showMessage(step2Message, '✓ Training complete! Click to register.', 'success');
  }
  
  typingInput.focus();
});

// Complete registration
registerBtn.addEventListener('click', async () => {
  registerBtn.disabled = true;
  registerBtn.textContent = 'Registering...';
  
  try {
    const data = await chrome.runtime.sendMessage({
      action: 'register',
      username: accountData.username,
      email: accountData.email,
      password: accountData.password,
      samples: samples
    });
    
    if (data.user_id) {
      // Success - show step 3
      step2.style.display = 'none';
      step3.style.display = 'block';
    } else {
      throw new Error('Registration failed');
    }
  } catch (err) {
    showMessage(step2Message, err.message || 'Registration failed', 'error');
    registerBtn.disabled = false;
    registerBtn.textContent = 'Complete Registration';
  }
});

// Back button
backBtn.addEventListener('click', () => {
  step2.style.display = 'none';
  step1.style.display = 'block';
});

// Go to login
goToLoginBtn.addEventListener('click', () => {
  window.location.href = 'popup.html';
});

// Helper function
function showMessage(element, text, type) {
  element.textContent = text;
  element.className = `message ${type}`;
}

// Enter key handlers
usernameInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') emailInput.focus();
});

emailInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') passwordInput.focus();
});

passwordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') confirmPasswordInput.focus();
});

confirmPasswordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') nextStepBtn.click();
});

// Initialize
init();
