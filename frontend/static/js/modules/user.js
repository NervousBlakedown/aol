// frontend/static/js/modules/user.js
import { authenticatedFetch } from './utils.js';
export { fetchPalsList };
let palsList = [];


// Fetch and display user profile data
export async function fetchUserProfile() {
    try {
        const data = await authenticatedFetch('/user/profile_data', { method: 'GET' });
        console.log("User profile fetched:", data);
        return data;

        // update DOM
        const userNameEl = document.getElementById('profile-username');
        const bioEl = document.getElementById('profile-bio');
        if (userNameEl) userNameEl.textContent = data.username;
        if (bioEl) bioEl.textContent = data.bio;
        return data;
    } catch (error) {
        console.error("Error fetching user profile:", error);
        window.location.href = '/auth/login';
    }
}


// Initialize user-specific events
export function initializeUser() {
    // Attach event for the "Edit Bio" button
    const editBioBtn = document.getElementById('edit-bio-button');
    if (editBioBtn) {
        editBioBtn.addEventListener('click', editBio);
    }

    // Attach event for the "Change Pic" button
    const changeAvatarBtn = document.getElementById('change-avatar-button');
    if (changeAvatarBtn) {
        changeAvatarBtn.addEventListener('click', () => {
            // Trigger the hidden file input
            const fileInput = document.getElementById('avatar-upload');
            if (fileInput) fileInput.click();
        });
    }

    // When file is selected, upload
    const avatarUploadInput = document.getElementById('avatar-upload');
    if (avatarUploadInput) {
        avatarUploadInput.addEventListener('change', uploadAvatar);
    }
}


// Upload Avatar Logic
async function uploadAvatar(event) {
    // The 'change' event from <input type="file">
    const file = event.target.files[0];
    if (!file) {
        console.warn('No file selected for avatar upload.');
        return;
    }

    const formData = new FormData();
    formData.append('avatar', file);

    try {
        const response = await fetch('/user/upload_avatar', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
            },
            body: formData
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.message || 'Failed to upload avatar');
        }

        console.log('✅ Avatar uploaded successfully:', result.avatar_url);
        // Update the DOM to show the new avatar
        const avatarImg = document.getElementById('profile-avatar');
        avatarImg.src = `${result.avatar_url}?t=${new Date().getTime()}`;

        if (avatarImg) {
            avatarImg.src = result.avatar_url;
        }

    } catch (error) {
        console.error('❌ Error uploading avatar:', error);
        alert(error.message || 'Error uploading avatar.');
    }
}


// Edit bio 
function editBio() {
    const bioEl = document.getElementById('profile-bio');
    if (!bioEl) return;

    const oldBio = bioEl.textContent || '';
    const newBio = prompt('Edit your bio:', oldBio);
    if (!newBio || newBio.trim() === oldBio) {
        return; // no changes
    }

    authenticatedFetch('/user/update_bio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bio: newBio })
    })
    .then(data => {
        if (data.success) {
            bioEl.textContent = newBio;
            console.log('✅ Bio updated successfully!');
            // Or alert('Bio updated successfully!');
        } else {
            console.error('❌ Failed to update bio:', data.message);
        }
    })
    .catch(err => console.error('❌ Error updating bio:', err));
}


