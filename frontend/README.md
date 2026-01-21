# :red_circle:QREC
This is the client-side application for the factory entry system. It provides a retro-crt security camera interface for entry terminal and a comprehensive, modern administration panel for managing workers and generating reports.

# Quickstart Guide
## For Workers: Clocking In

Goal: Enter the factory quickly using your pass.

    Approach Terminal: Go to the entry kiosk with the retro security screen.

    Scan Pass: Hold your QR Code pass steadily in front of the camera.

    Enter: Wait for the screen to confirm your entry before proceeding.

## For Admins: Daily Tasks

Goal: Manage staff and view activity.

To Add a New Employee:

    Open the Admin Panel and select Add Worker.

    Fill in employee details.

    Click Generate QR and then print the new pass.

To Check Who Has Arrived:

    Open the Admin Panel and select Reports.

    View the real-time log to see who scanned in and view their entry photo.

# Pages overview
- **Entry Terminal:** */* Real-time webcam feed for effortless worker entry when QR code is provided.
- **Admin Panel:** */admin* Comprehensive page for administrator functionalities.
    - **Worker Management:** */workers* View the list of workers and edit it.
    - **Add Worker:** */add-worker* Create worker passes and generate unique QR codes for every worker.
    - **Reports:** */reports* Filterable entry logs with photo previews and PDF export generation.

# User manual
Welcome to **QREC**, the factory entry system designed for speed and security. The system consists of two main interfaces:
1. **The Entry Terminal:** A retro-styled security interface for workers to scan in.
2. **The Admin Panel:** A modern dashboard for management to oversee workers and logs.

## Worker Guide
This section is for employees and workers entering the facility.

### How to Enter the Factory
The QREC Entry Terminal uses a webcam-based interface with a "Retro-CRT" aesthetic to process your entry.

1. **Prepare your Pass:** Ensure you have your physical or digital Worker Pass containing your unique **QR Code**.
2. **Approach the Terminal:** Walk up to the designated entry kiosk. You will see a live video feed on the screen.

*Note: The screen is styled to look like an old security monitor. This is intentional.*

3. **Scan your Code:** Hold your QR code up to the camera.
4. **Confirmation:** Once the system recognizes the QR code, it will verify your identity against the database.* If successful, access will be granted instantly.

**Troubleshooting for Workers:**

* **Camera not focusing?** Move your QR code slowly back and forth about 20cm from the camera lens.
* **Lighting:** Ensure you are not blocking the light source with your body; the camera needs to see the code clearly.

## Administrator Guide

This section is for HR, Facility Managers, and Security personnel managing the system.

### Accessing the Admin Panel

The Admin Panel is a modern, comprehensive dashboard built for managing the workforce and viewing security logs.

### 1. Worker Management

This is your central database for current employees.

* **View Workers:** Navigate to the **Worker Management** tab to see a full list of registered employees.
* **Edit Details:** Select a worker from the list to update their information (e.g., name changes, role updates).

### 2. Adding New Workers & Creating Passes

To onboard a new employee:

1. Navigate to the **Add Worker** section.
2. **Input Data:** Fill in the required fields for the new worker.
3. **Generate QR:** Click the button to generate a unique QR code for this specific worker.
4. **Print Pass:** The system utilizes `print-js`. Click the **Print** button to send the new pass (with the QR code) directly to your connected printer.

### 3. Reports & Monitoring

The Reports section allows you to audit who has entered the factory and when.

* **View Logs:** See a chronological list of all entry attempts.
* **Photo Previews:** To ensure security compliance, the system captures a photo at the moment of entry. Click on a log entry to view the photo preview.
* **Filtering:** Use the filter tools to search for specific dates, specific workers, or timeframes.
* **Exporting:** To save a report for offline records or meetings, click **Export PDF**. This will generate a downloadable document of the currently filtered logs.


## Technical Setup (IT Dept Only)

This section is for the IT personnel responsible for installing and maintaining the application.

### Prerequisites

Before running QREC, ensure the following are installed and running:

* **Node.js:** Version 16 or higher.
* **Backend:** The Flask Backend API must be running (Default port: `5000`).

### Installation

1. Clone the repository to the local machine.
2. Open your terminal in the project directory.
3. Install the required dependencies:
```bash
$ npm install

```
### Running the Application

To start the development server:

```bash
$ npm run dev

```

* **Note:** The application uses `vite.config.js` to proxy API requests. All requests starting with `/api` are automatically forwarded to `http://127.0.0.1:5000`.

This adress is the place of Entry Terminal, for Admin panel navigate to /admin.

### Troubleshooting Hardware

* **Webcam Issues:** The application relies on `react-webcam`. Ensure the browser has been granted permission to access the camera device.
* **Printing Issues:** If passes are not printing, check that the browser is not blocking pop-ups, as `print-js` may trigger a print dialog window.

### Tech Stack
* **Core:** React + Vite
* **UI Framework:** Mantine v7 (Core, Dates, Notifications)
* **Icons:** Tabler Icons
* **Hardware Access:** `react-webcam` (Face detection)
* **Utilities:** `print-js` (Pass printing), `react-router-dom` (Routing)