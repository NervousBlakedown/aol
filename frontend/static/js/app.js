// frontend/static/js/app.js
let SUPABASE_URL, SUPABASE_KEY;
let supabase;
let socket;
let typingTimeout;
let username = null; 
const activeChats = {}; 
let myContacts = []; 
let userStatuses = {}; 
const roomInputs = {};

// Base64 encoding to fix special character username chats
function encodeRoomName(roomName) {
  return btoa(roomName); 
}

function decodeRoomName(encodedName) {
  return atob(encodedName);
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  fetchEnvVariables();

  const currentPath = window.location.pathname;

  // login page
  if (currentPath === '/login') {
    const loginBtn = document.getElementById('login-button');
    if (loginBtn) {
      loginBtn.addEventListener('click', login);
    }
  }

  // dashboard page
  if (currentPath === '/dashboard') {
    setupSocketIO(); // Initialize Socket.IO first
    initializeDashboard();
    fetchMyContacts();

    const startChatButton = document.getElementById('start-chat-button');
    if (startChatButton) {
      startChatButton.addEventListener('click', startChat);
    }

    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
      logoutButton.addEventListener('click', logout);
    }

    // Add event listener for "Add Pals"
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            const resultsList = document.getElementById('search-results');
            resultsList.innerHTML = ''; // Clear previous results

            if (query) {
                fetch(`/search_contacts?query=${query}`)
                    .then(response => response.json())
                    .then(results => {
                        if (results.length === 0) {
                            resultsList.innerHTML = '<li>No users found.</li>';
                            return;
                        }
                        results.forEach(user => {
                            const listItem = document.createElement('li');
                            listItem.innerHTML = `
                                ${user.username} <button onclick="addPal('${user.username}')">Add</button>
                            `;
                            resultsList.appendChild(listItem);
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching contacts:', error);
                        resultsList.innerHTML = '<li>Error fetching users. Try again later.</li>';
                    });
            }
        });
    }
  }
});

// Add Pal to Pals list
function addPal(username) {
  fetch('/add_contact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username }),
    credentials: 'include'
  })
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        alert(`Successfully added ${username} as a Pal!`);
        fetchMyContacts(); // Refresh Pals list
      } else {
        alert(`Failed to add ${username}: ${result.message}`);
      }
    })
    .catch(error => {
      console.error('Error adding Pal:', error);
      alert('An error occurred while adding the Pal. Please try again.');
    });
}

// Remove Pal from Pals list
// Function to handle removing a pal
document.addEventListener('click', (event) => {
  if (event.target.classList.contains('remove-pal-btn')) {
    const username = event.target.getAttribute('data-username');
    if (confirm(`Are you sure you want to remove ${username} from your Pals list?`)) {
      removePal(username);
    }
  }
});

