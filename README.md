# 🛡️ Intelligent Security Dashboard

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

A sophisticated, AI-powered intruder detection system that transforms any camera into a smart security device. It uses **Computer Vision** to detect faces, identify authorized personnel, and send real-time alerts (SMS, Email, Audio) for unauthorized intruders, all managed via a reactive web dashboard.

![Dashboard Screenshot](https://via.placeholder.com/800x400?text=Security+Dashboard+Screenshot+Here)
*(Replace this link with a real screenshot of your dashboard!)*

## ✨ Key Features

### 🧠 AI & Computer Vision
* **Real-Time Face Recognition:** Uses `face_recognition` (dlib) to distinguish between "Known" (authorized) and "Unknown" people with 99.38% accuracy.
* **Live Video Streaming:** Low-latency MJPEG streaming via Django directly to the browser.
* **Multi-Threaded Architecture:** Dedicates separate threads for video capture, image processing, and alert dispatching to ensure **zero lag** in the video feed.

### 🚨 Smart Alerts
* **Instant SMS:** Integration with **Twilio** to send immediate intruder warnings.
* **Email Snapshots:** Sends an email via **SMTP (Gmail)** with a high-res attachment of the intruder's face.
* **Audio Deterrent:** Plays a loud warning sound (`alert.wav`) locally when a threat is confirmed.

### 💻 Interactive Web Dashboard
* **System Controls:** "Arm" and "Disarm" the system instantly with one click (AJAX).
* **Live Event Log:** Auto-updating log of all security events (Intrusion, System Status, Face Management).
* **Face Management:** Upload and delete authorized personnel directly from the UI without restarting the server.

---

## 🛠️ Tech Stack

* **Backend:** Django 4.2 (Python)
* **Computer Vision:** OpenCV, Face_Recognition, NumPy
* **Database:** SQLite (Lightweight & Zero-conf)
* **Frontend:** HTML5, CSS3, JavaScript (Fetch API/AJAX)
* **DevOps:** Docker & Docker Compose
* **APIs:** Twilio (SMS), Gmail SMTP (Email)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.9+**
* **Git**
* **Webcam** (Built-in or USB)
* *(Optional)* **Docker** (for containerized deployment)

---

## 🚀 Installation Guide (Local)

Follow these steps to run the project on your local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/piyushpcs/SecurityDashboard.git](https://github.com/piyushpcs/SecurityDashboard.git)
cd SecurityDashboard
```
### 2. Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies.

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
Note for Windows Users: If dlib fails to install, you must install Visual Studio C++ Build Tools first.

### 4. Configure Environment Variables
Rename the example file:
```bash
mv .env.example .env
```
(Or manually rename it in your file explorer)

Open .env and fill in your credentials:

Ini, TOML

#### Example .env configuration
```ini
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```
### 5. Initialize Database
```Bash

python manage.py migrate
```
6. Run the Server
```Bash

python manage.py runserver
```
Open your browser and visit: http://127.0.0.1:8000

🐳 Running with Docker
This project includes a fully configured Docker setup. This is the easiest way to deploy the application on any system (Raspberry Pi, Linux Server, etc.).

1. Build and Run:

```Bash

docker-compose up --build
```
2. Access: The application will be available at http://localhost:8000.

(Note: On macOS, Docker may not be able to access the built-in webcam directly. Docker deployment is best used with IP Cameras or on Linux hosts).
**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
### 📂 Project Structure
``` 
SecurityDashboard/
├── dashboard/              # Main Django App
│   ├── static/             # CSS & JS files
│   ├── templates/          # HTML files
│   ├── camera.py           # Core Computer Vision Logic (Multi-threaded)
│   ├── views.py            # Backend Logic & AJAX Endpoints
│   └── ...
├── security_project/       # Project Settings
├── known_faces/            # Directory for authorized personnel images
├── intruders/              # Directory for captured intruder images
├── security.db             # SQLite Database
├── Dockerfile              # Docker Image Configuration
├── docker-compose.yml      # Docker Services Configuration
├── manage.py               # Django CLI
└── requirements.txt        # Python Dependencies
```
## 🔧 Troubleshooting

**1. `dlib` installation fails:**
* **Mac:** Run `brew install cmake` before pip installing.
* **Windows:** Install Visual Studio Build Tools with "Desktop C++" support.

**2. Video lag:**
* The system uses a multi-threaded architecture. If lag persists, try lowering the `FACE_REC_FRAME_SKIP` value in `.env` (higher number = smoother video, slower detection).

**3. Email alerts not sending:**
* Ensure you are using a **Gmail App Password**, not your regular login password.
* Check if 2-Factor Authentication is enabled on your Google Account.

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Made with ❤️ by Piyush
</p>
