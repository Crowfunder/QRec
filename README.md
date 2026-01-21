# 🔴QREC - _ˈkurɛk_
A comprehensive access control system for a large industrial facility to enhance security and prevent abuses associated with traditional magnetic access cards.
It integrates QR-code scanning and automated facial recognition to reliably verify employee identity upon entry, logs all access attempts with detailed metadata, and supports management of employee permissions and authorized personnel lists.

## Documentation
[Link to detailed documentation](https://crowfunder.github.io/QRec)

## Deployment
### Front-end
#### Prerequisites

Before running QREC, ensure the following are installed and running:

* **Node.js:** Version 16 or higher.
* **Backend:** The Flask Backend API must be running (Default port: `5000`).

#### Installation

1. Clone the repository to the local machine.
2. Open your terminal in the project directory.
3. Install the required dependencies:
```bash
$ npm install

```
#### Running the Application

To start the development server:

```bash
$ npm run dev

```

* **Note:** The application uses `vite.config.js` to proxy API requests. All requests starting with `/api` are automatically forwarded to `http://127.0.0.1:5000`.

This adress is the place of Entry Terminal, for Admin panel navigate to /admin.

### Back-end

#### 1. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/Crowfunder/IO-Projekt.git
cd IO-Projekt
```

#### 2. Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies:
```bash
# Using venv
python -m venv venv
source venv/Scripts/activate  # On Windows
source venv/bin/activate      # On Linux/Mac
```

#### 3. Install Dependencies
Install the required dependencies using `pip`:
```bash
pip install -r requirements.txt
```

#### 4. Run the Application
Start the Flask application:
```bash
flask --app backend/app run
```

Alternatively, you can use the VS Code debugger:
1. Open the `launch.json` file in `.vscode/`.
2. Select the configuration **"Flask: Run App"**.
3. Start debugging.

---

### Notes
- Ensure that the database is properly configured in `config.py` before running the application.
- Use the `tests/` folder to run unit tests and verify the functionality of the backend.

```bash
# Run all tests with coverage
pytest --cov=.
```