// Remove Pal API call
function removePal(username) {
  fetch(`/remove_contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username }),
    credentials: 'include'
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert(`${username} has been removed from your Pals list.`);
        fetchMyContacts(); // Refresh the Pals list
      } else {
        alert(data.message || 'Failed to remove Pal.');
      }
    })
    .catch(error => console.error('Error removing Pal:', error));
}

// Fetch .env
function fetchEnvVariables() {
  fetch('/get_env')
    .then(response => response.json())
    .then(env => {
      SUPABASE_URL = env.SUPABASE_URL;
      SUPABASE_KEY = env.SUPABASE_KEY;
      initializeSupabase();
    })
    .catch(error => console.error('Error fetching environment variables:', error));
}

// Init DB
function initializeSupabase() {
  const { createClient } = window.supabase;
  supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
  console.log('Supabase initialized.');
}

// login
function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value.trim();

  if (!email || !password) {
    alert('Please enter both email and password.');
    return;
  }

  supabase.auth.signInWithPassword({ email, password })
    .then(({ error }) => {
      if (error) throw new Error(error.message);

      return fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      });
    })
    .then(response => {
      if (!response.ok) throw new Error('Failed to establish session.');
      return response.json();
    })
    .then(result => {
      if (result.success) {
        window.location.href = '/dashboard';
      } else {
        throw new Error(result.message || 'Login failed.');
      }
    })
    .catch(error => {
      console.error('Login error:', error);
      alert(`Login failed: ${error.message}`);
    });
}

// Set up Socket.IO
function setupSocketIO() {
  socket = io();

  socket.on('connect', () => {
    console.log('Socket.IO connected.');
    if (username) socket.emit('login', { username });
  });

  socket.on('chat_started', data => {
    console.log('chat_started event received:', data); // Debugging
    const roomName = data.room;
    if (!activeChats[roomName]) createChatBox(roomName, data.users);
  });

  socket.on('message', data => {
    appendMessageToChat(data.room, data.username, data.msg, data.timestamp);
  });

  socket.on('user_list', data => {
    userStatuses = {};
    data.users.forEach(user => {
      userStatuses[user.username] = user.status;
    });
    updateContactsList();
  });
}

// Fetch username for dashboard
function initializeDashboard() {
  fetch('/get_username', { credentials: 'include' })
    .then(response => response.json())
    .then(data => {
      if (data.username) {
        username = data.username;
        document.getElementById('username-display').textContent = username; //`Welcome, ${username}!`;
        socket.emit('login', { username });
      } else {
        alert('Error fetching username.');
        window.location.href = '/login';
      }
    })
    .catch(err => console.error('Error fetching username:', err));
}

// Fetch contacts list
function fetchMyContacts() {
  fetch('/get_my_contacts', { credentials: 'include' })
    .then(response => response.json())
    .then(data => {
      myContacts = data;
      updateContactsList();
    })
    .catch(err => console.error('Error fetching contacts:', err));
}

// Update contacts list UI
function updateContactsList() {
  const contactsList = document.getElementById('contacts-list');
  contactsList.innerHTML = '';

  myContacts.sort((a, b) => a.username.localeCompare(b.username));
  myContacts.forEach(contact => {
    const listItem = document.createElement('li');
    listItem.innerHTML = `
      <input type="checkbox" class="contact-checkbox" value="${contact.username}">
      <label>${contact.username} (${userStatuses[contact.username] || 'Offline'})</label>
    `;
    contactsList.appendChild(listItem);
  });
}

// Start Chat
function startChat() {
  const selectedContacts = Array.from(
      document.querySelectorAll('.contact-checkbox:checked')
  ).map(cb => cb.value);

  if (selectedContacts.length === 0) {
      alert('Please select at least one Pal.');
      return;
  }

  let roomName;
  const receivers = selectedContacts;

  // Generate plain room name
  if (receivers.length === 1) {
      roomName = receivers[0]; // Single chat: Receiver's username
  } else {
      const roomParticipants = [username, ...receivers].sort();
      roomName = roomParticipants.join('_'); // Group chat: Sorted participants
  }

  console.log(`Starting chat with: ${receivers} (Room Name: ${roomName})`);

  if (!activeChats[roomName]) {
      createChatBox(roomName, receivers); // Pass receivers for chat title
      socket.emit('start_chat', { users: [username, ...receivers], room: roomName }); // Use plain room name for server
  }

  // Deselect all checkboxes
  document.querySelectorAll('.contact-checkbox').forEach(cb => (cb.checked = false));
}

// Create chat box
function createChatBox(roomName, participants) {
  const chatsContainer = document.getElementById('chats-container');
  if (!chatsContainer) {
      console.error('Chats container not found.');
      return;
  }

  if (activeChats[roomName]) return;

  const encodedRoomName = encodeRoomName(roomName); // Consistently encode for DOM use

  const chatBox = document.createElement('div');
  chatBox.className = 'chat-box';
  chatBox.id = `chat-box-${encodedRoomName}`; // Set id with encoded room name

  const chatTitle = participants.length > 1 ? participants.join(', ') : participants[0]; // Title logic

  chatBox.innerHTML = `
      <div class="chat-header">
          <h3>${chatTitle}</h3>
          <button class="close-chat" data-room="${encodedRoomName}">X</button>
      </div>
      <div class="messages" id="messages-${encodedRoomName}"></div>
      <input type="text" id="message-${encodedRoomName}" placeholder="Type a message..." />
      <button onclick="sendMessage('${roomName}')">Send</button>
  `;

  chatsContainer.appendChild(chatBox);

  // Corrected selector to match the assigned id
  const messageInput = document.getElementById(`message-${encodedRoomName}`);
  if (!messageInput) {
      console.error(`Message input not found for room: ${roomName}`);
      console.error(`Expected selector: #message-${encodedRoomName}`);
      return;
  }

  // Debugging log to confirm listener attachment
  console.log(`Attaching keydown listener to: #message-${encodedRoomName}`);

  // Attach "Return" key listener
  messageInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
          console.log(`Return key pressed in room: ${roomName}`);
          sendMessage(roomName); // Call sendMessage with plain room name
      }
  });

  const closeButton = chatBox.querySelector('.close-chat');
  if (closeButton) {
      closeButton.addEventListener('click', () => {
          chatsContainer.removeChild(chatBox);
          delete activeChats[roomName];
      });
  }

  activeChats[roomName] = chatBox;
}

// Append message
function appendMessageToChat(roomName, sender, message, timestamp) {
  const encodedRoomName = encodeRoomName(roomName); // Use encoded name
  const messagesDiv = document.getElementById(`messages-${encodedRoomName}`);
  if (!messagesDiv) return;

  const messageElement = document.createElement('div');
  messageElement.textContent = `[${timestamp}] ${sender}: ${message}`;
  messagesDiv.appendChild(messageElement);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Send message
function sendMessage(roomName) {
  const encodedRoomName = encodeRoomName(roomName); // Use encoded name for DOM queries
  const input = document.getElementById(`message-${encodedRoomName}`);
  if (!input) {
      console.error(`Input field not found for room: ${roomName}`);
      return;
  }

  const message = input.value.trim();
  if (!message) return;

  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  socket.emit('send_message', { username, message, room: roomName, timestamp }); // Use plain room name for server
  appendMessageToChat(roomName, 'You', message, timestamp);
  input.value = '';
}

// Logout
function logout() {
  fetch('/logout', { method: 'POST', credentials: 'include' })
    .then(response => {
      if (response.ok) {
        if (socket) socket.disconnect();
        window.location.href = '/login';
      } else {
        alert('Failed to logout.');
      }
    });
}
