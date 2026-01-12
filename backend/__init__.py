'''
## Back-end Structure

The backend is organized into the following main components:

- **`app.py`**: The entry point for the Flask application.
- **`config.py`**: Configuration settings for the application.
- **`components/`**: Contains modularized backend logic, such as worker management, entry logging, and camera verification.
- **`database/`**: Contains database models and schemas for data validation and serialization.
- **`tests/`**: Unit tests for the backend components.

## Functions
The back-end is responsible for **2** core modules:

### Employee Camera Verification
Verification of employee (worker) entry into the building. Works by implementing a 2 factor authentication by checking the face biometry and the QR code provided to the worker. 
Any violation gets logged, notably:
- Mismatch of face and QR code data
- Multiple QR codes detected
- Multiple persons (faces) detected
- Expired QR code

### Admin Panel
Handles all administration tasks related to the camera verification behind an intuitive web dashboard.
- Creation of entry permits
- Invalidation of entry permits
- Changing details of existing entry permits
- Viewing entry logs, advanced filtering by employee, event type, event code
- Generating PDF/JSON entry log reports


---

## Setup Instructions

### 1. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/Crowfunder/IO-Projekt.git
cd IO-Projekt
```

### 2. Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies:
```bash
# Using venv
python -m venv venv
source venv/Scripts/activate  # On Windows
source venv/bin/activate      # On Linux/Mac
```

### 3. Install Dependencies
Install the required dependencies using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Run the Application
Start the Flask application:
```bash
flask --app backend/app run
```

Alternatively, you can use the VS Code debugger:
1. Open the `launch.json` file in `.vscode/`.
2. Select the configuration **"Flask: Run App"**.
3. Start debugging.

---

## Notes
- Ensure that the database is properly configured in `config.py` before running the application.
- Use the `tests/` folder to run unit tests and verify the functionality of the backend.

```bash
# Run all tests
pytest
```

'''