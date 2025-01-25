// frontend/static/js/modules/chat.js
// Manages UI interactions (starting chats, appending messages, opening chatboxes)
import { socket, sendMessageRealtime } from './socket.js';
import { encodeRoomName, sanitizeInput } from './utils.js';

export let activeChats = {};

// Initialize Chat
export function initializeChat() {
    console.log('✅ initializeChat called');
    const chatButton = document.getElementById('chat-button');
    if (!chatButton) {
        console.error('❌ Chat button not found in DOM.');
        return;
    }

    // Ensure only one listener is attached
    if (!chatButton.dataset.listener) {
        chatButton.addEventListener('click', startChat);
        chatButton.dataset.listener = "true";
        console.log('✅ Chat button initialized successfully.');
    }
}


// Get usernames 
function getUsername() {
    return new Promise((resolve, reject) => {
        const username = sessionStorage.getItem('username');
        if (username) {
            resolve(username); // Resolve with the username
        } else {
            console.error('❌ Username not found in SessionStorage. Please log in again.');
            alert('❌ Unable to retrieve username. Please log in again.');
            reject(new Error('Username not found.'));
        }
    });
}


// start chat
function startChat() {
    console.log('✅ startChat called');
    getUsername().then(username => {
        console.log('Username:', username);
        if (!username) return;

        const selectedContacts = Array.from(
            document.querySelectorAll('.contact-checkbox:checked')
        ).map(cb => cb.value);

        if (selectedContacts.length === 0) {
            alert('Please select at least one contact.');
            return;
        }

        const allParticipants = [username, ...selectedContacts].sort((a, b) => a.localeCompare(b));
        const sortedRoomName = allParticipants.sort().join('_'); // Ensure correct room name format
        // const internalRoomName = allParticipants.sort().join('_');
        const displayName = selectedContacts.join(', ');

        fetch('/chat/start_chat', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('jwt_token')}` 
            },
            body: JSON.stringify({ users: allParticipants })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    socket.emit('join_room', { room: sortedRoomName, username });
                    openChatRoom(sortedRoomName, displayName);

                    // Deselect all checkboxes
                    document.querySelectorAll('.contact-checkbox:checked').forEach(cb => {
                        cb.checked = false;
                    });
                    console.log('✅ Checkboxes deselected after chat started.');
                } else {
                    alert(`❌ Failed to start chat: ${data.message}`);
                }
            })
            .catch(err => {
                alert('❌ An error occurred while starting the chat.');
                console.error(err);
            });
    });
}
  

// Open Chat Room
function openChatRoom(roomName, chatTitle) {
  if (!roomName) {
    console.error('❌ Room name is required to open a chat.');
    return;
  }

  const chatsContainer = document.getElementById('chats-container');
  if (!chatsContainer) {
    console.error('❌ Chats container not found.');
    return;
  }

  const encodedRoomName = encodeRoomName(roomName);

  if (activeChats[encodedRoomName]) {
  //if (document.getElementById(`chat-box-${encodedRoomName}`)) {
    //console.warn(`Chat box for room '${roomName}' is already open.`);
    return;
  }

  console.log(`Opening chat room (DB key): ${roomName}, display: ${chatTitle}`);
  createChatBox(roomName, chatTitle);
  fetchMessagesForRoom(roomName);
  activeChats[encodedRoomName] = true;
}


// Load existing messages for each designated room
function fetchMessagesForRoom(roomName) {
  const username = sessionStorage.getItem('username');
  if (!username) {
    console.error('username not found in sessionStorage');
    return;
  }

  // Ensure the correct room name format before fetching messages
  //const sortedRoomName = roomName.split('_').sort().join('_');

  fetch(`/chat/get_private_chat_history?room=${roomName}`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.messages) {
        console.log(`✅ Messages loaded for room ${roomName}`, data.messages);
        data.messages.forEach(msg => {
          appendMessageToChat(
            roomName,
            msg.username === username ? 'You' : msg.username,
            //msg.username,
            msg.message,
            msg.timestamp
          );
        });
      } else {
        console.warn('No messages or error fetching chat history:', data);
      }
    })
    .catch(err => console.error('❌ Error fetching room history:', err));
}


// Append Message
export function appendMessageToChat(roomName, sender, message, timestamp) {
  if (!roomName) {
    console.error('❌ Room name is undefined. Cannot append message.');
    return;
  }

  const encodedRoomName = encodeRoomName(roomName);
  const chatBox = document.getElementById(`messages-${encodedRoomName}`);
  if (!chatBox) {
    console.error(`❌ Chat box for room '${roomName}' not found.`);
    return;
  }

  const messageElement = document.createElement('div');
  messageElement.className = sender === 'You' ? 'message sender' : 'message receiver';
  messageElement.innerHTML = `
    <div class="message-meta">
      <span class="message-sender">${sanitizeInput(sender)}</span>
      <span class="message-timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
    </div>
    <div class="message-text">${sanitizeInput(message)}</div>
  `;
  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Create Chat Box UI
export function createChatBox(roomName, chatTitle) {
  const chatsContainer = document.getElementById('chats-container');
  if (!chatsContainer) {
    console.error('❌ Chats container not found.');
    return;
  }

  const encodedRoomName = encodeRoomName(roomName);

  if (document.getElementById(`chat-box-${encodedRoomName}`)) {
    // console.warn(`Chat box for room '${roomName}' is already open.`);
    return; // Prevent duplicate chat boxes
  }

  const chatBox = document.createElement('div');
  chatBox.className = 'chat-box';
  chatBox.id = `chat-box-${encodedRoomName}`;
  chatBox.innerHTML = `
    <div class="chat-header">
      <h3>${sanitizeInput(chatTitle)}</h3>
      <button class="close-chat" data-room="${encodedRoomName}">X</button>
    </div>
    <div class="messages" id="messages-${encodedRoomName}"></div>
    <input type="text" id="message-${encodedRoomName}" placeholder="Type a message..." />
    <button id="send-${encodedRoomName}" class="btn-send">Send</button>
  `;

  chatsContainer.appendChild(chatBox);

  const inputField = document.getElementById(`message-${encodedRoomName}`);
  inputField.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendMessage(roomName);
    }
  });

  const sendButton = document.getElementById(`send-${encodedRoomName}`);
  sendButton.addEventListener('click', () => sendMessage(roomName));

  const closeBtn = chatBox.querySelector(`[data-room="${encodedRoomName}"]`);
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      chatBox.remove();
      delete activeChats[encodedRoomName];
      console.log(`✅ Chat box for room '${roomName}' closed.`);
    });
  }

  activeChats[roomName] = chatBox;
}

// Send Message
function sendMessage(roomName) {
  const encodedRoomName = encodeRoomName(roomName);
  const input = document.getElementById(`message-${encodedRoomName}`);
  const message = sanitizeInput(input.value.trim());
  if (!message) return;

  const username = sessionStorage.getItem('username');
  if (!username) {
    console.error('❌ Username is not defined in sessionStorage. Cannot send message.');
    alert('❌ Username is not defined. Please refresh the page or log in again.');
    return;
  }

  // This uses your existing route-based approach (/chat/send_message),
  // which in turn calls handle_private_message(...) and does socketio.emit('private_message').
  fetch('/chat/send_message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room: roomName,
      username: username,
      message: message
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        // Append locally
        //appendMessageToChat(roomName, 'You', message, new Date().toISOString());
        input.value = '';
      } else {
        console.error('❌ Failed to send message:', data.message);
        alert(`❌ Failed to send message: ${data.message}`);
      }
    })
    .catch(err => {
      console.error('❌ Error sending message:', err);
      alert('❌ An error occurred while sending the message.');
    });
}
