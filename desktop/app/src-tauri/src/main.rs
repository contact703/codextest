// SPDX-FileCopyrightText: 2024 Audiodescricao Toolkit Contributors
// SPDX-License-Identifier: MIT

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use tauri::{command};
use walkdir::WalkDir;

#[derive(Serialize)]
struct AssetEntry {
    name: String,
    path: String,
}

#[command]
fn list_assets(path: String) -> Vec<AssetEntry> {
    let mut entries = Vec::new();
    for entry in WalkDir::new(path).into_iter().flatten() {
        if entry.file_type().is_file() {
            if let Some(name) = entry.file_name().to_str() {
                if let Some(path_str) = entry.path().to_str() {
                    entries.push(AssetEntry {
                        name: name.to_string(),
                        path: path_str.to_string(),
                    });
                }
            }
        }
    }
    entries
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![list_assets])
        .run(tauri::generate_context!())
        .expect("erro ao iniciar aplicativo Tauri");
}
