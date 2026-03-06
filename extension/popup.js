// KeyAuth Extension - Popup Script

let REQUIRED_PHRASE = '';
let keystrokes = [];
let currentUserId = null;

// DOM Elements
const loginSection = document.getElementById('loginSection');
const statusSection = document.getElementById('statusSection');
const verifySection = document.getElementById('verifySection');
const successSection = document.getElementById('successSection');
const otpSection = document.getElementById('otpSection');

const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginBtn = document.getElementById('loginBtn');
const loginMessage = document.getElementById('loginMessage');
const logoutBtn = document.getElementById('logoutBtn');
const statusLogoutBtn = document.getElementById('statusLogoutBtn');
const loggedInUser = document.getElementById('loggedInUser');
const statusUser = document.getElementById('statusUser');

const phraseDisplay = document.getElementById('phraseDisplay');
const typingInput = document.getElementById('typingInput');
const matchStatus = document.getElementById('matchStatus');
const verifyBtn = document.getElementById('verifyBtn');
const verifyMessage = document.getElementById('verifyMessage');

const gmailPending = document.getElementById('gmailPending');
const gmailEmail = document.getElementById('gmailEmail');

const confidenceScore = document.getElementById('confidenceScore');
const doneBtn = document.getElementById('doneBtn');

// Initialize popup
async function init() {
  // Check if user is logged in
  const userData = await chrome.runtime.sendMessage({ action: 'getStoredUser' });
  
  if (userData.user_id) {
    currentUserId = userData.user_id;
    
    // Check if there's a pending Gmail login
    const gmailData = await chrome.storage.local.get(['pendingGmailLogin', 'gmailEmail']);
    
    if (gmailData.pendingGmailLogin && gmailData.gmailEmail) {
      // Show verification UI
      showVerifySection(userData.username, gmailData.gmailEmail);
      loadPhrase();
    } else {
      // Show status (no pending login)
      showStatusSection(userData.username);
    }
  } else {
    showLoginSection();
  }
}

function showLoginSection() {
  loginSection.style.display = 'block';
  statusSection.style.display = 'none';
  verifySection.style.display = 'none';
  successSection.style.display = 'none';
}

function showStatusSection(username) {
  loginSection.style.display = 'none';
  statusSection.style.display = 'block';
  verifySection.style.display = 'none';
  successSection.style.display = 'none';
  statusUser.textContent = username;
}

function showVerifySection(username, email) {
  loginSection.style.display = 'none';
  statusSection.style.display = 'none';
  verifySection.style.display = 'block';
  successSection.style.display = 'none';
  otpSection.style.display = 'none';
  loggedInUser.textContent = username;
  if (email) {
    gmailEmail.textContent = email;
  }
}

function showSuccessSection(confidence) {
  loginSection.style.display = 'none';
  statusSection.style.display = 'none';
  verifySection.style.display = 'none';
  successSection.style.display = 'block';
  
  // Hide confidence display for OTP verification (no confidence score)
  const confidenceEl = document.querySelector('.confidence');
  if (confidence !== null && confidence !== undefined) {
    confidenceScore.textContent = Math.round(confidence * 100);
    if (confidenceEl) confidenceEl.style.display = 'block';
  } else {
    if (confidenceEl) confidenceEl.style.display = 'none';
  }
}

