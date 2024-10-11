let websocket;
let typingTimeout;

// account creation
function createAccount() {
  const email = document.getElementById('email').value.trim();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();

  if (!email || !username || !password) {
    alert('All fields are required.');
    return;
  }

  // Send the signup details to the server
  fetch('/signup', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      username: username,
      password: password
    }),
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Account created successfully!');
      // Redirect to login page
      window.location.href = 'index.html';
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
  const username = document.getElementById('username').value;

  if (!username) {
    alert("Please enter a screen name.");
    return;
  }

  // Establish a WebSocket connection
  // websocket = new WebSocket("ws://localhost:8080");
  websocket = new WebSocket("ws://127.0.0.1:8080");


  websocket.onopen = function() {
    console.log("Connected to WebSocket server.");
    document.getElementById('login').style.display = 'none';
    document.getElementById('chat').style.display = 'block';
  };

  websocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("Received data:", data); // Debugging output

    switch(data.type) {
      case 'message':
        displayMessage(data.username, data.message);
        break;
      case 'typing':
        document.getElementById('typing').textContent = `${data.username} is typing...`;
        break;
      case 'stop_typing':
        document.getElementById('typing').textContent = '';
        break;
      default:
        console.error("Unsupported message type:", data.type);
    }
  };

  websocket.onerror = function(event) {
    console.error("WebSocket error:", event);
  };

  websocket.onclose = function(event) {
    console.log("WebSocket connection closed:", event);
  };
}

// Function to play login success sound
function playLoginSound() {
  const loginSound = document.getElementById("login_sound");
  loginSound.play();
}

// Function to play the message receive sound
function playMessageReceiveSound() {
  const messageReceiveSound = document.getElementById("message_receive_sound");
  messageReceiveSound.play();
}

// Play the AOL sound when a message is sent
function playAOLSound() {
  const aolSound = document.getElementById("message_sent_sound");
  aolSound.play();
}

// Send a chat message
function sendMessage() {
  const message = document.getElementById('message').value.trim();

  if (message === "") {
    return; // Avoid sending empty messages
  }

  // Display the sent message immediately
  displayMessage(document.getElementById('username').value, message);

  // Send the message over the WebSocket connection
  console.log("Sending message:", message); // Debugging output
  websocket.send(JSON.stringify({
    type: 'message',
    username: document.getElementById('username').value,
    message: message
  }));

  // Play the AOL sound effect
  playAOLSound();

  // Clear the input field
  document.getElementById('message').value = '';
}

// Display messages in the chat area
function displayMessage(username, message) {
  let messages = document.getElementById('messages');
  let messageDiv = document.createElement('div');
  messageDiv.textContent = `${username}: ${message}`;
  messages.appendChild(messageDiv);

  // Scroll to the latest message
  messages.scrollTop = messages.scrollHeight;
}

// Send typing notifications
function sendTypingNotification() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: 'typing',
      username: document.getElementById('username').value
    }));

    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(function() {
      websocket.send(JSON.stringify({
        type: 'stop_typing',
        username: document.getElementById('username').value
      }));
    }, 3000); // Clears typing status after 3 seconds of inactivity
  }
}

// Add event listener for 'Enter' key to send message
document.getElementById('message').addEventListener('keydown', function(event) {
  if (event.key === 'Enter') {
    sendMessage();
  }
});
