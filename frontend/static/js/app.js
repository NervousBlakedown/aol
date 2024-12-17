let SUPABASE_URL, SUPABASE_KEY;
let supabase;
let socket;
let typingTimeout;
let username = null; // Store the logged-in username
const activeChats = {}; // Track active chat boxes and their messages
let myContacts = []; // Store users' contacts
let userStatuses = {}; // Store {username: status} from user_list event

// Part I: Initialization
document.addEventListener('DOMContentLoaded', () => {
  fetchEnvVariables();

  const currentPath = window.location.pathname;

  if (currentPath === '/dashboard') {
    setupSocketIO(); // Initialize Socket.IO first
    initializeDashboard();
    fetchMyContacts();

    const startChatButton = document.getElementById('start-chat-button');
    if (startChatButton) {
      startChatButton.addEventListener('click', startChat);
    }
  }
});

// Fetch environment variables
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

// Initialize Supabase
function initializeSupabase() {
  const { createClient } = window.supabase;
  supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
  console.log('Supabase initialized.');
}

// Set up Socket.IO
function setupSocketIO() {
  socket = io();

  socket.on('connect', () => {
    console.log('Socket.IO connected.');
    if (username) socket.emit('login', { username });
  });

  socket.on('chat_started', data => {
    const roomName = data.room;
    if (!activeChats[roomName]) createChatBox(roomName, data.users);
  });

  socket.on('message', data => appendMessageToChat(data.room, data.username, data.msg));

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
        document.getElementById('username-display').textContent = `Welcome, ${username}!`;
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
    alert('Select at least one contact to start a chat.');
    return;
  }

  const roomName = selectedContacts.join('_');
  socket.emit('start_chat', { users: [...selectedContacts, username] });

  // Immediately open the chat box
  if (!activeChats[roomName]) createChatBox(roomName, selectedContacts);
}

// Create a chat box
function createChatBox(roomName, users) {
  const chatsContainer = document.getElementById('chats-container');
  if (!chatsContainer) {
    console.error('Chats container not found.');
    return;
  }

  if (activeChats[roomName]) return; // Prevent duplicate chat boxes

  const chatBox = document.createElement('div');
  chatBox.className = 'chat-box';
  chatBox.id = `chat-box-${roomName}`;

  chatBox.innerHTML = `
    <div class="chat-header">
      <h3>Chat with ${users.join(', ')}</h3>
      <button class="close-chat" data-room="${roomName}">X</button>
    </div>
    <div class="messages" id="messages-${roomName}"></div>
    <input type="text" id="message-${roomName}" placeholder="Type a message..." />
    <button onclick="sendMessage('${roomName}')">Send</button>
  `;

  // Close button functionality
  chatBox.querySelector('.close-chat').addEventListener('click', () => {
    chatsContainer.removeChild(chatBox);
    delete activeChats[roomName];
  });

  // Enter key functionality for sending messages
  const messageInput = chatBox.querySelector(`#message-${roomName}`);
  messageInput.addEventListener('keydown', event => {
    if (event.key === 'Enter') sendMessage(roomName);
  });

  chatsContainer.appendChild(chatBox);
  activeChats[roomName] = chatBox;
}

// Append a message to the chat
function appendMessageToChat(roomName, sender, message) {
  const messagesDiv = document.getElementById(`messages-${roomName}`);
  if (!messagesDiv) return;

  const messageElement = document.createElement('div');
  messageElement.textContent = `${sender}: ${message}`;
  messagesDiv.appendChild(messageElement);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Send message
function sendMessage(roomName) {
  const input = document.getElementById(`message-${roomName}`);
  const message = input.value.trim();
  if (!message) return;

  socket.emit('send_message', { username, message, room: roomName });
  appendMessageToChat(roomName, 'You', message);
  input.value = '';
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
