// KeyAuth Extension - Options/Settings Script

const DEFAULT_API_URL = 'http://localhost:8000';
const DEFAULT_SESSION_DURATION = 30;

// DOM Elements
const apiUrlInput = document.getElementById('apiUrl');
const sessionDurationInput = document.getElementById('sessionDuration');
const currentUser = document.getElementById('currentUser');
const currentEmail = document.getElementById('currentEmail');
const logoutBtn = document.getElementById('logoutBtn');
const retrainBtn = document.getElementById('retrainBtn');
const saveBtn = document.getElementById('saveBtn');
const resetBtn = document.getElementById('resetBtn');
const settingsMessage = document.getElementById('settingsMessage');

// Load settings
async function loadSettings() {
  const data = await chrome.storage.local.get([
    'apiUrl',
    'sessionDuration',
    'user_id',
    'username',
    'email'
  ]);
  
  apiUrlInput.value = data.apiUrl || DEFAULT_API_URL;
  sessionDurationInput.value = data.sessionDuration || DEFAULT_SESSION_DURATION;
  
  if (data.username) {
    currentUser.textContent = data.username;
    currentEmail.textContent = data.email || '-';
    logoutBtn.disabled = false;
    retrainBtn.disabled = false;
  } else {
    currentUser.textContent = 'Not logged in';
    currentEmail.textContent = '-';
    logoutBtn.disabled = true;
    retrainBtn.disabled = true;
  }
}

// Save settings
saveBtn.addEventListener('click', async () => {
  const apiUrl = apiUrlInput.value.trim();
  const sessionDuration = parseInt(sessionDurationInput.value) || DEFAULT_SESSION_DURATION;
  
  // Validate API URL
  if (!apiUrl) {
    showMessage('Please enter a valid API URL', 'error');
    return;
  }
  
  // Validate session duration
  if (sessionDuration < 5 || sessionDuration > 120) {
    showMessage('Session duration must be between 5 and 120 minutes', 'error');
    return;
  }
  
  try {
    await chrome.storage.local.set({
      apiUrl,
      sessionDuration
    });
    showMessage('Settings saved successfully!', 'success');
  } catch (err) {
    showMessage('Failed to save settings', 'error');
  }
});

// Reset to defaults
resetBtn.addEventListener('click', async () => {
  apiUrlInput.value = DEFAULT_API_URL;
  sessionDurationInput.value = DEFAULT_SESSION_DURATION;
  
  await chrome.storage.local.set({
    apiUrl: DEFAULT_API_URL,
    sessionDuration: DEFAULT_SESSION_DURATION
  });
  
  showMessage('Settings reset to defaults', 'success');
});

// Logout
logoutBtn.addEventListener('click', async () => {
  await chrome.runtime.sendMessage({ action: 'clearUser' });
  loadSettings();
  showMessage('Logged out successfully', 'success');
});

// Retrain - opens register page in training mode
retrainBtn.addEventListener('click', () => {
  // For now, open the register page
  // In a full implementation, this would skip step 1 and go directly to training
  showMessage('Feature coming soon - please re-register to retrain', 'info');
});

function showMessage(text, type) {
  settingsMessage.textContent = text;
  settingsMessage.className = `message ${type}`;
  
  // Clear after 3 seconds
  setTimeout(() => {
    settingsMessage.textContent = '';
    settingsMessage.className = 'message';
  }, 3000);
}

// Initialize
loadSettings();
