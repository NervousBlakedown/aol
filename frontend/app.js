// app.js

let socket;
let typingTimeout;
let currentRoom = null; // Keep track of the active chat room
let username = null; // Store the logged-in username

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

  // Send the signup details to the server
  fetch('/signup', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: email,
      username: usernameInput,
      password: password
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('Account created successfully.');
        // Redirect to login page
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

// Handle the login process
function login() {
  username = document.getElementById('username').value.trim(); // store logged-in user
  const password = document.getElementById('password').value.trim();

  if (!username || !password) {
    alert('Please enter both your screen name and password.');
    return;
  }

  // Fetch request to the server for authentication
  fetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: username,
      password: password
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Login successful.');
      // Establish a Socket.IO connection on successful login
      socket = io();

      socket.on('connect', function() {
        console.log('Connected to Socket.IO server.');
        socket.emit('login', { username: username });
        document.getElementById('login').style.display = 'none';
        document.getElementById('contacts').style.display = 'block';
        document.getElementById('chat').style.display = 'block';
        playLoginSound();

        // Handle incoming messages
        socket.on('message', function (data) {
          displayMessage(data.username, data.msg);
        });

        // Handle typing notifications
        socket.on('typing', function (data) {
          document.getElementById('typing').textContent = `${data.username} is typing...`;
        });

        socket.on('stop_typing', function (data) {
          document.getElementById('typing').textContent = '';
        });

        // Update contacts list
        socket.on('user_list', function (data) {
          updateContactsList(data.users);
        });

        // Handle chat started event
        socket.on('chat_started', function (data) {
          currentRoom = data.room;
          console.log(`Joined chat room: ${currentRoom}`);
        });

        socket.on('disconnect', function () {
          console.log('Disconnected from Socket.IO server.');
        });

        socket.on('connect_error', function (err) {
          console.error('Socket.IO connect error:', err);
        });
      });
    } else {
      alert('Login failed: ' + data.message);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error occurred during login.');
  });
}

// Function to update the list of online users (contacts) with checkboxes for group selection
function updateContactsList(users) {
  let contactsList = document.getElementById('contacts-list');
  contactsList.innerHTML = ''; // Clear the existing list

  users.forEach(function (user) {
    let contactItem = document.createElement('li');

    // Skip the current user
    if (user.username === username) return;

    // Create a checkbox for each contact
    let checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = user.username; // Adjusted to match the data structure
    checkbox.className = 'contact-checkbox'; // Class to make selection easier

    // Add the contact name next to the checkbox
    let label = document.createElement('label');
    label.innerText = `${user.username} (${user.status})`; // Display username and status

    // Append the checkbox and label to the list item
    contactItem.appendChild(checkbox);
    contactItem.appendChild(label);

    // Add the contact item to the list
    contactsList.appendChild(contactItem);
  });
}

// Start a chat
function startChat(users) {
  if (!users || users.length == 0) {
    alert('You must select at least one user to start chatting...obviously.');
    return;
  }
  // add current user to the chat to ensure you're part of the chat
  users.push(username);

  currentRoom = users.join('_'); // Use usernames to create a unique room ID
  socket.emit('start_chat', { users });
  console.log('Starting chat with: ${users.join(', ')} in room: ${currentRoom}');
}

// Function to initiate a group chat
function startGroupChat() {
  let selectedUsers = [];

  // Get all selected checkboxes
  const checkboxes = document.querySelectorAll('.contact-checkbox:checked');
  checkboxes.forEach(function (checkbox) {
    selectedUsers.push(checkbox.value);
  });
  // start chat with selected users
  startChat(selectedUsers);
}


// Send a chat message
function sendMessage() {
  const messageInput = document.getElementById('message');
  const message = messageInput ? messageInput.value.trim() : '';

  if (message === '') {
    return; // Avoid sending empty messages
  }

  // Display the sent message immediately
  displayMessage(username, message);

  // Send the message over the Socket.IO connection
  console.log('Sending message:', message);
  socket.emit('send_message', {
    username: username,
    message: message,
    room: currentRoom // Send message to the current chat room
  });

  // Play the AOL sound effect
  playAOLSound();

  // Clear the input field
  messageInput.value = '';
}

// Display messages in the chat area
function displayMessage(username, message) {
  let messages = document.getElementById('messages');
  let messageDiv = document.createElement('div');
  messageDiv.textContent = `${username}: ${message}`;
  messages.appendChild(messageDiv);

  // Scroll to the latest message
  messages.scrollTop = messages.scrollHeight;
  playMessageReceiveSound(); // Play sound when a new message is received
}


// Send typing notifications
function sendTypingNotification() {
  if (socket && socket.connected && currentRoom) {
    socket.emit('typing', {
      username: username,
      room: currentRoom // Send typing status to the current chat room
    });

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(function () {
      socket.emit('stop_typing', {
        username: username,
        room: currentRoom
      });
    }, 3000); // Clears typing status after 3 seconds of inactivity
  }
}

// Play the login success sound
function playLoginSound() {
  const loginSound = document.getElementById('login_sound');
  if (loginSound) {
    loginSound.play();
  }
}

// Play the message receive sound
function playMessageReceiveSound() {
  const messageReceiveSound = document.getElementById('message_receive_sound');
  if (messageReceiveSound) {
    messageReceiveSound.play();
  }
}

// Play the AOL message sent sound
function playAOLSound() {
  const aolSound = document.getElementById('message_sent_sound');
  if (aolSound) {
    aolSound.play();
  }
}

// Add event listeners after DOM content is loaded
document.addEventListener('DOMContentLoaded', function () {
  // For 'login' button
  const loginButton = document.getElementById('login-button');
  if (loginButton) {
    loginButton.addEventListener('click', login);
  }

  // For 'create account' button
  const createAccountButton = document.getElementById('create-account-button');
  if (createAccountButton) {
    createAccountButton.addEventListener('click', createAccount);
  }

  // For 'send message' button
  const sendMessageButton = document.getElementById('send-message-button');
  if (sendMessageButton) {
    sendMessageButton.addEventListener('click', sendMessage);
  }

  // For 'start chat' button
  const startChatButton = document.getElementById('start-chat-button');
  if (startChatButton) {
    startChatButton.addEventListener('click', startGroupChat);
  }

  // Add event listener for 'Enter' key to send message
  const messageInput = document.getElementById('message');
  if (messageInput) {
    messageInput.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        sendMessage();
      }
    });

    // Add event listener for input to send typing notifications
    messageInput.addEventListener('input', sendTypingNotification);
  }
});
