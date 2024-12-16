// app.js
let SUPABASE_URL, SUPABASE_KEY;
let supabase;
let socket;
let typingTimeout;
let username = null; // Store the logged-in username
const activeChats = {}; // Track active chat boxes and their messages
let myContacts = []; // store users' contacts after fetching them
let userStatuses = {}; // store {username: status} from user_list event

// Fetch environment variables from the server
async function fetchEnvVariables() {
  try {
    const response = await fetch('/get_env');
    if (!response.ok) throw new Error('Failed to fetch environment variables');

    const env = await response.json();
    SUPABASE_URL = env.SUPABASE_URL;
    SUPABASE_KEY = env.SUPABASE_KEY;

    // Initialize Supabase after fetching environment variables
    initializeSupabase();
  } catch (error) {
    console.error('Error fetching environment variables:', error);
  }
}

// Initialize Supabase client
function initializeSupabase() {
  const { createClient } = window.supabase;
  supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
  console.log('Supabase initialized:', supabase);
}

// Account creation
function createAccount() {
  const email = document.getElementById('email').value.trim();
  const usernameInput = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();

  if (!email || !usernameInput || !password) {
    alert('All fields are required.');
    return;
  }

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(email)) {
    alert('Please enter a valid email address.');
    return;
  }

  fetch('/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username: usernameInput, password })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('Account created successfully.');
        window.location.href = '/login';
      } else {
        alert('Failed to create account: ' + data.message);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Error occurred while creating account.');
    });
}

// Handle login process
function login() {
  const email = document.getElementById('email').value.trim(); // Get email input
  const password = document.getElementById('password').value.trim(); // Get password input

  if (!email || !password) {
    alert('Please enter both your email and password.');
    return;
  }

  fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }) // Send email and password
  })
    .then(response => (response.ok ? response.json() : response.json().then(data => Promise.reject(data))))
    .then(() => {
      alert('Login successful.');
      window.location.href = '/dashboard';
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Login failed: ' + error.message);
    });
}


// Event listener for login button
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname === '/login') {
    const loginBtn = document.getElementById('login-button');
    if (loginBtn) loginBtn.addEventListener('click', login);

    // Fetch environment variables on login page load
    fetchEnvVariables();
  }
});

// Fetch user's contacts
function fetchMyContacts() {
  return fetch('/get_my_contacts', { credentials: 'include' })
    .then(res => res.json())
    .then(contactData => {
      myContacts = contactData; // Store in global variable
    })
    .catch(err => {
      console.error('Error fetching contacts:', err);
    });
}

// Init dashboard
function initializeDashboard() {
  fetch('/get_username', { credentials: 'include' })
    .then(response => (response.ok ? response.json() : window.location.href = '/login'))
    .then(data => {
      username = data.username;
      document.getElementById('username-display').textContent = username;
      //setupSocketIO();
      //document.getElementById('start-chat-button').addEventListener('click', startChat);

      // After we get the username, fetch the user's contacts
      fetchMyContacts().then(() => {
        setupSocketIO();
        document.getElementById('start-chat-button').addEventListener('click', startChat);
      // Logout button
      const logoutButton = document.getElementById('logout-button');
      if (logoutButton) {
        logoutButton.addEventListener('click', logout);
      }
      // set up search input listener
      const searchInput = document.getElementById('search-input');
      if (searchInput) {
        searchInput.addEventListener('input', () => {
          const query = searchInput.value.trim();
          if (!query) {
            document.getElementById('search-results').innerHTML = '';
          } else {
            searchContacts(query);
          }
        });
      }
      // Now that I have contacts and search set up, I can handle updates
    });
  });
}

// Setup Socket.IO
// CHANGED socket.on('message') to auto-create chat if closed
function setupSocketIO() {
  socket = io();

  socket.on('connect', () => {
    console.log('Connected to Socket.IO server.');
    socket.emit('login', { username });
    playLoginSound();
  });

  socket.on('message', data => {
    // Auto-create chat if it doesn't exist
    if (!activeChats[data.room]) {
      createChatBox(data.room, [data.username]);
    }
    appendMessageToChat(data.room, data.username, data.msg);

    if (data.username !== username) {
      const receiveSound = document.getElementById('message_receive_sound');
      if (receiveSound) {
        receiveSound.play().catch(error => console.log('Autoplay prevented:', error));
      }
    }
  });

  socket.on('user_list', data => {
    // CHANGED: Store statuses in userStatuses
    userStatuses = {};
    data.users.forEach(u => {
      userStatuses[u.username] = u.status;
    });
    updateContactsList([]);
  });

  socket.on('chat_started', data => {
    const roomName = data.room;
    if (!activeChats[roomName]) createChatBox(roomName, data.users);
  });

  socket.on('typing', data => {
    const typingIndicator = document.getElementById(`typing-${data.room}`);
    if (typingIndicator) typingIndicator.textContent = `${data.username} is typing...`;
  });

  socket.on('stop_typing', data => {
    const typingIndicator = document.getElementById(`typing-${data.room}`);
    if (typingIndicator) typingIndicator.textContent = '';
  });
}

