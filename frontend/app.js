// app.js
let socket;
let typingTimeout;
let username = null; // Store the logged-in username
const activeChats = {}; // Track active chat boxes and their messages

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
  username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();

  if (!username || !password) {
    alert('Please enter both your screen name and password.');
    return;
  }

  fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
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

// Initialize dashboard
function initializeDashboard() {
  fetch('/get_username', { credentials: 'include' })
    .then(response => (response.ok ? response.json() : window.location.href = '/login'))
    .then(data => {
      username = data.username;
      document.getElementById('username-display').textContent = username;
      setupSocketIO();
      document.getElementById('start-chat-button').addEventListener('click', startChat);
    });
}

// Setup Socket.IO
function setupSocketIO() {
  socket = io();

  socket.on('connect', () => {
    console.log('Connected to Socket.IO server.');
    socket.emit('login', { username });
    playLoginSound();
  });

  socket.on('message', data => {
    if (activeChats[data.room]) appendMessageToChat(data.room, data.username, data.msg);
  
    // Play the receive sound only if the message is from someone else
    if (data.username !== username) {
      const receiveSound = document.getElementById('message_receive_sound');
      if (receiveSound) {
        receiveSound.play().catch(error => console.log('Autoplay prevented:', error));
      }
    }
  });
  

  socket.on('user_list', data => updateContactsList(data.users));

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

// Update contacts list
function updateContactsList(users) {
  const contactsList = document.getElementById('contacts-list');
  contactsList.innerHTML = '';
  users.forEach(user => {
    if (user.username === username) return;

    const listItem = document.createElement('li');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = user.username;
    checkbox.className = 'contact-checkbox';

    const label = document.createElement('label');
    label.textContent = `${user.username} (${user.status})`;

    listItem.appendChild(checkbox);
    listItem.appendChild(label);
    contactsList.appendChild(listItem);
  });
}

// Start a group chat
function startChat() {
  const selectedUsers = Array.from(document.querySelectorAll('.contact-checkbox:checked')).map(cb => cb.value);
  
  if (selectedUsers.length === 0) {
    alert('Please select at least one contact to start a chat...obviously.');
    return;
  }
  
  // If there's only one selected user, it's a one-on-one chat.
  // If more than one, it's a group chat.
  // The server treats them similarly: it just creates a room with the given participants.
  
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

