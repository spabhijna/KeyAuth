// KeyAuth Extension - Content Script for Gmail Login Detection

(function() {
  'use strict';
  
  let loginIntercepted = false;
  let capturedEmail = null;
  let verificationComplete = false; // Bypass flag after successful verification
  
  // Check if we're on a Google sign-in page
  function isGoogleSignInPage() {
    return window.location.href.includes('accounts.google.com') &&
           (window.location.href.includes('signin') || 
            window.location.href.includes('ServiceLogin') ||
            window.location.href.includes('identifier'));
  }
  
  // Find the email input field
  function findEmailInput() {
    return document.querySelector('input[type="email"]') ||
           document.querySelector('input#identifierId') ||
           document.querySelector('input[name="identifier"]');
  }
  
  // Find the password input field
  function findPasswordInput() {
    return document.querySelector('input[type="password"]') ||
           document.querySelector('input[name="password"]') ||
           document.querySelector('input[name="Passwd"]');
  }
  
  // Find the Next/Sign in button
  function findSubmitButton() {
    // Password page button takes priority - try multiple selectors
    const passwordNext = document.querySelector('#passwordNext');
    if (passwordNext) {
      console.log('KeyAuth: Found #passwordNext button');
      return passwordNext;
    }
    
    // Try the inner button/span inside passwordNext div
    const passwordNextBtn = document.querySelector('#passwordNext button') || 
                           document.querySelector('#passwordNext span[role="button"]');
    if (passwordNextBtn) {
      console.log('KeyAuth: Found #passwordNext inner element');
      return passwordNextBtn;
    }
    
    // Then try identifier page button
    const identifierNext = document.querySelector('#identifierNext');
    if (identifierNext) {
      console.log('KeyAuth: Found #identifierNext button');
      return identifierNext;
    }
    
    // Try VfPpkd button class (Material Design buttons Google uses)
    const materialBtn = document.querySelector('.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-k8QpJ');
    if (materialBtn) {
      console.log('KeyAuth: Found Material Design button');
      return materialBtn;
    }
    
    // Fallback to generic selectors
    const fallback = document.querySelector('[data-primary-action-label]') ||
                     document.querySelector('button[type="submit"]');
    console.log('KeyAuth: Using fallback button:', fallback);
    return fallback;
  }
  
  // Capture email when user enters it
  function captureEmail() {
    const emailInput = findEmailInput();
    if (emailInput && emailInput.value) {
      capturedEmail = emailInput.value.trim().toLowerCase();
      // Store in extension storage
      chrome.storage.local.set({ pendingGmailEmail: capturedEmail });
    }
  }
  
  // Check verification status before allowing login
  async function checkVerification(email) {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'checkVerified',
        email: email
      });
      return response.verified;
    } catch (err) {
      console.error('KeyAuth: Error checking verification', err);
      return false;
    }
  }
  
  // Show overlay blocking login until verified
  function showVerificationOverlay() {
    // Remove existing overlay if any
    const existing = document.getElementById('keyauth-overlay');
    if (existing) existing.remove();
    
    const overlay = document.createElement('div');
    overlay.id = 'keyauth-overlay';
    overlay.innerHTML = `
      <div class="keyauth-modal">
        <div class="keyauth-header">
          <span class="keyauth-icon">🔐</span>
          <h2>KeyAuth Verification Required</h2>
        </div>
        <p>Additional typing biometrics verification is required to proceed with Gmail login.</p>
        <p class="keyauth-email">Email: <strong>${capturedEmail || 'Unknown'}</strong></p>
        <button id="keyauth-verify-btn">Open Verification</button>
        <button id="keyauth-cancel-btn" class="secondary">Cancel</button>
      </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      #keyauth-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        z-index: 999999;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      .keyauth-modal {
        background: white;
        padding: 40px;
        border-radius: 12px;
        max-width: 400px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      }
      .keyauth-header {
        margin-bottom: 20px;
      }
      .keyauth-icon {
        font-size: 48px;
        display: block;
        margin-bottom: 10px;
      }
      .keyauth-modal h2 {
        color: #333;
        margin: 0;
        font-size: 22px;
      }
      .keyauth-modal p {
        color: #666;
        margin: 15px 0;
        line-height: 1.5;
      }
      .keyauth-email {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
      }
      .keyauth-modal button {
        width: 100%;
        padding: 14px;
        margin-top: 10px;
        border: none;
        border-radius: 6px;
        font-size: 16px;
        cursor: pointer;
        transition: background 0.3s;
      }
      #keyauth-verify-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
      #keyauth-verify-btn:hover {
        opacity: 0.9;
      }
      #keyauth-cancel-btn {
        background: #e0e0e0;
        color: #333;
      }
      #keyauth-cancel-btn:hover {
        background: #d0d0d0;
      }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(overlay);
    
    // Handle verify button - open extension popup
    document.getElementById('keyauth-verify-btn').addEventListener('click', () => {
      // Send message to background to trigger verification
      chrome.runtime.sendMessage({
        action: 'gmailLoginDetected',
        email: capturedEmail
      });
      
      // Start polling for verification completion
      startVerificationPolling();
      
      // Open extension popup by simulating click on extension icon
      // Note: Can't programmatically open popup, so show instructions
      overlay.querySelector('.keyauth-modal').innerHTML = `
        <div class="keyauth-header">
          <span class="keyauth-icon">👆</span>
          <h2>Click Extension Icon</h2>
        </div>
        <p>Click the <strong>KeyAuth</strong> extension icon in your browser toolbar to complete verification.</p>
        <p style="font-size: 13px; color: #888;">Look for the 🔐 icon in the top-right of your browser.</p>
        <button id="keyauth-done-btn">I've Completed Verification</button>
        <button id="keyauth-cancel-btn" class="secondary">Cancel</button>
      `;
      
      document.getElementById('keyauth-done-btn').addEventListener('click', async () => {
        const verified = await checkVerification(capturedEmail);
        if (verified) {
          removeOverlay();
          proceedWithLogin();
        } else {
          alert('Verification not completed. Please try again.');
        }
      });
      
      document.getElementById('keyauth-cancel-btn').addEventListener('click', removeOverlay);
    });
    
    // Handle cancel button
    document.getElementById('keyauth-cancel-btn').addEventListener('click', removeOverlay);
  }
  
  function removeOverlay() {
    const overlay = document.getElementById('keyauth-overlay');
    if (overlay) overlay.remove();
    loginIntercepted = false;
  }
  
  function proceedWithLogin() {
    // Set bypass flag to prevent re-interception
    verificationComplete = true;
    
    // Remove overlay first
    removeOverlay();
    
    // Re-enable form submission
    loginIntercepted = false;
    
    console.log('KeyAuth: proceedWithLogin called, verificationComplete =', verificationComplete);
    
    // Try clicking button with multiple attempts
    let attempts = 0;
    const maxAttempts = 5;
    
    function tryClick() {
      attempts++;
      const submitBtn = findSubmitButton();
      console.log('KeyAuth: Attempt', attempts, '- found button:', submitBtn);
      
      if (submitBtn) {
        console.log('KeyAuth: Clicking button...');
        
        // Method 1: Direct click
        submitBtn.click();
        
        // Method 2: Dispatch mouse event
        const clickEvent = new MouseEvent('click', {
          bubbles: true,
          cancelable: true,
          view: window
        });
        submitBtn.dispatchEvent(clickEvent);
        
        // Method 3: Try pressing Enter key on password field
        const passwordInput = findPasswordInput();
        if (passwordInput) {
          passwordInput.focus();
          const enterEvent = new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
          });
          passwordInput.dispatchEvent(enterEvent);
        }
        
        // Method 4: Try submitting the form directly
        const form = submitBtn.closest('form');
        if (form) {
          console.log('KeyAuth: Submitting form directly');
          form.submit();
        }
      } else if (attempts < maxAttempts) {
        // Button not found yet, try again after a short delay
        setTimeout(tryClick, 200);
      } else {
        console.log('KeyAuth: Could not find submit button after', maxAttempts, 'attempts');
        // Last resort - try submitting any form with password field
        const passwordInput = findPasswordInput();
        if (passwordInput) {
          const form = passwordInput.closest('form');
          if (form) {
            console.log('KeyAuth: Submitting password form as last resort');
            form.submit();
          }
        }
      }
    }
    
    // Start with a small delay to let overlay removal complete
    setTimeout(tryClick, 150);
  }
  
  // Intercept password form submission
  function interceptPasswordSubmit(event) {
    // If verification already completed, allow login to proceed
    if (verificationComplete) {
      console.log('KeyAuth: Verification complete, allowing login');
      return;
    }
    
    if (loginIntercepted) return;
    
    const passwordInput = findPasswordInput();
    if (!passwordInput || !passwordInput.value) return;
    
    // Get stored email
    chrome.storage.local.get(['pendingGmailEmail'], async (result) => {
      capturedEmail = result.pendingGmailEmail;
      
      if (!capturedEmail) {
        // Try to get from page
        const emailDisplay = document.querySelector('[data-email]') ||
                            document.querySelector('.Hj');
        if (emailDisplay) {
          capturedEmail = emailDisplay.textContent || emailDisplay.getAttribute('data-email');
        }
      }
      
      // Check if already verified recently
      const verified = await checkVerification(capturedEmail);
      
      if (!verified) {
        // Block login and show verification
        event.preventDefault();
        event.stopPropagation();
        loginIntercepted = true;
        showVerificationOverlay();
      }
    });
  }
  
  // Listen for form submissions
  function setupInterception() {
    // Watch for email input changes
    const emailInput = findEmailInput();
    if (emailInput) {
      emailInput.addEventListener('blur', captureEmail);
      emailInput.addEventListener('change', captureEmail);
    }
    
    // Watch for Next button click (captures email before moving to password)
    const nextBtn = document.getElementById('identifierNext');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        setTimeout(captureEmail, 100);
      });
    }
    
    // Watch for password form
    const passwordInput = findPasswordInput();
    if (passwordInput) {
      // Find parent form
      const form = passwordInput.closest('form');
      if (form) {
        form.addEventListener('submit', interceptPasswordSubmit, true);
      }
      
      // Also watch the Next/Submit button on password page
      const passwordNext = document.getElementById('passwordNext');
      if (passwordNext) {
        passwordNext.addEventListener('click', interceptPasswordSubmit, true);
      }
    }
  }
  
  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('KeyAuth content script received message:', request.action);
    if (request.action === 'proceedWithLogin') {
      console.log('KeyAuth: Received proceedWithLogin, removing overlay and clicking button');
      proceedWithLogin();
      sendResponse({ success: true });
    }
    return true;
  });
  
  // Listen for storage changes (backup communication method)
  chrome.storage.onChanged.addListener((changes, namespace) => {
    console.log('KeyAuth: Storage changed:', namespace, Object.keys(changes));
    if (namespace === 'local' && changes.proceedWithGmailLogin) {
      if (changes.proceedWithGmailLogin.newValue === true) {
        console.log('KeyAuth: Detected proceedWithGmailLogin storage flag');
        // Clear the flag
        chrome.storage.local.remove(['proceedWithGmailLogin']);
        // Proceed with login
        proceedWithLogin();
      }
    }
  });
  
  // Also poll for verification completion (backup for storage.onChanged)
  function startVerificationPolling() {
    console.log('KeyAuth: Starting verification polling');
    const pollInterval = setInterval(async () => {
      const { proceedWithGmailLogin } = await chrome.storage.local.get(['proceedWithGmailLogin']);
      if (proceedWithGmailLogin === true) {
        console.log('KeyAuth: Poll detected proceedWithGmailLogin flag');
        clearInterval(pollInterval);
        chrome.storage.local.remove(['proceedWithGmailLogin']);
        proceedWithLogin();
      }
    }, 500); // Check every 500ms
    
    // Stop polling after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      console.log('KeyAuth: Stopped verification polling (timeout)');
    }, 5 * 60 * 1000);
  }
  
  // Initialize with a slight delay to ensure page is loaded
  function init() {
    if (isGoogleSignInPage()) {
      console.log('KeyAuth: Google sign-in page detected, setting up interception');
      setupInterception();
      
      // Re-run setup when page content changes (Google uses dynamic loading)
      const observer = new MutationObserver(() => {
        setupInterception();
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }
  
  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
