// frontend/static/js/modules/notifications.js
/*
export function initializeNotifications() {
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

// Mark Notification as Read
export function markNotificationAsRead(notificationId) {
    fetch('/api/mark-notification-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: notificationId }),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ Notification marked as read.');
        } else {
            console.error('❌ Failed to mark notification as read:', data.message);
        }
    })
    .catch(error => console.error('❌ Error marking notification as read:', error));
} */
