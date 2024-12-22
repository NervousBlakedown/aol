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
const roomEncodings = {}; // Global mapping of room names to encoded room names


// Base64 encoding to fix special character username chats
function encodeRoomName(roomName) {
  return btoa(roomName); 
}

function decodeRoomName(encodedName) {
  return atob(encodedName);
}

// Init DB
function initializeSupabase() {
  if (!window.supabase || !window.supabase.createClient) {
    console.error("Supabase library not loaded or createClient is undefined.");
    return;
  }
  const { createClient } = window.supabase;
  supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
  console.log('Supabase initialized.');
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

// Set up Socket.IO
function setupSocketIO() {
  socket = io();

  socket.on('connect', () => {
    console.log('Socket.IO connected with ID:', socket.id);
    // test broadcast
    socket.emit('test_broadcast');
    console.log('Broadcast test emitted.');

  socket.on('test', (data) => {
    console.log("Received broadcast message:", data.message); // data.msg
});
    if (username) socket.emit('login', { username });
  });

  socket.on('chat_started', (data) => {
    const { room, users } = data;
  
    // If sender initiated the chat, the chat box is already created
    if (activeChats[room]) return;
  
    // Generate title excluding the current user's name
    const chatTitle = users.filter(user => user !== username).join(', ');
    createChatBox(room, chatTitle);
  });
  
  socket.on('message', data => {
    console.log('Received message:', data);
    appendMessageToChat(data.room, data.username, data.message, data.timestamp); // data.msg
  });

  // Handle incoming typing events
  socket.on('typing', (data) => {
    const encodedRoomName = roomEncodings[data.room]; // Map room to encoded name
    const typingIndicator = document.getElementById(`typing-${encodedRoomName}`); // RoomName
    if (typingIndicator) {
      typingIndicator.textContent = `${data.username} is typing...`;
      typingIndicator.style.display = 'block';
    }
  });

// Handle stop typing events
  socket.on('stop_typing', (data) => {
    const encodedRoomName = roomEncodings[data.room]; // Map room to encoded name
    const typingIndicator = document.getElementById(`typing-${encodedRoomName}`);
    if (typingIndicator) {
      typingIndicator.style.display = 'none';
    }
  });

  socket.on('user_list', data => {
    console.log("Received user list:", data.users);
    userStatuses = {};
    data.users.forEach(user => {
      userStatuses[user.username] = user.status;
    });
    console.log("Updated user statuses:", userStatuses); 
    updateContactsList();
  });
}

// Page Initialization
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
                      // Ensure results is an array
                      if (!Array.isArray(results)) {
                        console.error('Unexpected response format:', results);
                        resultsList.innerHTML = '<li>Error fetching users. Try again later.</li>';
                        return;
                      }
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

// core features (dashboard-specific)
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
    if (contact.username !== username) {
      const listItem = document.createElement('li');
      listItem.innerHTML = `
      <input type="checkbox" class="contact-checkbox" value="${contact.username}">
      <label>${contact.username} (${userStatuses[contact.username] || 'Offline'})</label>
    `;
      contactsList.appendChild(listItem);

    }
    
  });
}

// Messaging and Chat Functions
// Start Chat
function startChat() {
  const selectedContacts = Array.from(
    document.querySelectorAll('.contact-checkbox:checked')
  ).map(cb => cb.value);

  if (selectedContacts.length === 0) {
    alert('Please select at least one Pal.');
    return;
  }

  // Generate room name and chat participants
  const roomParticipants = [username, ...selectedContacts].sort();
  const roomName = roomParticipants.join('_');
  console.log(`Starting chat with: ${selectedContacts}, Room: ${roomName}`);

  // Avoid creating duplicate chat boxes
  if (!activeChats[roomName]) {
    const chatTitle = selectedContacts.join(', '); // Exclude sender's name
    createChatBox(roomName, chatTitle); // Only include other participants in the title
    socket.emit('start_chat', { users: roomParticipants, room: roomName });
  }
  // Deselect all checkboxes
  document.querySelectorAll('.contact-checkbox').forEach(cb => (cb.checked = false));
}