// Create a chat box
function createChatBox(roomName, users) {
  const chatsContainer = document.getElementById('chats-container');
  const chatBox = document.createElement('div');
  chatBox.className = 'chat-box';
  chatBox.id = `chat-box-${roomName}`;

  chatBox.innerHTML = `
    <div class="chat-header">
      <h3>${users.join(', ')}</h3>
      <button class="close-chat" data-room="${roomName}">X</button>
    </div>
    <div class="messages" id="messages-${roomName}"></div>
    <input type="text" id="message-${roomName}" placeholder="Type a message..." oninput="sendTypingNotification('${roomName}')">
    <button onclick="sendMessage('${roomName}')">Send</button>
    <div id="typing-${roomName}" class="typing-indicator"></div>
  `;

  chatsContainer.appendChild(chatBox);
  activeChats[roomName] = chatBox;

  // Add Enter key listener to the input field
  const messageInput = document.getElementById(`message-${roomName}`);
  messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendMessage(roomName);
    }
  });

  // Close button logic
  const closeBtn = chatBox.querySelector('.close-chat');
  closeBtn.addEventListener('click', () => {
    // Remove from DOM
    chatsContainer.removeChild(chatBox);

    // Remove from activeChats
    delete activeChats[roomName];
  });
}

// ADDED: Search contacts function
function searchContacts(query) {
  fetch(`/search_contacts?query=${encodeURIComponent(query)}`, { credentials: 'include' })
    .then(response => response.json())
    .then(data => {
      const resultsUl = document.getElementById('search-results');
      resultsUl.innerHTML = '';
      data.forEach(contact => {
        const li = document.createElement('li');
        li.textContent = `${contact.username} `;

        // Add "Add Contact" button
        const addButton = document.createElement('button');
        addButton.textContent = '+';
        addButton.addEventListener('click', () => addContact(contact.id));
        li.appendChild(addButton);

        resultsUl.appendChild(li);
      });
    })
    .catch(error => console.error('Error fetching contacts:', error));
}

// ADDED: addContact function
function addContact(contactId) {
  fetch('/add_contact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ contact_id: contactId })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Contact added successfully!');
      // After adding a contact, re-fetch user contacts and update the list
      fetchMyContacts().then(() => {
        updateContactsList([]); // Pass empty array here, since updateContactsList now only uses myContacts
      });
    } else {
      alert('Failed to add contact: ' + data.message);
    }
  })
  .catch(error => {
    console.error('Error adding contact:', error);
    alert('An error occurred while adding the contact.');
  });
}

function updateContactsList(users) {
  const contactsList = document.getElementById('contacts-list');
  contactsList.innerHTML = '';

  // Sort contacts alphabetically by username
  myContacts.sort((a, b) => a.username.localeCompare(b.username));

  // Display contacts
  myContacts.forEach(contact => {
    const listItem = document.createElement('li');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = contact.username;
    checkbox.className = 'contact-checkbox';

    const label = document.createElement('label');
    // Show username and status
    let status = userStatuses[contact.username] || 'Offline'; // If not in userStatuses, user is offline
    label.textContent = `${contact.username} (${status})`;

    listItem.appendChild(checkbox);
    listItem.appendChild(label);
    contactsList.appendChild(listItem);
  });
}

// Start a group chat
function startChat() {
  const selectedUsers = Array.from(document.querySelectorAll('.contact-checkbox:checked')).map(cb => cb.value);
  
  if (selectedUsers.length === 0) {
    alert('Select at least one contact to start a chat...obviously.');
    return;
  }
  
  socket.emit('start_chat', { users: [...selectedUsers, username] });
}


// Send a message
function sendMessage(roomName) {
  const input = document.getElementById(`message-${roomName}`);
  const message = input.value.trim();
  if (!message) return;

  socket.emit('send_message', { username, message, room: roomName });
  // appendMessageToChat(roomName, username, message);
  input.value = '';
}

// Append a message to the chat
function appendMessageToChat(roomName, sender, message) {
  const messagesDiv = document.getElementById(`messages-${roomName}`);
  const messageElement = document.createElement('div');
  messageElement.textContent = `${sender}: ${message}`;
  messagesDiv.appendChild(messageElement);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Send typing notification
function sendTypingNotification(roomName) {
  socket.emit('typing', { username, room: roomName });
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => socket.emit('stop_typing', { username, room: roomName }), 3000);
}

// Play login sound
function playLoginSound() {
  const loginSound = document.getElementById('login_sound');
  if (loginSound) loginSound.play();
}

// Logout function
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

// Initialize the app on page load
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname === '/login') {
    const loginBtn = document.getElementById('login-button');
    if (loginBtn) loginBtn.addEventListener('click', login);
  } else if (window.location.pathname === '/dashboard') {
    initializeDashboard();
  }
});

