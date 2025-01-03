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

  // Listen for incoming Topic messages (not Private)
  socket.on('topic_message', (data) => {
    console.log('Received topic message:', data);
  
    const { topic, username, message, timestamp } = data;
  
    console.log(`Extracted Message: ${message}`);
    console.log(`Username: ${username}, Timestamp: ${timestamp}`);
  
    if (!message) {
      console.error('Received topic message with undefined content:', data);
      return;
    }
  
    const chatBox = document.getElementById(`messages-${encodeRoomName(topic)}`);
    if (chatBox) {
      const messageElement = document.createElement('div');
      messageElement.className = 'message';
      messageElement.innerHTML = `
        <div><strong>${username}</strong>: ${message}</div>
        <div class="timestamp">${new Date(timestamp).toLocaleTimeString()}</div>
      `;
      chatBox.appendChild(messageElement);
      chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
    }
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

  // listen
  socket.on('private_message', (data) => {
    appendMessageToChat(data.room, data.username, data.msg, data.timestamp);
  });

  // user list
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
    //Avatar upload logic
    const avatarButton = document.getElementById('change-avatar-button');
    const avatarInput = document.getElementById('avatar-upload');
    const avatarImage = document.getElementById('profile-avatar');
    if (avatarButton && avatarInput) {
      // Trigger file input when button is clicked
      avatarButton.addEventListener('click', () => avatarInput.click());

      // Handle file selection and upload
      avatarInput.addEventListener('change', async () => {
          const file = avatarInput.files[0];
          if (!file) return;

          // Validate file type
          const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
          if (!allowedTypes.includes(file.type)) {
              alert('Please upload a valid image file (PNG, JPEG, JPG, GIF).');
              return;
          }

          const formData = new FormData();
          formData.append('avatar', file);

          try {
              const response = await fetch('/upload_avatar', {
                  method: 'POST',
                  body: formData,
                  credentials: 'include'
              });

              const data = await response.json();
              if (response.ok && data.success) {
                  // Update the avatar image dynamically
                  avatarImage.src = `${data.avatar_url}?t=${new Date().getTime()}`;
                  alert('Avatar updated successfully!');
              } else {
                  alert(data.message || 'Failed to upload avatar.');
              }
            } catch (error) {
              console.error('Error uploading avatar:', error);
              alert('An error occurred while uploading the avatar.');
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

// create Topic chats (different from Private chats)
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

  // If activeChats already has messages, reuse them
  if (activeChats[roomName]) {
    console.log(`Reopening topic chat: ${topicName}`);
    topicsContainer.appendChild(activeChats[roomName].chatBox);
    return;
  }

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

    // Load saved messages first client side
    if (activeChats[roomName]?.messages) {
      // Load saved messages first
      activeChats[roomName].messages.forEach(msgHTML => {
        const msgDiv = document.createElement('div');
        msgDiv.innerHTML = msgHTML;
        messagesDiv.appendChild(msgDiv);
      });
    }

    data.messages.forEach(msg => {
      appendMessageToChat(roomName, msg.username, msg.message, msg.timestamp);
    });
  })
  .catch(err => console.error('Error fetching topic chat history:', err));
  activeChats[roomName] = { chatBox, messages: [] }; // stored
  // activeChats[roomName] = chatBox;
}

// Open private chats
function openPrivateChat(participants) {
  const roomName = participants.sort().join('_'); // Consistent room naming

  if (!activeChats[roomName]) {
      // If this room hasn't been opened, create it and fetch history
      activeChats[roomName] = []; // Initialize message storage
      createChatBox(roomName, participants);

      fetch(`/get_private_chat_history?room=${roomName}`)
          .then(response => response.json())
          .then(data => {
              if (data.success) {
                  activeChats[roomName] = data.messages || []; // Store history locally
                  displayChatHistory(roomName); // Display the history in the UI
              } else {
                  console.error('Failed to load chat history:', data.message);
              }
          })
          .catch(error => console.error('Error fetching chat history:', error));
  } else {
      // If the chat box already exists, just display the stored messages
      createChatBox(roomName, participants);
      displayChatHistory(roomName);
  }
}

// send private message
function sendPrivateMessage(roomName) {
  const input = document.getElementById(`message-${roomName}`);
  const message = input.value.trim();
  if (!message) return;

  const timestamp = new Date().toLocaleTimeString();

  socket.emit('send_private_message', {
      room: roomName,
      username: username,
      message: message,
      timestamp: timestamp
  });

  appendMessageToChat(roomName, 'You', message, timestamp);
  input.value = '';
}

// Load Topics table messages
function loadTopicHistory(topicName) {
  console.log(`Fetching topic history for: ${topicName}`);
  
  fetch(`/get_topic_history?topic=${encodeURIComponent(topicName)}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Network response was not ok (${response.status})`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Fetched Data:', data); // Log the entire JSON response

      if (data.messages && Array.isArray(data.messages)) {
        const chatBox = document.getElementById(`messages-${topicName}`);
        if (!chatBox) {
          console.error(`Chat box for topic "${topicName}" not found.`);
          return;
        }

        chatBox.innerHTML = ''; // Clear previous messages

        data.messages.forEach((msg, index) => {
          console.log(`Message #${index + 1}:`, msg); // Log each message object
          console.log(`Username: ${msg.username}, Message: ${msg.message}, Timestamp: ${msg.timestamp}`);

          // Explicit checks for each property
          const displayedMessage = msg?.message || '[Empty Message]';
          const displayedUsername = msg?.username || '[Unknown User]';
          const displayedTimestamp = msg?.timestamp
            ? new Date(msg.timestamp).toLocaleString()
            : '[Invalid Timestamp]';

          console.log(`Rendering - Username: ${displayedUsername}, Message: ${displayedMessage}, Timestamp: ${displayedTimestamp}`);

          const messageElement = document.createElement('div');
          messageElement.className = 'message';

          // Use textContent instead of innerHTML for message security
          const userElement = document.createElement('div');
          userElement.innerHTML = `<strong>${displayedUsername}</strong>: ${displayedMessage}`;
          
          const timestampElement = document.createElement('div');
          timestampElement.className = 'timestamp';
          timestampElement.textContent = displayedTimestamp;

          messageElement.appendChild(userElement);
          messageElement.appendChild(timestampElement);

          chatBox.appendChild(messageElement);
        });

        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to bottom
      } else {
        console.warn('No messages returned from the server.');
      }
    })
    .catch(error => {
      console.error('Error loading topic history:', error);
    });
}

// Display chat history
function displayChatHistory(roomName) {
  const messagesDiv = document.getElementById(`messages-${roomName}`);
  if (!messagesDiv) return;

  messagesDiv.innerHTML = ''; // Clear existing content

  activeChats[roomName].forEach(msg => {
      appendMessageToChat(
          roomName,
          msg.username,
          msg.message,
          new Date(msg.timestamp).toLocaleTimeString()
      );
  });
}

// Edit Bio
function editBio() {
  const newBio = prompt('Enter your new bio:');
  if (newBio !== null) {
      fetch('/api/update-bio', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bio: newBio }),
          credentials: 'include'
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              document.getElementById('profile-bio').textContent = `"${newBio}"`;
              console.log('✅ Bio updated successfully.');
          } else {
              console.error('❌ Failed to update bio:', data.message);
          }
      })
      .catch(error => console.error('❌ Error:', error));
  }
}

