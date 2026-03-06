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
    
    // Check if typing verification failed but OTP fallback is available
    if (data.status === 'suspicious' && data.fallback_available) {
      showOtpFallback();
      return;
    }
    
    localStorage.setItem('verificationResult', JSON.stringify(data));
    window.location.href = 'success.html';
  } catch (err) {
    alert('Cannot connect to server');
    verifyBtn.disabled = false;
    verifyBtn.textContent = 'Verify';
  }
});

// =====================
// OTP Fallback Handlers
// =====================

function showOtpFallback() {
  // Hide typing section elements and disable input
  document.querySelector('.instruction').style.display = 'none';
  document.getElementById('phraseDisplay').style.display = 'none';
  input.style.display = 'none';
  input.disabled = true;  // Prevent capturing keystrokes
  input.blur();  // Remove focus
  matchStatus.style.display = 'none';
  verifyBtn.style.display = 'none';
  
  // Show OTP section
  document.getElementById('otpSection').style.display = 'block';
}

// Request OTP
document.getElementById('requestOtpBtn')?.addEventListener('click', async () => {
  const userId = localStorage.getItem('user_id');
  const requestBtn = document.getElementById('requestOtpBtn');
  const otpMessage = document.getElementById('otpMessage');
  
  requestBtn.disabled = true;
  requestBtn.textContent = 'Sending...';
  otpMessage.textContent = '';
  
  try {
    const res = await fetch('http://localhost:8000/request-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: parseInt(userId) })
    });
    const data = await res.json();
    
    if (res.ok && data.status === 'otp_sent') {
      // Show OTP input section
      requestBtn.style.display = 'none';
      const otpInputSection = document.getElementById('otpInputSection');
      otpInputSection.classList.add('visible');
      document.getElementById('otpSentMsg').textContent = data.message || 'OTP sent to your email. Valid for 5 minutes.';
      setTimeout(() => document.getElementById('otpInput').focus(), 100);
    } else {
      otpMessage.textContent = data.detail || 'Failed to send OTP';
      otpMessage.className = 'otp-message error';
      requestBtn.disabled = false;
      requestBtn.textContent = 'Send OTP to Email';
    }
  } catch (err) {
    otpMessage.textContent = 'Cannot connect to server';
    otpMessage.className = 'otp-message error';
    requestBtn.disabled = false;
    requestBtn.textContent = 'Send OTP to Email';
  }
});

// Verify OTP
document.getElementById('verifyOtpBtn')?.addEventListener('click', async () => {
  const userId = localStorage.getItem('user_id');
  const code = document.getElementById('otpInput').value.trim();
  const verifyOtpBtn = document.getElementById('verifyOtpBtn');
  const otpMessage = document.getElementById('otpMessage');
  
  if (code.length !== 6) {
    otpMessage.textContent = 'Please enter a 6-digit code';
    otpMessage.className = 'otp-message error';
    return;
  }
  
  verifyOtpBtn.disabled = true;
  verifyOtpBtn.textContent = 'Verifying...';
  otpMessage.textContent = '';
  
  try {
    const res = await fetch('http://localhost:8000/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: parseInt(userId), code: code })
    });
    const data = await res.json();
    
    if (res.ok && data.status === 'verified') {
      // OTP verified successfully - redirect to success page
      localStorage.setItem('verificationResult', JSON.stringify({
        status: 'verified',
        method: 'otp',
        message: 'Verified via OTP'
      }));
      window.location.href = 'success.html';
    } else {
      otpMessage.textContent = data.detail || 'Invalid or expired OTP';
      otpMessage.className = 'otp-message error';
      verifyOtpBtn.disabled = false;
      verifyOtpBtn.textContent = 'Verify OTP';
      document.getElementById('otpInput').value = '';
      document.getElementById('otpInput').focus();
    }
  } catch (err) {
    otpMessage.textContent = 'Cannot connect to server';
    otpMessage.className = 'otp-message error';
    verifyOtpBtn.disabled = false;
    verifyOtpBtn.textContent = 'Verify OTP';
  }
});

// Resend OTP
document.getElementById('resendOtpBtn')?.addEventListener('click', async () => {
  const userId = localStorage.getItem('user_id');
  const resendBtn = document.getElementById('resendOtpBtn');
  const otpMessage = document.getElementById('otpMessage');
  
  resendBtn.disabled = true;
  resendBtn.textContent = 'Sending...';
  otpMessage.textContent = '';
  
  try {
    const res = await fetch('http://localhost:8000/request-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: parseInt(userId) })
    });
    const data = await res.json();
    
    if (res.ok && data.status === 'otp_sent') {
      document.getElementById('otpSentMsg').textContent = 'New OTP sent to your email. Valid for 5 minutes.';
      document.getElementById('otpInput').value = '';
      document.getElementById('otpInput').focus();
    } else {
      otpMessage.textContent = data.detail || 'Failed to resend OTP';
      otpMessage.className = 'otp-message error';
    }
  } catch (err) {
    otpMessage.textContent = 'Cannot connect to server';
    otpMessage.className = 'otp-message error';
  }
  
  resendBtn.disabled = false;
  resendBtn.textContent = 'Resend OTP';
});

// Allow Enter key to verify OTP
document.getElementById('otpInput')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    document.getElementById('verifyOtpBtn')?.click();
  }
});

// Developer tools: Load sample from JSON
document.getElementById('loadSampleBtn')?.addEventListener('click', () => {
  document.getElementById('loadSampleInput').click();
});

document.getElementById('loadSampleInput')?.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const data = JSON.parse(event.target.result);
      // Can load either a single sample or pick first from samples array
      let sample = null;
      if (data.keystrokes) {
        sample = data.keystrokes;
      } else if (data.samples && data.samples.length > 0) {
        sample = data.samples[0];
      }
      
      if (sample && Array.isArray(sample)) {
        // Clear existing keystrokes and load new ones
        keystrokes.length = 0;
        sample.forEach(k => keystrokes.push(k));
        
        // Set input to match phrase
        input.value = REQUIRED_PHRASE;
        updateMatchStatus();
        
        document.getElementById('message').textContent = `Loaded sample with ${keystrokes.length} keystrokes`;
        document.getElementById('message').style.color = 'green';
      } else {
        alert('Invalid file format - need keystrokes or samples array');
      }
    } catch (err) {
      alert('Failed to parse JSON file');
    }
  };
  reader.readAsText(file);
  e.target.value = '';
});
