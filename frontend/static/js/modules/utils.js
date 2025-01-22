// frontend/static/js/modules/utils.js
// JWT token in every API call, not Flask Sessions
export async function authenticatedFetch(url, options = {}) {
    let token = localStorage.getItem('jwt_token');

    // Refresh token if expired or missing
    if (!token || isTokenExpired(token)) {
        console.warn("⚠️ JWT token expired or missing. Attempting refresh...");
        token = await refreshToken();
        
        if (!token) {
            console.error("❌ No new token obtained after refresh. Redirecting to login.");
            window.location.href = '/auth/login';
            return;
        }
    }

    console.log("📤 Sending Authorization Header:", `Bearer ${token}`);

    // Ensure headers are set correctly
    options.headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
    };

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error("❌ Error making request:", error);
        throw error;
    }
}


// check if JWT token is expired
export function isTokenExpired(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1])); // Decode JWT payload
        const now = Math.floor(Date.now() / 1000); // Current time in seconds
        return payload.exp < now; // Check if token is expired
    } catch (error) {
        console.error("Failed to decode token:", error);
        return true; // Treat as expired if decoding fails
    }
}


export async function refreshToken() {
    const refresh_token = localStorage.getItem('refresh_token');
    if (!refresh_token) {
        console.error("No refresh token found. Redirecting to login.");
        window.location.href = '/auth/login';
        return null;
    }

    try {
        const response = await fetch('/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token })
        });

        const result = await response.json();
        if (result.jwt_token) {
            localStorage.setItem('jwt_token', result.jwt_token);
            localStorage.setItem('refresh_token', result.refresh_token);
            console.log("Access token refreshed and stored in localStorage.");
            return result.jwt_token;
        } else {
            console.error("Failed to refresh token:", result);
            window.location.href = '/auth/login';
            return null;
        }
    } catch (error) {
        console.error("Error refreshing token:", error);
        window.location.href = '/auth/login';
        return null;
    }
}


// Base64 Encoding and Decoding
export function encodeRoomName(roomName) {
    if (!roomName || typeof roomName !== 'string') {
        console.error('❌ Invalid room name provided for encoding:', roomName);
        return '';
    }
    return btoa(roomName);
}

export function decodeRoomName(encodedName) {
    try {
        return atob(encodedName);
    } catch (error) {
        console.error('❌ Error decoding room name:', error);
        return '';
    }
}

// Timestamp Formatter
export function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
        console.warn('❌ Invalid timestamp:', timestamp);
        return timestamp; // Fallback to raw timestamp if invalid
    }
    return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
}

// Sanitize Input
export function sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    return input.replace(/</g, '&lt;').replace(/>/g, '&gt;').trim();
}

// Validate Email
export function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Clear Input Field
export function clearInputField(inputId) {
    const input = document.getElementById(inputId);
    if (input) input.value = '';
}

// Display Alert Message
export function displayAlert(message, type = 'info') {
    const alertBox = document.getElementById('alert-box');
    if (alertBox) {
        alertBox.innerHTML = `<div class="alert alert-${type}">${sanitizeInput(message)}</div>`;
        setTimeout(() => (alertBox.innerHTML = ''), 3000);
    } else {
        console.warn('❌ Alert box not found in DOM.');
    }
}

// Handle API Errors
export function handleApiError(error) {
    console.error('❌ API Error:', error);
    displayAlert('An error occurred. Please try again later.', 'error');
}

// Scroll to Bottom of an Element
export function scrollToBottom(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollTop = element.scrollHeight;
    } else {
        console.warn(`❌ Element with ID '${elementId}' not found for scrolling.`);
    }
}
