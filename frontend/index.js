/* ---------------------------------------------------------
    FRONTEND UI LOGIC 
--------------------------------------------------------- */
const API_URL = "http://127.0.0.1:8000";

const themeSelectorBtn = document.getElementById('themeSelectorBtn');
const themeOptions = document.getElementById('themeOptions');
const options = document.querySelectorAll('.theme-option');

// Load saved theme on page load
const savedTheme = localStorage.getItem('eventhub-theme') || 'light';
if (savedTheme !== 'light') {
    document.documentElement.setAttribute('data-theme', savedTheme);
}
updateActiveOption(savedTheme);

// Toggle dropdown visibility
themeSelectorBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    themeOptions.classList.toggle('active');
});

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    themeOptions.classList.remove('active');
});

// Prevent dropdown from closing when clicking inside it
themeOptions.addEventListener('click', (e) => e.stopPropagation());

// Handle theme selection
options.forEach(option => {
    option.addEventListener('click', () => {
        const theme = option.getAttribute('data-theme');
        if (theme === 'light') {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        localStorage.setItem('eventhub-theme', theme);
        updateActiveOption(theme);
        themeOptions.classList.remove('active');
    });
});

function updateActiveOption(currentTheme) {
    options.forEach(opt => {
        if (opt.getAttribute('data-theme') === currentTheme) {
            opt.classList.add('active');
        } else {
            opt.classList.remove('active');
        }
    });
}

// Redirect if already logged in
if (localStorage.getItem('token')) window.location.href = 'dashboard.html';

// Form Submission Wrappers
function handleLogin(event) {
    event.preventDefault();
    login();
}

function handleSignup(event) {
    event.preventDefault();
    signup();
}

// Tab Switching & Indicator Animation
function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-btn');
    const forms = document.querySelectorAll('.form-view');
    const indicator = document.querySelector('.indicator');
    
    // Clear errors via text content (relies on CSS :not(:empty))
    document.querySelectorAll('.error-msg').forEach(el => el.textContent = '');

    tabs.forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
            indicator.style.width = `${tab.offsetWidth}px`;
            indicator.style.left = `${tab.offsetLeft}px`;
        } else {
            tab.classList.remove('active');
        }
    });

    forms.forEach(form => {
        form.classList.toggle('active', form.id === `${tabName}-form`);
    });
}

// Initialize Indicator Position on Load & Resize
const updateIndicator = () => {
    const activeTab = document.querySelector('.tab-btn.active');
    const indicator = document.querySelector('.indicator');
    if(activeTab && indicator) {
        indicator.style.width = `${activeTab.offsetWidth}px`;
        indicator.style.left = `${activeTab.offsetLeft}px`;
    }
};

window.addEventListener('load', updateIndicator);
window.addEventListener('resize', updateIndicator);

window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('signup-form').addEventListener('input', () => {
        document.getElementById('signup-error-message').textContent = '';
    });
    document.getElementById('login-form').addEventListener('input', () => {
        document.getElementById('login-error-message').textContent = '';
    });
});

function showError(elementId, message) {
    document.getElementById(elementId).textContent = message;
}

/* ---------------------------------------------------------
    BACKEND LOGIC  
--------------------------------------------------------- */

async function login() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    
    if (!email || !password) return showError('login-error-message', 'Please enter your email and password.');

    try {
        const res = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();
        if (res.ok) {
            localStorage.setItem('token', data.access_token);
            window.location.href = 'dashboard.html';
        } else {
            showError('login-error-message', data.detail || "Incorrect email or password.");
        }
    } catch (error) {
        showError('login-error-message', 'Unable to connect to the backend server.');
    }
}

let pendingEmail = ""; // Store email temporarily for OTP verification

