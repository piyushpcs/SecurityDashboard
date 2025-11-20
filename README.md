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
**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
