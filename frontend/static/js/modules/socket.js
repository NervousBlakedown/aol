// frontend/static/js/modules/socket.js
// Handles WebSocket-related logic (real-time message sending and receiving)
import { io } from 'https://cdn.socket.io/4.5.1/socket.io.esm.min.js';
import { appendMessageToChat, createChatBox } from './chat.js';
export let socket = null;
export { createChatBox };

// export const socket = io();


// init socket
export function initializeSocket() {
    if (!socket) {
        socket = io(); 
        console.log('✅ Socket.IO initialized');

        // Set up event listeners after connecting
        socket.on('connect', () => {
            console.log('✅ Socket.IO connected:', socket.id);

            const username = sessionStorage.getItem('username');
            const userId = sessionStorage.getItem('user_id');
            if (username && userId) {
                socket.emit('login', { username, user_id: userId });
                console.log('✅ Logged in with username:', username, 'and user ID', userId);
            } else {
                console.warn('⚠️ Username not found. Ensure it is set in sessionStorage.');
            }
        });

        // Handle private messages
        socket.on('private_message', (data) => {
            console.log('📩 Incoming message:', data);

            const { room, username, message, timestamp, sender_id } = data;
            const currentUserId = sessionStorage.getItem('user_id');

            // avoid duplicate display of own messages
            if (currentUserId === sender_id) {
                console.log('🔄 Ignoring message from self:', message);
                return;
            }

            // Ensure chatbox is opened when receiving a new message
            let chatBox = document.getElementById(`chat-box-${room}`);
            if (!chatBox) {
                console.log(`🔓 Opening chatbox for room: ${room}`);
                createChatBox(room, username);  // Ensure chatbox is created
                chatBox = document.getElementById(`chat-box-${room}`);
            }
            
            // add message
            appendMessageToChat(room, username, message, timestamp);
        });

        // Chat started
        socket.on('chat_started', (data) => {
            console.log('Chat started successfully:', data);
            const { room, users } = data;
            const username = sessionStorage.getItem('username');
            const chatTitle = users.filter(u => u !== username).join(', ');
            createChatBox(room, chatTitle);
        });

        // Typing events
        socket.on('typing', (data) => {
            console.log(`${data.username} is typing...`);
        });

        socket.on('stop_typing', (data) => {
            console.log(`${data.username} stopped typing.`);
        });

        socket.on('disconnect', () => {
            console.warn('⚠️ Socket.IO disconnected');
        });
    } else {
        console.log('⚠️ Socket.IO already initialized.');
    }
}


// Send real-time message before storing in DB
export function sendMessageRealtime(roomName, username, message) {
    const timestamp = new Date().toISOString();
    socket.emit('private_message', { room: roomName, username, message, timestamp });

    // Show message in the chatbox immediately
    appendMessageToChat(roomName, 'You', message, timestamp);
}


// test socket init
export function ensureSocketInitialized() {
    if (!socket || !socket.connected) {
        console.warn('⚠️ Socket.IO is not connected. Initializing...');
        initializeSocket();
    }
}