// Change Password
// Change Password
function changePassword() {
  const newPassword = prompt('Enter your new password (minimum 8 characters):');
  if (!newPassword) {
      console.warn('❌ Password change canceled by user.');
      return;
  }

  if (newPassword.length < 8) {
      alert('❌ Password must be at least 8 characters long.');
      return;
  }

  fetch('/api/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: newPassword }),
      credentials: 'include'
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          alert('✅ Password changed successfully! Please log in again with your new password.');
          logout(); // Log out user to force re-authentication
      } else {
          alert(`❌ Failed to change password: ${data.message}`);
          console.error('❌ Password change error:', data.message);
      }
  })
  .catch(error => {
      console.error('❌ Error changing password:', error);
      alert('❌ An error occurred while changing the password. Please try again later.');
  });
}

// Deactivate Account
function deactivateAccount() {
  const confirmation = confirm('⚠️ Are you sure you want to deactivate your account? This action cannot be undone.');
  if (!confirmation) {
      console.warn('❌ Account deactivation canceled by user.');
      return;
  }

  fetch('/api/deactivate-account', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          alert('✅ Your account has been deactivated. Goodbye!');
          logout(); // Log out user after account deactivation
      } else {
          alert(`❌ Failed to deactivate account: ${data.message}`);
          console.error('❌ Account deactivation error:', data.message);
      }
  })
  .catch(error => {
      console.error('❌ Error deactivating account:', error);
      alert('❌ An error occurred while deactivating your account. Please try again later.');
  });
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

