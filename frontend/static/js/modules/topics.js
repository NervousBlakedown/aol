// frontend/static/js/modules/topics.js
import { socket, ensureSocketInitialized } from './socket.js';
import { encodeRoomName } from './utils.js';

// In-memory tracker of open topic boxes if needed
export const activeTopics = {};

// Initialize any "Topics" logic (TODO: create new topics on the fly? )
export function initializeTopics() {
    const topics = [
        "Science",
        "Religion",
        "News",
        "Movies",
        "Music",
        "Tech",
        "Books",
        "Cooking",
        "Travel",
        "Fitness",
        "Sports",
        "Art",
        "Fashion",
        "History",
        "Photography"
    ]

    // Sort topics alphabetically
    topics.sort((a, b) => a.localeCompare(b));

    // Get the topics container
    const topicsContainer = document.getElementById('topics-container');
    if (!topicsContainer) {
        console.error('❌ Topics container not found.');
        return;
    }

    // Clear existing buttons
    topicsContainer.innerHTML = '';

    // Create buttons for each topic
    topics.forEach(topic => {
        const button = document.createElement('button');
        button.className = 'cta-button topic-button';
        button.setAttribute('data-tooltip', `Discuss about ${topic}`);
        button.textContent = topic;

        // Add event listener to open the topic chat
        button.addEventListener('click', () => {
            openTopicChat(topic);
        });

        // Append the button to the topics container
        topicsContainer.appendChild(button);
    });
}


// Join "Topics" chat (via REST or Socket call)
function joinTopicChat(topicName) {
    const userId = sessionStorage.getItem('user_id');
    const username = window.username; // sessionStorage.getItem('username');

    // If userId is missing, just log error and return
    if (!userId) {
        console.error('❌ joinTopicChat aborted: user_id missing from sessionStorage');
        return;
    }
    if (!username) {
        console.error('❌ joinTopicChat aborted: window.username is missing');
        return;
    }

    fetch('/chat/join_topic_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            topic: topicName,
            user_id: userId,
            username: username
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`✅ Joined topic: ${topicName}`);
        } else {
            console.error(`❌ Failed to join topic: ${data.message}`);
        }
    })
    .catch(error => console.error('❌ Error joining topic chat:', error));
}

// Open a "Topics" chat UI
export function openTopicChat(topicName) {
    ensureSocketInitialized();

    const topicsContainer = document.getElementById('topics-container');
    if (!topicsContainer) {
        console.error('❌ Topics container not found.');
        return;
    }

    // If a chat box for this topic is already open, do nothing
    if (document.getElementById(`topic-chat-${topicName}`)) {
        console.warn(`Topic chat for "${topicName}" is already open.`);
        return;
    }

    // Create DOM
    const roomName = `topic_${topicName}`;
    const encodedRoomName = encodeRoomName(roomName);

    const chatBox = document.createElement('div');
    chatBox.className = 'topic-chat-box';
    chatBox.id = `topic-chat-${topicName}`; 
    chatBox.innerHTML = `
        <div class="chat-header">
            <h3>${topicName}</h3>
            <button class="close-chat" data-room="${encodedRoomName}">X</button>
        </div>
        <div class="messages" id="messages-${encodedRoomName}"></div>
        <input type="text" id="message-${encodedRoomName}" placeholder="Type a message..." />
        <button id="send-btn-${encodedRoomName}">Send</button>
    `;

    topicsContainer.appendChild(chatBox);

    // Event listeners for input + send button
    const msgInput = document.getElementById(`message-${encodedRoomName}`);
    msgInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            sendTopicMessage(topicName);
        }
    });

    const sendButton = document.getElementById(`send-btn-${encodedRoomName}`);
    sendButton.addEventListener('click', () => {
        sendTopicMessage(topicName);
    });

    // Close chat
    const closeBtn = chatBox.querySelector(`.close-chat[data-room="${encodedRoomName}"]`);
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            chatBox.remove();
            delete activeTopics[topicName];
        });
    }

    // Check user ID
    const userId = sessionStorage.getItem('user_id');
    if (!userId) {
        console.error('❌ User ID is missing from sessionStorage; cannot open topic chat fully.');
        return;
    }

    // Join topic socket room
    socket.emit('join_topic_chat', {
        room: roomName,
        username: window.username,
        user_id: userId
    });

    // Also do a REST call to record that the user joined (if needed)
    joinTopicChat(topicName);

    // Fetch existing messages for this topic
    fetchTopicHistory(topicName);

    // Track in activeTopics if you want to
    activeTopics[topicName] = chatBox;
}

// Send a "Topics" message
export function sendTopicMessage(topicName) {
    const roomName = `topic_${topicName}`;
    const encodedRoomName = encodeRoomName(roomName);

    const input = document.getElementById(`message-${encodedRoomName}`);
    if (!input) {
        console.error(`❌ No input found for topic "${topicName}" with id "message-${encodedRoomName}".`);
        return;
    }

    const message = input.value.trim();
    if (!message) {
        console.warn('Cannot send an empty message.');
        return;
    }

    const username = window.username;
    if (!username) {
        console.error('❌ sendTopicMessage aborted: window.username is missing');
        return;
    }

    // POST to your Flask route for "topic" messages
    fetch('/chat/send_topic_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            topic: topicName,
            username: username,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear the input after a successful send
            input.value = '';
            console.log(`✅ Topic message sent: ${message}`);
        } else {
            console.error('❌ Failed to send topic message:', data.error || data.message);
        }
    })
    .catch(error => console.error('❌ Error sending topic message:', error));
}

// Fetch existing messages for this topic (like chat history)
export function fetchTopicHistory(topicName, page = 1, limit = 20) {
    fetch(`/chat/get_topic_history?topic=${encodeURIComponent(topicName)}&page=${page}&limit=${limit}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.messages) {
                data.messages.forEach(msg => {
                    appendTopicMessage(topicName, msg.username, msg.message, msg.timestamp);
                });
            } else {
                console.warn('⚠️ No messages or error fetching topic history:', data.message || data.error);
            }
        })
        .catch(err => console.error('❌ Error fetching topic history:', err));
}

// Helper to append topic messages to the DOM
function appendTopicMessage(topicName, sender, message, timestamp) {
    const encodedRoomName = encodeRoomName(`topic_${topicName}`);
    const messagesDiv = document.getElementById(`messages-${encodedRoomName}`);
    if (!messagesDiv) {
        console.error(`❌ Messages container for topic '${topicName}' not found.`);
        return;
    }

    const messageElement = document.createElement('div');
    // Customize styling if sender === window.username
    messageElement.className = (sender === window.username) ? 'topic-message sender' : 'topic-message receiver';

    messageElement.innerHTML = `
        <div class="message-meta">
            <span class="message-sender">${sender}</span>
            <span class="message-timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="message-text">${message}</div>
    `;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Make global if your HTML calls them via onclick:
window.openTopicChat = openTopicChat;
window.sendTopicMessage = sendTopicMessage;
