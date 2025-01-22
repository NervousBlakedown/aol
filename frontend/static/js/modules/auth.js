// frontend/static/js/modules/auth.js
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
import { isTokenExpired } from './utils.js';


// Initialize Supabase client
if (!window.SUPABASE_URL || !window.SUPABASE_KEY) {
    console.error("❌ Supabase configuration missing from global window object.");
    throw new Error("Supabase configuration is missing.");
}
const SUPABASE_URL = window.SUPABASE_URL;
const SUPABASE_KEY = window.SUPABASE_KEY;
export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
console.log('✅ Supabase Client Initialized:', supabase);


// Login
async function login() {
    console.log('Login button clicked');
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!email || !password) {
        alert('Please fill out all fields.');
        return;
    }
    console.log('Attempting to login with:', { email, password });


    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        console.log('Fetch response received:', response);

        if (!response.ok) {
            const errorData = await response.json();
            alert(`Authentication failed: ${errorData.message}`);
            return;
        }

        const data = await response.json();
        console.log('Login response data:', data);

        if (data.success && data.jwt_token) {
            // Store tokens
            localStorage.setItem('jwt_token', data.jwt_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            console.log('✅ Tokens stored successfully.');
            console.log("Stored JWT Token:", localStorage.getItem('jwt_token')); // Debugging
            console.log('Login successful. Redirecting to profile...');
            // Redirect to /user/profile
            window.location.href = data.redirect || '/user/dashboard';
        } else {
            alert(data.message || 'Login failed. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error.message);
        alert('An error occurred during login. Please try again.');
    }
}

// Initialize Auth State
export function initializeAuthState() {
    const loginButton = document.getElementById('login-button');
    if (loginButton) {
        loginButton.addEventListener('click', login);
        console.log('✅ Login button event listener attached.');
    }

    const currentPath = window.location.pathname;
    const token = localStorage.getItem('jwt_token');

    if (!token || isTokenExpired(token)) {
        if (currentPath !== '/auth/login') {
            console.warn("⚠️ Token missing or expired, redirecting to login.");
            window.location.href = '/auth/login';
        }
    } else {
        console.log("✅ Token exists and is valid.");
    }
}

// Signup
function signup() {
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value.trim();
    const username = document.getElementById('signup-username').value.trim();

    fetch('/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                localStorage.removeItem('token'); // Clear any leftover tokens
                console.log('✅ Signup successful. Redirecting to login...');
                window.location.href = '/auth/login';
            } else {
                alert(data.message);
            }
        });
}


// Initialize Signup Page
export function initializeSignupPage() {
    console.log('🔄 Clearing authentication state on signup page...');
    localStorage.removeItem('token'); // Clear JWT
}