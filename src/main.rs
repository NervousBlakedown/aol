#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::{Builder, generate_handler};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use tokio::net::{TcpListener, TcpStream};
use tokio_tungstenite::{accept_async, tungstenite::protocol::Message};
use futures_util::{StreamExt, SinkExt};

mod api;
mod db;

struct AppState {
    online_users: Mutex<Vec<String>>,
}

async fn handle_socket_connection(peer: TcpStream, tx: mpsc::Sender<String>) {
    let ws_stream = accept_async(peer).await.expect("Failed to accept WebSocket connection.");
    let (mut write, mut read) = ws_stream.split();

    // Handle messages from the client
    while let Some(message) = read.next().await {
        if let Ok(msg) = message {
            match msg {
                Message::Text(txt) => {
                    println!("Received: {}", txt);
                    tx.send(txt).await.unwrap(); // Send the message to the other client
                }
                _ => {}
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let conn = db::initialize_db().expect("Failed to initialize database");
    println!("Database initialized!");

    let app_state = Arc::new(AppState {
        online_users: Mutex::new(Vec::new()),
    });

    // Set up WebSocket server to handle real-time communication
    let listener = TcpListener::bind("127.0.0.1:8080").await.expect("Failed to bind WebSocket listener");
    println!("WebSocket server listening on 127.0.0.1:8080");

    let (tx, mut rx) = mpsc::channel::<String>(100);

    tokio::spawn(async move {
        while let Some(message) = rx.recv().await {
            println!("Broadcasting message: {}", message);
        }
    });

    tokio::spawn(async move {
        while let Ok((peer, _)) = listener.accept().await {
            let tx_clone = tx.clone();
            tokio::spawn(handle_socket_connection(peer, tx_clone));
        }
    });

    Builder::default()
        .manage(app_state)
        .invoke_handler(generate_handler![api::send_message, api::register_user, api::login_user, api::get_online_users])
        .run(tauri::generate_context!())
        .expect("Error while running Tauri application");
}