function showOtpSection() {
  document.querySelector('.verify-box').style.display = 'none';
  otpSection.style.display = 'block';
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

// Keystroke capture
typingInput.addEventListener('keydown', (e) => {
  keystrokes.push({
    key: e.key,
    type: 'down',
    time: performance.now()
  });
});

typingInput.addEventListener('keyup', (e) => {
  keystrokes.push({
    key: e.key,
    type: 'up',
    time: performance.now()
  });
  updateMatchStatus();
});

function updateMatchStatus() {
  const typed = typingInput.value;
  if (typed === REQUIRED_PHRASE) {
    matchStatus.textContent = '✓ Phrase matches';
    matchStatus.className = 'match-status match';
    verifyBtn.disabled = false;
  } else {
    matchStatus.textContent = typed.length > 0 ? '✗ Keep typing...' : '';
    matchStatus.className = 'match-status no-match';
    verifyBtn.disabled = true;
  }
}

// Login handler
loginBtn.addEventListener('click', async () => {
  const username = usernameInput.value.trim();
  const password = passwordInput.value;
  
  if (!username || !password) {
    loginMessage.textContent = 'Please enter username and password';
    loginMessage.className = 'message error';
    return;
  }
  
  loginBtn.disabled = true;
  loginBtn.textContent = 'Logging in...';
  loginMessage.textContent = '';
  
  try {
    const data = await chrome.runtime.sendMessage({
      action: 'login',
      username,
      password
    });
    
    if (data.user_id) {
      currentUserId = data.user_id;
      
      // Check if there's a pending Gmail login
      const gmailData = await chrome.storage.local.get(['pendingGmailLogin', 'gmailEmail']);
      if (gmailData.pendingGmailLogin && gmailData.gmailEmail) {
        showVerifySection(username, gmailData.gmailEmail);
        loadPhrase();
      } else {
        showStatusSection(username);
      }
    }
  } catch (err) {
    loginMessage.textContent = err.message || 'Login failed';
    loginMessage.className = 'message error';
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = 'Login';
  }
});

// Verify handler
verifyBtn.addEventListener('click', async () => {
  if (typingInput.value !== REQUIRED_PHRASE) return;
  
  verifyBtn.disabled = true;
  verifyBtn.textContent = 'Verifying...';
  verifyMessage.textContent = '';
  
  try {
    const data = await chrome.runtime.sendMessage({
      action: 'verify',
      user_id: currentUserId,
      keystrokes
    });
    
    if (data.status === 'verified') {
      // Mark as verified for Gmail
      const gmailData = await chrome.storage.local.get(['gmailEmail']);
      if (gmailData.gmailEmail) {
        await chrome.runtime.sendMessage({
          action: 'setVerified',
          email: gmailData.gmailEmail
        });
      }
      
      // Set flag for content script to pick up and proceed
      console.log('KeyAuth popup: Setting proceedWithGmailLogin flag to true');
      await chrome.storage.local.set({ proceedWithGmailLogin: true });
      
      // Verify it was set
      const checkSet = await chrome.storage.local.get(['proceedWithGmailLogin']);
      console.log('KeyAuth popup: Verified flag is set:', checkSet);
      
      // Clear pending Gmail login state
      await chrome.storage.local.remove(['pendingGmailLogin', 'gmailEmail']);
      
      // Also try direct message to content script
      try {
        const tabs = await chrome.tabs.query({ url: 'https://accounts.google.com/*' });
        console.log('KeyAuth: Found Google tabs:', tabs.length);
        for (const tab of tabs) {
          try {
            await chrome.tabs.sendMessage(tab.id, { action: 'proceedWithLogin' });
            console.log('KeyAuth: Sent proceedWithLogin to tab', tab.id);
          } catch (e) {
            console.log('KeyAuth: Could not send to tab', tab.id, e);
          }
        }
      } catch (err) {
        console.error('KeyAuth: Error sending proceedWithLogin:', err);
      }
      
      showSuccessSection(data.confidence);
    } else if (data.status === 'suspicious' && data.fallback_available) {
      showOtpSection();
    } else {
      verifyMessage.textContent = 'Verification failed. Please try again.';
      verifyMessage.className = 'message error';
      resetTyping();
    }
  } catch (err) {
    verifyMessage.textContent = err.message || 'Verification failed';
    verifyMessage.className = 'message error';
  } finally {
    verifyBtn.disabled = false;
    verifyBtn.textContent = 'Verify Identity';
  }
});

// Reset typing for retry
function resetTyping() {
  typingInput.value = '';
  keystrokes = [];
  matchStatus.textContent = '';
  verifyBtn.disabled = true;
}

// Logout handler
logoutBtn.addEventListener('click', async () => {
  await chrome.runtime.sendMessage({ action: 'clearUser' });
  currentUserId = null;
  showLoginSection();
  usernameInput.value = '';
  passwordInput.value = '';
  loginMessage.textContent = '';
});

// Status section logout handler
statusLogoutBtn.addEventListener('click', async () => {
  await chrome.runtime.sendMessage({ action: 'clearUser' });
  currentUserId = null;
  showLoginSection();
  usernameInput.value = '';
  passwordInput.value = '';
  loginMessage.textContent = '';
});

// OTP handlers
document.getElementById('requestOtpBtn')?.addEventListener('click', async () => {
  const btn = document.getElementById('requestOtpBtn');
  btn.disabled = true;
  btn.textContent = 'Sending...';
  
  try {
    const data = await chrome.runtime.sendMessage({
      action: 'requestOtp',
      user_id: currentUserId
    });
    
    if (data.status === 'otp_sent') {
      btn.style.display = 'none';
      document.getElementById('otpInputSection').style.display = 'block';
      document.getElementById('otpSentMsg').textContent = data.message;
      document.getElementById('otpInput').focus();
    }
  } catch (err) {
    document.getElementById('otpMessage').textContent = err.message;
    document.getElementById('otpMessage').className = 'message error';
    btn.disabled = false;
    btn.textContent = 'Send OTP to Email';
  }
});

document.getElementById('verifyOtpBtn')?.addEventListener('click', async () => {
  const code = document.getElementById('otpInput').value.trim();
  if (code.length !== 6) {
    document.getElementById('otpMessage').textContent = 'Enter 6-digit code';
    document.getElementById('otpMessage').className = 'message error';
    return;
  }
  
  const btn = document.getElementById('verifyOtpBtn');
  btn.disabled = true;
  btn.textContent = 'Verifying...';
  
  try {
    const data = await chrome.runtime.sendMessage({
      action: 'verifyOtp',
      user_id: currentUserId,
      code
    });
    
    if (data.status === 'verified') {
      // Mark as verified and clear pending state
      const gmailData = await chrome.storage.local.get(['gmailEmail']);
      if (gmailData.gmailEmail) {
        await chrome.runtime.sendMessage({
          action: 'setVerified',
          email: gmailData.gmailEmail
        });
      }
      
      // Set flag for content script to pick up and proceed
      console.log('KeyAuth popup (OTP): Setting proceedWithGmailLogin flag to true');
      await chrome.storage.local.set({ proceedWithGmailLogin: true });
      
      // Verify it was set
      const checkSet = await chrome.storage.local.get(['proceedWithGmailLogin']);
      console.log('KeyAuth popup (OTP): Verified flag is set:', checkSet);
      
      // Clear pending Gmail login state
      await chrome.storage.local.remove(['pendingGmailLogin', 'gmailEmail']);
      
      // Also try direct message to content script
      try {
        const tabs = await chrome.tabs.query({ url: 'https://accounts.google.com/*' });
        console.log('KeyAuth: Found Google tabs (OTP):', tabs.length);
        for (const tab of tabs) {
          try {
            await chrome.tabs.sendMessage(tab.id, { action: 'proceedWithLogin' });
            console.log('KeyAuth: Sent proceedWithLogin to tab', tab.id);
          } catch (e) {
            console.log('KeyAuth: Could not send to tab', tab.id, e);
          }
        }
      } catch (err) {
        console.error('KeyAuth: Error sending proceedWithLogin:', err);
      }
      
      showSuccessSection(null); // OTP doesn't have confidence score
    } else {
      document.getElementById('otpMessage').textContent = data.message || 'Invalid code';
      document.getElementById('otpMessage').className = 'message error';
    }
  } catch (err) {
    document.getElementById('otpMessage').textContent = err.message;
    document.getElementById('otpMessage').className = 'message error';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Verify OTP';
  }
});

document.getElementById('retryTypingBtn')?.addEventListener('click', () => {
  otpSection.style.display = 'none';
  document.querySelector('.verify-box').style.display = 'block';
  resetTyping();
  typingInput.focus();
});

// Done button - close popup after success
doneBtn.addEventListener('click', async () => {
  // Set storage flag (backup - should already be set on verification success)
  await chrome.storage.local.set({ proceedWithGmailLogin: true });
  
  // Also try direct message
  try {
    const tabs = await chrome.tabs.query({ url: 'https://accounts.google.com/*' });
    for (const tab of tabs) {
      try {
        await chrome.tabs.sendMessage(tab.id, { action: 'proceedWithLogin' });
      } catch (e) {
        // Ignore errors for individual tabs
      }
    }
  } catch (err) {
    console.error('KeyAuth: Error in done button:', err);
  }
  window.close();
});

// Enter key handlers
usernameInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') passwordInput.focus();
});

passwordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') loginBtn.click();
});

// Initialize on load
init();