// fetch Pals List
async function fetchPalsList() {
    try {
        const response = await fetch('/user/get_pals', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        if (data.success) {
            palsList = data.pals.map(pal => pal.username);  // Store pals for filtering
            console.log('✅ Pals loaded:', data.pals);
            displayPalsList(data.pals);
        } else {
            console.error('❌ Failed to load pals:', data.message);
        }
    } catch (error) {
        console.error('❌ Error fetching pals:', error);
    }
}


// handle user searching from chat_routes.py endpoint and chat_service.py
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', async () => {
        const query = searchInput.value.trim();
        if (query.length === 0) {
            searchResults.innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/chat/search_users?query=${encodeURIComponent(query)}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                }
            });
            const data = await response.json();
            console.log("Search response:", data);
            
            if (data.success && data.users.length > 0) {
                searchResults.innerHTML = '';
                data.users
                    .filter(u => !palsList.includes(u.username)) // Correct scoping
                    .forEach(user => {
                        const li = document.createElement('li');
                        
                        // Create a container for username and button
                        li.classList.add('search-result-item');

                        // Add username text
                        const usernameSpan = document.createElement('span');
                        usernameSpan.textContent = user.username;
                        usernameSpan.classList.add('username-text');

                        // Add Font Awesome '+' button
                        const addButton = document.createElement('button');
                        addButton.innerHTML = '<i class="fas fa-plus"></i>'; // Add Font Awesome icon
                        addButton.classList.add('add-pal-btn');
                        addButton.addEventListener('click', (event) => {
                            event.stopPropagation();  // Prevent li click event
                            addPal(user.username);
                        });

                        li.appendChild(usernameSpan);
                        li.appendChild(addButton);
                        searchResults.appendChild(li);
                    });


                    // Add username text
                    const usernameSpan = document.createElement('span');
                    usernameSpan.textContent = user.username;
                    usernameSpan.classList.add('username-text');

                    // Add 'Add Pal' button
                    const addButton = document.createElement('button');
                    addButton.innerHTML = '<i class="fas fa-plus"></i>'; // Font Awesome icon
                    // addButton.textContent = 'Add Pal';
                    addButton.classList.add('add-pal-btn');
                    addButton.addEventListener('click', (event) => {
                        event.stopPropagation();  // Prevent li click event
                        addPal(user.username);
                    });

                    li.appendChild(usernameSpan);
                    li.appendChild(addButton);
                    searchResults.appendChild(li);
            } else {
                searchResults.innerHTML = '<li>No users found.</li>';
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    });

    async function addPal(username) {
        console.log(`Attempting to add pal: ${username}`);

        try {
            const token = localStorage.getItem('jwt_token');
        if (!token) {
            alert('Authentication token is missing. Please log in again.');
            return;
        }

            const response = await fetch('/user/add_pal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
                },
                body: JSON.stringify({ username })
            });
            console.log('Server response:', response);          
    
            const result = await response.json();
            if (response.ok && result.success) {
                alert(`Successfully added ${username} as a pal!`);
                fetchPalsList();  // Refresh the pals list
            } else {
                console.error('Error:', result.message);
                alert(`Failed to add ${username}: ${result.message}`);
            }
        } catch (error) {
            console.error('Error adding pal:', error);
            alert('Error adding pal. Please try again.');
        }
    }    
});


// display pals list in DOM/sidebar chat area
function displayPalsList(pals) {
    const palsContainer = document.getElementById('contacts-list');
    palsContainer.innerHTML = ''; 

    // Sort pals alphabetically by username
    pals.sort((a, b) => a.username.localeCompare(b.username));

    pals.forEach(pal => {
        const palElement = document.createElement('li');
        palElement.innerHTML = `
            <input type="checkbox" class="contact-checkbox" value="${pal.username}">
            <img src="${pal.avatar_url || '/static/assets/avatars/default_avatar.png'}" alt="${pal.username}" class="pal-avatar">
            <span class="pal-username">${pal.username}</span>
        `;
        palsContainer.appendChild(palElement);
    });
}

// settings button popup
document.addEventListener('DOMContentLoaded', () => {
    const settingsButton = document.getElementById('settings-button');
    const closeSettings = document.getElementById('close-settings');
    const settingsModal = document.getElementById('settings-modal');
    const saveSettingsBtn = document.getElementById('save-settings');

    // Open settings modal
    settingsButton.addEventListener('click', () => {
        settingsModal.style.display = 'block';

        // Load existing settings from sessionStorage (as example)
        document.getElementById('settings-username').value = sessionStorage.getItem('username') || '';
        document.getElementById('settings-email').value = 'user@example.com';  // Placeholder for actual data
    });

    // Close settings modal
    closeSettings.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    window.onclick = function(event) {
        if (event.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    };

    // Save settings functionality
    saveSettingsBtn.addEventListener('click', async () => {
        const updatedUsername = document.getElementById('settings-username').value;
        const updatedEmail = document.getElementById('settings-email').value;
        const updatedPassword = document.getElementById('settings-password').value;
        const notifications = document.getElementById('settings-notifications').checked;
        const privacy = document.getElementById('settings-privacy').value;

        const response = await fetch('/user/update_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: updatedUsername,
                email: updatedEmail,
                password: updatedPassword,
                notifications: notifications,
                privacy: privacy
            }),
        });

        const result = await response.json();
        if (result.success) {
            alert('✅ Settings updated successfully!');
            settingsModal.style.display = 'none';
            sessionStorage.setItem('username', updatedUsername);
            document.getElementById('username-display').textContent = updatedUsername;
        } else {
            alert('❌ Failed to update settings.');
        }
    });
});


// Logout
document.addEventListener('DOMContentLoaded', () => {
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            logoutUser();
        });
    }
});

// logout user
async function logoutUser() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
            }
        });

        if (response.ok) {
            localStorage.removeItem('jwt_token');
            sessionStorage.clear();
            window.location.href = '/auth/login';
        } else {
            console.error('❌ Logout failed');
            alert('Logout failed. Please try again.');
        }
    } catch (error) {
        console.error('❌ Error during logout:', error);
        alert('Error during logout. Please try again.');
    }
}