// Handle Notifications Dropdown
function initializeNotifications() {
  const notificationsButton = document.getElementById('notifications-button');
  const notificationsDropdown = document.getElementById('notifications-dropdown');
  const notificationCount = document.getElementById('notification-count');

  if (!notificationsButton || !notificationsDropdown || !notificationCount) {
    console.error('❌ Notifications elements not found in the DOM.');
    return;
  }

  // Toggle Dropdown Visibility
  notificationsButton.addEventListener('click', () => {
    notificationsDropdown.style.display = notificationsDropdown.style.display === 'block' ? 'none' : 'block';
  });

  // Fetch Notifications from the Backend
  function fetchNotifications() {
    fetch('/api/get-notifications', { credentials: 'include' })
      .then(response => response.json())
      .then(data => {
        if (data.success && data.notifications) {
          notificationsDropdown.innerHTML = ''; // Clear existing notifications

          data.notifications.forEach(notification => {
            const notificationItem = document.createElement('li');
            notificationItem.textContent = notification.message;
            notificationItem.onclick = () => handleNotificationClick(notification.link);
            notificationsDropdown.appendChild(notificationItem);
          });

          // Update Notification Count
          notificationCount.textContent = data.notifications.length;
          notificationCount.style.display = data.notifications.length > 0 ? 'inline' : 'none';
        } else {
          console.warn('No notifications found or error fetching notifications.');
          notificationsDropdown.innerHTML = '<li>No new notifications</li>';
          notificationCount.style.display = 'none';
        }
      })
      .catch(error => console.error('❌ Error fetching notifications:', error));
  }

  // Handle Clicking on a Notification
  function handleNotificationClick(link) {
    if (link) {
      window.location.href = link;
    }
    notificationsDropdown.style.display = 'none';
  }

  // Initial Fetch on Load
  fetchNotifications();

  // Fetch Notifications Periodically (e.g., every 30 seconds)
  setInterval(fetchNotifications, 30000);
}

// Notify missed messages (@ in Topics)
function notifyMissedTopicMessages(topicId, missedCount) {
  if (isNaN(topicId)) {
      console.error('❌ Invalid topic ID. Expected an integer.');
      return;
  }

  fetch('/api/handle-missed-topic', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
          topic_id: parseInt(topicId, 10), // Ensure it's an integer
          missed_messages: missedCount
      }),
      credentials: 'include'
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          console.log('✅ Missed topic notification logged.');
      } else {
          console.error('❌ Failed to log missed topic notification:', data.message);
      }
  })
  .catch(error => console.error('❌ Error:', error));
}

// Topics mention notification
function sendTopicMessage(topicId, message) {
  const mentionRegex = /@(\w+)/g;
  const mentions = [...message.matchAll(mentionRegex)].map(match => match[1]);

  fetch('/api/send-topic-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic_id: topicId, message, mentions }),
      credentials: 'include'
  });
}

// Send message (Private, not Topic)
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

// Send Topic Message with Real-Time UI Update
function sendTopicMessage(topicName) {
  const input = document.getElementById(`message-${encodeRoomName(topicName)}`);
  const message = input.value.trim();

  if (!message) {
    console.warn('Cannot send an empty message.');
    return;
  }

  fetch('/send_topic_message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic: topicName, username, message })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // appendMessageToChat(topicName, username, message, new Date().toLocaleTimeString());
        input.value = '';
      } else {
        console.error('Failed to send message:', data.error);
      }
    })
    .catch(error => console.error('Error:', error));
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

  // Ensure activeChats[roomName] is an array
  if (!Array.isArray(activeChats[roomName])) {
    console.warn(`activeChats[${roomName}] was not an array. Resetting to an empty array.`);
    activeChats[roomName] = [];
  }

  // Ensure messages are stored locally
  if (!activeChats[roomName]) activeChats[roomName] = [];
  activeChats[roomName].push({
      username: sender,
      message: message,
      timestamp: timestamp
  });

  // Format timestamp for display
  const formattedTimestamp = formatTimestamp(timestamp); 

  // Create message element
  const messageElement = document.createElement('div');
  messageElement.className = sender === 'You' ? 'message sender' : 'message receiver';

  messageElement.innerHTML = `
      <div class="message-meta">
          <span class="message-sender">${sender}</span>
          <span class="message-timestamp">${formattedTimestamp}</span>
      </div>
      <div class="message-text">${message}</div>
  `;

  // Append the message to the chat window
  messagesDiv.appendChild(messageElement);
  messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to bottom
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
