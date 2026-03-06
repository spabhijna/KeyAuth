// KeyAuth Extension - Background Service Worker

const DEFAULT_API_URL = 'http://localhost:8000';

// Get API URL from storage or use default
async function getApiUrl() {
  const result = await chrome.storage.local.get(['apiUrl']);
  return result.apiUrl || DEFAULT_API_URL;
}

// API Helper function
async function apiRequest(endpoint, options = {}) {
  const apiUrl = await getApiUrl();
  const url = `${apiUrl}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json'
    }
  };
  
  const response = await fetch(url, { ...defaultOptions, ...options });
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || 'API request failed');
  }
  
  return data;
}

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender).then(sendResponse).catch(err => {
    sendResponse({ error: err.message });
  });
  return true; // Keep channel open for async response
});

async function handleMessage(request, sender) {
  switch (request.action) {
    case 'getPhrase':
      return await apiRequest('/phrase');
    
    case 'login':
      const loginData = await apiRequest('/login', {
        method: 'POST',
        body: JSON.stringify({
          username: request.username,
          password: request.password
        })
      });
      // Store user_id on successful login
      if (loginData.user_id) {
        await chrome.storage.local.set({ 
          user_id: loginData.user_id,
          username: request.username
        });
      }
      return loginData;
    
    case 'register':
      const registerData = await apiRequest('/register', {
        method: 'POST',
        body: JSON.stringify({
          username: request.username,
          email: request.email,
          password: request.password,
          samples: request.samples
        })
      });
      // Store user_id on successful registration
      if (registerData.user_id) {
        await chrome.storage.local.set({ 
          user_id: registerData.user_id,
          username: request.username,
          email: request.email
        });
      }
      return registerData;
    
    case 'verify':
      return await apiRequest('/verify', {
        method: 'POST',
        body: JSON.stringify({
          user_id: request.user_id,
          keystrokes: request.keystrokes
        })
      });
    
    case 'requestOtp':
      return await apiRequest('/request-otp', {
        method: 'POST',
        body: JSON.stringify({
          user_id: request.user_id
        })
      });
    
    case 'verifyOtp':
      return await apiRequest('/verify-otp', {
        method: 'POST',
        body: JSON.stringify({
          user_id: request.user_id,
          code: request.code
        })
      });
    
    case 'getUserByEmail':
      return await apiRequest(`/user-by-email?email=${encodeURIComponent(request.email)}`);
    
    case 'getStoredUser':
      return await chrome.storage.local.get(['user_id', 'username', 'email']);
    
    case 'clearUser':
      await chrome.storage.local.remove(['user_id', 'username', 'email', 'lastVerified']);
      return { success: true };
    
    case 'setVerified':
      await chrome.storage.local.set({ 
        lastVerified: Date.now(),
        verifiedEmail: request.email
      });
      return { success: true };
    
    case 'checkVerified':
      const stored = await chrome.storage.local.get(['lastVerified', 'verifiedEmail']);
      // Consider verified if within last 30 minutes
      const thirtyMinutes = 30 * 60 * 1000;
      const isVerified = stored.lastVerified && 
                         stored.verifiedEmail === request.email &&
                         (Date.now() - stored.lastVerified) < thirtyMinutes;
      return { verified: isVerified };
    
    case 'gmailLoginDetected':
      // Content script detected Gmail login - notify popup
      await chrome.storage.local.set({ 
        pendingGmailLogin: true,
        gmailEmail: request.email
      });
      return { success: true };
    
    case 'allowGmailLogin':
      // Clear pending state and allow login to proceed
      await chrome.storage.local.remove(['pendingGmailLogin', 'gmailEmail']);
      // Notify content script to proceed
      if (sender.tab) {
        chrome.tabs.sendMessage(sender.tab.id, { action: 'proceedWithLogin' });
      }
      return { success: true };
    
    default:
      throw new Error('Unknown action: ' + request.action);
  }
}

// Create context menu for quick access
chrome.runtime.onInstalled.addListener(() => {
  console.log('KeyAuth Extension installed');
});
