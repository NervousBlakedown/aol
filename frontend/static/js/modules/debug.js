// frontend/static/js/modules/debug.js

export function initializeDebug() {
    document.getElementById('debug-session-button')?.addEventListener('click', debugSession);
    document.getElementById('debug-config-button')?.addEventListener('click', debugConfig);
}

// Debug Session
function debugSession() {
    fetch('/debug_session', { credentials: 'include' })
        .then(response => response.json())
        .then(data => {
            console.log('Session Debug Data:', data);
            alert('Session debug data logged in the console.');
        })
        .catch(error => {
            console.error('❌ Error debugging session:', error);
            alert('Failed to fetch session debug data.');
        });
}

// Debug Config
function debugConfig() {
    fetch('/debug_config')
        .then(response => response.json())
        .then(data => {
            console.log('Config Debug Data:', data);
            alert('Config debug data logged in the console.');
        })
        .catch(error => {
            console.error('❌ Error debugging config:', error);
            alert('Failed to fetch config debug data.');
        });
}

// Display Session in UI
export function displaySessionDebug() {
    fetch('/debug_session', { credentials: 'include' })
        .then(response => response.json())
        .then(data => {
            const debugContainer = document.getElementById('session-debug');
            if (debugContainer) {
                debugContainer.innerText = JSON.stringify(data, null, 2);
            }
        })
        .catch(error => {
            console.error('❌ Error fetching session data:', error);
        });
}