async function signup() {
    const name = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value.trim();
    const role = document.getElementById('signup-role').value.trim();
    
    if (!name || !email || !password || !role) return showError('signup-error-message', 'Please enter all the details.');
    if (password.length < 6) return showError('signup-error-message', 'Password must be at least 6 characters.');

    try {
        document.body.style.filter = "blur(5px)"; 

        const res = await fetch(`${API_URL}/api/auth/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, email, password, role })
        });

        const data = await res.json();
        if (res.ok) {
            // Registration successful, show OTP overlay instead of redirecting
            pendingEmail = email;
            showOtpOverlay();
        } else {
            // Displays exact backend error (e.g., "Email already registered")
            showError('signup-error-message', data.detail || "Signup failed.");
        }
    } catch (error) {
        showError('signup-error-message', 'Unable to connect to the backend server.');
    }
    finally{
        document.body.style.filter = "none";

    }
}

function showOtpOverlay() {
    document.getElementById('otp-overlay').classList.remove('hidden');
    document.getElementById('otp-input').value = ''; // Clear previous attempts
    document.getElementById('otp-input').focus();
}

function closeOtpOverlay() {
    document.getElementById('otp-overlay').classList.add('hidden');
    document.getElementById('otp-error-message').textContent = '';
}

async function verifyOtp() {
    const otp = document.getElementById('otp-input').value.trim();
    if (!otp || otp.length !== 6) {
        showError('otp-error-message', 'Please enter the 6-digit OTP.');
        return;
    }

    try {
        const res = await fetch(`${API_URL}/api/auth/verify-otp`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email: pendingEmail, otp: otp })
        });

        const data = await res.json();
        if (res.ok) {
            // OTP verified, account activated, save token and redirect
            localStorage.setItem('token', data.access_token);
            window.location.href = 'dashboard.html';
        } else {
            // Displays exact backend error (e.g., "Invalid OTP", "OTP expired")
            showError('otp-error-message', data.detail || "OTP verification failed.");
        }
    } catch (error) {
        showError('otp-error-message', 'Unable to connect to the backend server.');
    }
}


//    ----------------FORGOT PASSWORD LOGIC--------------------

document.querySelector('.forgot-pass').addEventListener('click', (e) => {
    e.preventDefault();
    showForgotOverlay();
});

function showForgotOverlay() {
    document.getElementById('forgot-overlay').classList.remove('hidden');
    document.getElementById('forgot-step1').style.display = 'block';
    document.getElementById('forgot-step2').style.display = 'none';
    document.getElementById('forgot-email').value = '';
    document.getElementById('forgot-otp').value = '';
    document.getElementById('forgot-new-password').value = '';
    document.getElementById('forgot-error-message').textContent = '';
    document.getElementById('forgot-title').innerText = 'Reset Password';
    document.getElementById('forgot-subtitle').innerText = "Enter your email to receive a reset code.";
}

function closeForgotOverlay() {
    document.getElementById('forgot-overlay').classList.add('hidden');
    document.getElementById('forgot-error-message').textContent = '';
}

async function sendForgotOtp() {
    const email = document.getElementById('forgot-email').value.trim();
    if (!email) return showError('forgot-error-message', 'Please enter your email.');

    try {
        const res = await fetch(`${API_URL}/api/auth/forgot-password?email=${encodeURIComponent(email)}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            document.getElementById('forgot-step1').style.display = 'none';
            document.getElementById('forgot-step2').style.display = 'block';
            document.getElementById('forgot-title').innerText = 'Verify & Reset';
            document.getElementById('forgot-subtitle').innerText = "Enter the OTP sent to your email and your new password.";
        } else {
            showError('forgot-error-message', data.detail || "Failed to send OTP.");
        }
    } catch (error) {
        showError('forgot-error-message', 'Unable to connect to the backend server.');
    }
}

async function resetPassword() {
    const email = document.getElementById('forgot-email').value.trim();
    const otp = document.getElementById('forgot-otp').value.trim();
    const new_password = document.getElementById('forgot-new-password').value.trim();

    if (!otp || otp.length !== 6) return showError('forgot-error-message', 'Please enter the 6-digit OTP.');
    if (!new_password || new_password.length < 6) return showError('forgot-error-message', 'Password must be at least 6 characters.');

    try {
        const res = await fetch(`${API_URL}/api/auth/reset-password`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email, otp, new_password })
        });
        const data = await res.json();
        if (res.ok) {
            const el = document.getElementById('forgot-error-message');
            showError('forgot-error-message', 'Password reset successful! Please login.');
            
            // Apply Green Success Styling
            el.style.color = '#10b981'; 
            el.style.background = 'rgba(16, 185, 129, 0.08)';
            el.style.borderColor = 'rgba(16, 185, 129, 0.2)';
            
            setTimeout(() => {
                closeForgotOverlay();
                switchTab('login'); // Automatically switch back to login tab
            }, 2000);
        } else {
            showError('forgot-error-message', data.detail || "Reset failed.");
        }
    } catch (error) {
        showError('forgot-error-message', 'Unable to connect to the backend server.');
    }
}






//   ------------ EMAIL TOGGLE LOGIC (Responsive & Green Success Text)--------------

document.addEventListener('DOMContentLoaded', async () => {
    const toggleBtn = document.getElementById('emailToggleBtn');
    if (!toggleBtn) return;

    const getActiveErrorId = () => {
        if (!document.getElementById('otp-overlay').classList.contains('hidden')) return 'otp-error-message';
        const activeForm = document.querySelector('.form-view.active');
        return activeForm ? activeForm.querySelector('.error-msg').id : 'login-error-message';
    };

    const notify = (msg, isSuccess = true) => {
        const id = getActiveErrorId();
        const el = document.getElementById(id);
        if (!el) return;

        showError(id, msg);
        
        // Apply Green styling for success, leave default (red) for errors
        if (isSuccess) {
            el.style.color = '#10b981'; 
            el.style.background = 'rgba(16, 185, 129, 0.08)';
            el.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        }
        else{
            el.style.color = ''; 
            el.style.background = '';
            el.style.borderColor = '';
        }
        
        setTimeout(() => {
            showError(id, '');
            el.style.color = '';
            el.style.background = '';
            el.style.borderColor = '';
        }, 6000);
    };

    const updateSetting = async (val) => {
        try {
            const res = await fetch(`${API_URL}/api/system/toggle-email?toggle=${val}`, { method: 'PUT' });
            if (!res.ok) throw new Error((await res.json()).detail || 'Server error');
            notify(`${(val == true)?"You will now recieve emails":"You will not recieve emails"}`, val);
        } catch (e) {
            notify(`Unable to connect to the backend server. Must be cold booting , Please try after few minutes`, false);
            toggleBtn.checked = !val; 
        }
    };

    toggleBtn.checked = false;
    await updateSetting(false);
    toggleBtn.addEventListener('change', function() { updateSetting(this.checked); });
});