// create Topic chats (different from private chats)
function openTopicChat(topicName) {
  const topicsContainer = document.getElementById('topics-container');
  if (!topicsContainer) {
      console.error('Topics container not found.');
      return;
  }

  // Prevent duplicate topic chats
  if (document.getElementById(`topic-chat-${topicName}`)) {
    console.warn(`Topic chat for "${topicName}" is already open.`);
    return;
  }

  const roomName = `topic_${topicName}`;
  if (activeChats[roomName]) {
      console.log(`Topic chat "${topicName}" is already open.`);
      return;
  }

  const encodedRoomName = encodeRoomName(roomName);
  roomEncodings[roomName] = encodedRoomName;

  const chatBox = document.createElement('div');
  chatBox.className = 'topic-chat-box';
  chatBox.id = `chat-box-${encodedRoomName}`;

  chatBox.innerHTML = `
      <div class="chat-header">
          <h3>${topicName}</h3>
          <button class="close-chat" data-room="${encodedRoomName}">X</button>
      </div>
      <div class="messages" id="messages-${encodedRoomName}"></div>
      <div class="chat-input">
        <input type="text" id="message-${encodedRoomName}" placeholder="Type a message..." />
        <button onclick="sendMessage('${roomName}')">Send</button>
      </div>
  `;

  topicsContainer.appendChild(chatBox);

  const messageInput = document.getElementById(`message-${encodedRoomName}`);
  if (!messageInput) {
      console.error(`Message input not found for topic: ${topicName}`);
      return;
  }

  // Typing events
  messageInput.addEventListener('input', () => {
      socket.emit('typing', { room: roomName, username });
      clearTimeout(typingTimeout);
      typingTimeout = setTimeout(() => {
          socket.emit('stop_typing', { room: roomName, username });
      }, 2000);
  });

  // Send message on Enter
  messageInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
          sendMessage(roomName);
      }
  });

  // Close button
  const closeButton = chatBox.querySelector('.close-chat');
  closeButton.addEventListener('click', () => {
      topicsContainer.removeChild(chatBox);
      delete activeChats[roomName];
  });

  


  // Fetch historical messages
  fetch(`/get_topic_history?topic=${encodeURIComponent(topicName)}`)
  .then(response => response.json())
  .then(data => {
    const messagesDiv = document.getElementById(`messages-${encodedRoomName}`);
    if (!messagesDiv) {
      console.error(`Messages container not found for topic: ${topicName}`);
      return;
    }

    data.messages.forEach(msg => {
      appendMessageToChat(roomName, msg.username, msg.text, msg.timestamp);
    });
  })
  .catch(err => console.error('Error fetching topic chat history:', err));
  activeChats[roomName] = chatBox;
}

// change online status
function updateStatus(newStatus) {
  if (!socket) {
    console.error('Socket.IO is not initialized. Cannot update status.');
    return;
  }

  // Emit the status_change event to the server
  socket.emit('status_change', { username, status: newStatus });
  console.log(`Status updated to: ${newStatus}`);
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

// Create chat box
function createChatBox(roomName, chatTitle) {
  const chatsContainer = document.getElementById('chats-container');
  if (!chatsContainer) {
    console.error('Chats container not found.');
    return;
  }

  if (activeChats[roomName]) return; // Prevent duplicate boxes

  const encodedRoomName = encodeRoomName(roomName);
  roomEncodings[roomName] = encodedRoomName;

  const chatBox = document.createElement('div');
  chatBox.className = 'chat-box';
  chatBox.id = `chat-box-${encodedRoomName}`;

  chatBox.innerHTML = `
    <div class="chat-header">
      <h3>${chatTitle}</h3>
      <button class="close-chat" data-room="${encodedRoomName}">X</button>
    </div>
    <div class="messages" id="messages-${encodedRoomName}"></div>
    <div class="typing-indicator" id="typing-${encodedRoomName}" style="display: none;"></div>
    <input type="text" id="message-${encodedRoomName}" placeholder="Type a message..." />
    <button onclick="sendMessage('${roomName}')">Send</button>
  `;

  chatsContainer.appendChild(chatBox);

  // Attach keydown listener to the message input field
  const messageInput = document.getElementById(`message-${encodedRoomName}`);
  if (!messageInput) {
    console.error(`Message input not found for room: ${roomName}`);
    return;
  }

  // listen for typing events
  messageInput.addEventListener('input', () => {
    socket.emit('typing', { room: roomName, username });
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
      socket.emit('stop_typing', { room: roomName, username });
    }, 2000); // Stop typing after 2 seconds of no input
  });

  messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendMessage(roomName); // Call sendMessage with the room name
    }
  });

  const closeButton = chatBox.querySelector('.close-chat');
  closeButton.addEventListener('click', () => {
    chatsContainer.removeChild(chatBox);
    delete activeChats[roomName];
  });
  activeChats[roomName] = chatBox;
}

// Function to format timestamps consistently
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) {
      // console.error('Invalid timestamp:', timestamp);
      return timestamp; // Fallback to raw timestamp if invalid
  }
  return date.toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}

// Append a message to the chat window
function appendMessageToChat(roomName, sender, message, timestamp) {
  const encodedRoomName = encodeRoomName(roomName); // Use encoded name for DOM queries
  const messagesDiv = document.getElementById(`messages-${encodedRoomName}`);
  if (!messagesDiv) {
      console.error(`Messages container not found for room: ${roomName}`);
      return;
  }

  const formattedTimestamp = formatTimestamp(timestamp); // Ensure consistent formatting

  const messageElement = document.createElement('div');
  messageElement.className = sender === 'You' ? 'message sender' : 'message receiver';

  messageElement.innerHTML = `
    <div class="message-meta">
        <span class="message-sender">${sender}</span>
        <span class="message-timestamp">${formattedTimestamp}</span>
    </div>
    <span class="message-text">${message}</span>
  `;
  /*messageElement.innerHTML = `
      //<span class="message-text">${message}</span>
      //<span class="message-timestamp">${formattedTimestamp}</span>
  `; */

  messagesDiv.appendChild(messageElement);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Append message
/* function appendMessageToChat(roomName, sender, message, timestamp) {
  const encodedRoomName = encodeRoomName(roomName); // Use encoded name
  const messagesDiv = document.getElementById(`messages-${encodedRoomName}`);
  if (!messagesDiv) return;

  const messageElement = document.createElement('div');
  messageElement.textContent = `[${timestamp}] ${sender}: ${message}`;
  messagesDiv.appendChild(messageElement);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
} */

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
