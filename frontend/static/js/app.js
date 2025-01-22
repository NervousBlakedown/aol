// frontend/static/js/app.js
import { initializeAuthState } from './modules/auth.js';
import { authenticatedFetch, isTokenExpired } from './modules/utils.js';
import { fetchPalsList, fetchUserProfile, initializeUser } from './modules/user.js';
import { initializeChat } from './modules/chat.js'; // './modules
import { initializeSocket } from './modules/socket.js';
// import { initializeNotifications } from './modules/notifications.js';
import { initializeTopics } from './modules/topics.js';
import { initializeMusicPlayer } from './modules/music.js';
window.userIdToName = {};


// collapsibles logic
function initCollapsibles() {
    const collapsibles = document.querySelectorAll('.collapsible');
    collapsibles.forEach((section) => {
      section.addEventListener('click', (event) => {
        const isInputClicked = ['INPUT', 'SELECT', 'BUTTON'].includes(event.target.tagName);
        if (isInputClicked) return;
  
        const contentId = section.getAttribute('data-toggle');
        const content = document.getElementById(contentId);
        const icon = section.querySelector('.toggle-icon');
  
        if (content.style.display === 'none' || !content.style.display) {
          content.style.display = 'block';
          icon.textContent = '▼';
        } else {
          content.style.display = 'none';
          icon.textContent = '▶';
        }
      });
    });
  }


// status 
function initStatusOptions() {
    const statusOptions = document.querySelectorAll('.status-option');
    statusOptions.forEach(option => {
        option.addEventListener('click', () => {
            statusOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');

            const selectedStatus = option.textContent.trim().toLowerCase();
            console.log(`User status changed to: ${selectedStatus}`);

            fetch('/user/update_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: selectedStatus })
            })
            .then(response => {
                if (response.ok) {
                    console.log('Status updated successfully');
                } else {
                    console.error('Failed to update status');
                }
            });

            localStorage.setItem('userStatus', selectedStatus);
        });
    });

    // Restore from localStorage
    const savedStatus = localStorage.getItem('userStatus');
    if (savedStatus) {
        const activeOption = document.getElementById(`status-${savedStatus}`);
        if (activeOption) {
            statusOptions.forEach(opt => opt.classList.remove('active'));
            activeOption.classList.add('active');
        }
    }
}


// 3) Load user profile, set username in sessionStorage
async function loadUserProfileAndStoreUsername() {
    try {
        console.log('Loading profile_data via authenticatedFetch...');
        const response = await authenticatedFetch('/user/profile_data');
        console.log('Profile data fetched:', response);

        // Put it in sessionStorage so socket.js sees it
        if (response.username) {
            sessionStorage.setItem('username', response.username);
            console.log('✅ Username set in sessionStorage:', response.username);
        }
        // If your server returns user_id, do sessionStorage.setItem('user_id', response.user_id);

        // Update the DOM
        document.getElementById('profile-username').textContent = response.username;
        document.getElementById('profile-bio').textContent = response.bio;

    } catch (err) {
        console.error('Error fetching profile:', err);
        window.location.href = '/auth/login';
    }
}


// other logic  
async function loadNewsTicker() {
try {
    const response = await fetch('/api/news');
    const data = await response.json();

    const tickerContent = document.getElementById('news-ticker');
    if (response.ok && data.success) {
    tickerContent.innerHTML = data.headlines.map(article =>
        `<span><a href="${article.url}" target="_blank">${article.title}</a></span>`
    ).join('');
    } else {
    console.error('Failed to load news:', data.message);
    tickerContent.innerHTML = '<span>⚠️ Failed to load news headlines.</span>';
    }
} catch (error) {
    console.error('Error fetching news:', error);
    document.getElementById('news-ticker').innerHTML = '<span>⚠️ Error fetching news.</span>';
}
}
  
  // This function will fetch the user's profile from /user/profile
  async function loadUserProfile() {
    try {
      console.log('Attempting to load profile via authenticatedFetch...');
      const responseData = await authenticatedFetch('/user/profile_data', { method: 'GET' });
      console.log('Profile data:', responseData);
  
      // Update the DOM
      document.getElementById('profile-username').textContent = responseData.username;
      document.getElementById('profile-bio').textContent = responseData.bio;
  
    } catch (err) {
      console.error('Error fetching profile:', err);
      window.location.href = '/auth/login';
    }
  }


// DOM Vito Corleone
document.addEventListener('DOMContentLoaded', async () => {
    console.log('✅ DOMContentLoaded event triggered.');
    const currentPath = window.location.pathname;
    console.log('Current Path:', currentPath);

    // Login page
    if (currentPath === '/auth/login') {
        initializeAuthState();
        console.log('✅ Initialized login page for /login route.');
        return;
    }

    // If we are on the "dashboard" page:
    if (currentPath === '/user/dashboard') {
        // 1) Check if the token is missing or expired
        const token = localStorage.getItem('jwt_token');
        if (!token || isTokenExpired(token)) {
            console.warn("⚠️ Token missing or expired. Redirecting to login.");
            window.location.href = '/auth/login';
            return;
        }

        // 2) Load profile & store the username in session
        await loadUserProfileAndStoreUsername();

        // user logic (avatar, bio, etc.)
        initializeUser();

        

        // 3) setup other page features
        initCollapsibles();
        initStatusOptions();
        // initializeNotifications();
        initializeTopics();
        initializeChat();
        initializeSocket();
        initializeMusicPlayer();

        // 2) load user profile
        await loadUserProfile();
        fetchPalsList();

        // RSS logic
        await loadNewsTicker();
        setInterval(loadNewsTicker, 300000); // refresh every 5 minutes
        console.log('profile page setup complete');
    }
});