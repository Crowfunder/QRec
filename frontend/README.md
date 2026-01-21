# Projekt IO - Frontend
This is the client-side application for the factory entry system. It provides a retro-crt security camera interface for entry terminal and a comprehensive, modern administration panel for managing workers and generating reports.

## Pages
- **Entry Terminal:** Real-time webcam feed for effortless worker entry when QR code is provided.
- **Admin Panel:** Comprehensive page for administrator functionalities.
    - **Worker Management:** View the list of workers and edit it.
    - **Add Worker:** Create worker passes and generate unique QR codes for every worker.
    - **Reports:** Filterable entry logs with photo previews and PDF export generation.

# Running the Front-end
First, install dependencies.
```bash
$ npm install
```
Then, run the dev server
```bash
$ npm run dev
```

## Prerequisites
* Node.js (v16+ recommended)
* The Flask Backend must be running (default: port 5000) for API calls to work.

## Tech Stack
* **Core:** React + Vite
* **UI Framework:** Mantine v7 (Core, Dates, Notifications)
* **Icons:** Tabler Icons
* **Hardware Access:** `react-webcam` (Face detection)
* **Utilities:** `print-js` (Pass printing), `react-router-dom` (Routing)

## Configuration
The project uses `vite.config.js` to proxy API requests. By default, it forwards all requests starting with `/api` to `http://127.0.0.1:5000`.