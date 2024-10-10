#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::{Builder, generate_handler};
use std::sync::{Arc, Mutex};

mod db;
mod api;

// App state to manage shared data (like connected users)
struct AppState {
    online_users: Mutex<Vec<String>>, // To store online users' names
}

fn main() {
    // Initialize the SQLite database
    let conn = db::initialize_db().expect("Failed to initialize the database");
    println!("Database initialized!");

    // Shared application state (e.g., online users)
    let app_state = Arc::new(AppState {
        online_users: Mutex::new(Vec::new()),
    });

    // Initialize Tauri with the command handlers
    Builder::default()
        .manage(app_state)
        .invoke_handler(generate_handler![
            api::send_message,
            api::register_user,
            api::login_user,
            api::get_online_users
        ])
        .run(tauri::generate_context!())
        .expect("Error while running Tauri application");
}
