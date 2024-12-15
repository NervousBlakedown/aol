# aol
you've got mail! (that sound, but for those dreamy AIM vibes from yonder)
# BlakeOL: A Flask + Supabase Chat Application

BlakeOL is a retro-inspired chat application that leverages Flask, Socket.IO, and Supabase for real-time messaging. The interface recalls vintage online messaging, while the underlying technologies enable a robust, scalable modern chat solution.

## Features

- **User Registration & Login:**  
  Users can sign up with an email, username, and password. Passwords are hashed with Argon2.
  
- **Real-Time Messaging:**  
  With Socket.IO, users can have one-on-one or group chats instantly updated for all participants.
  
- **User Status & Typing Indicators:**  
  Track who is online, away, or in "Do Not Disturb" mode. See when someone is typing in a chat.
  
- **Search for Contacts:**  
  Users can search for existing registered users by username or email. Results appear in real-time as they type.
  
- **Add & Manage Contacts:**  
  Add users to a contact list for quick access. Start one-on-one or multi-user chats with selected contacts.
  
- **Close Active Chats:**  
  Each chat window includes a close button, allowing users to remove chats they no longer need.

## Technologies Used

- **Backend:** Flask (Python), Flask-SocketIO for real-time communications
- **Database:** Supabase (PostgreSQL)
- **Frontend:** Vanilla JavaScript, HTML, CSS
- **Password Hashing:** Argon2
- **Environment Management:** Python `dotenv` for loading environment variables
- **Deployment:** Can be deployed locally or on a server. Includes `requirements.txt` for dependencies.


## Getting Started

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/BlakeOL.git
   cd BlakeOL

2. **Set up environment variables:**
Create an .env file at the root of the project. Include:
DATABASE_URL="your_supabase_database_url"
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_key"
GMAIL_ADDRESS="your_gmail_address"
GMAIL_PASSWORD="your_gmail_app_password"

3. **Install Python dependencies:**
cd server
pip install -r requirements.txt

4. **Initialize the Database: If you’re using the provided scripts and schema, run:**
python db/init_db.py
Or run SQL migrations on your Supabase/Postgres DB as needed.

5. **Run the app:**
cd server
python server.py
This will start the Flask server with Socket.IO. By default, it listens on http://0.0.0.0:5000.

6. **Access the Application: Open your browser and go to:**
http://localhost:5000
Sign up for a new account.
Login from the /login page.
Explore the dashboard, add contacts, and start chatting.

**Usage**
Signup: Create a new account at the root /.
Login: Go to /login to sign in.
Dashboard: Once logged in, /dashboard shows contacts, search bar, and active chats.
Start a Chat: Select contacts and click "Start Chat".
Close a Chat: Use the "X" button in the chat header.
Log Out: Click Logout in the sidebar.

**Troubleshooting**
Login Button Not Working:
Ensure no JavaScript errors occur before attaching the login button's event listener. Check app.js for duplicate code blocks or syntax errors.

**Start Chat Not Working:**
Make sure session['user_id'] is set upon login. Confirm that initializeDashboard() is not called multiple times and that event listeners attach correctly.

**Contact Search Not Working:**
Ensure session['user_id'] is set and that /search_contacts returns results. Check network tab in browser DevTools for errors.

**Contributing**
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.  Feel free to email me anytime!

**License**
MIT License. See LICENSE file for details.




