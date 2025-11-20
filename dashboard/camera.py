import cv2
import face_recognition
import os
import time
import numpy as np
from twilio.rest import Client
from dotenv import load_dotenv
from collections import deque
import sqlite3
from django.utils import timezone
import simpleaudio as sa  # Use simpleaudio
import threading  # We need the full threading library
import sys
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- Configuration and Setup (No changes) ---
try:
    if load_dotenv():
        print("Loaded environment variables from .env file.")
    else:
        print("Warning: .env file not found.")
except Exception as e:
    print(f"Error loading .env file: {e}")

# (All your .env variables like TWILIO_ACCOUNT_SID, IP_CAMERA_URL, etc.)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
ADMIN_PHONE_NUMBER = os.getenv('ADMIN_PHONE_NUMBER')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
IP_CAMERA_URL = os.getenv('IP_CAMERA_URL', '0')
MIN_CONTOUR_AREA = int(os.getenv('MIN_CONTOUR_AREA', 500))
FACE_REC_FRAME_SKIP = int(os.getenv('FACE_REC_FRAME_SKIP', 5))
DETECTION_THRESHOLD_FRAMES = int(os.getenv('DETECTION_THRESHOLD_FRAMES', 15))
PATIENCE_SECONDS = int(os.getenv('PATIENCE_SECONDS', 7))
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("Twilio client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Twilio client: {e}")
else:
    print("Warning: Twilio credentials not fully set. SMS alerts will be disabled.")
last_sms_alert_time = 0
last_beep_alert_time = 0
SMS_ALERT_COOLDOWN = 300
BEEP_ALERT_COOLDOWN = 10


# --- All Helper Functions (No changes) ---

def load_known_faces(faces_dir="known_faces"):
    # (This function is unchanged)
    known_face_encodings = []
    known_face_names = []
    print(f"Loading known faces from {faces_dir}...")
    if not os.path.isdir(faces_dir):
        print(f"Error: Directory '{faces_dir}' not found.")
        return known_face_encodings, known_face_names
    for filename in os.listdir(faces_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                path = os.path.join(faces_dir, filename)
                name = os.path.splitext(filename)[0]
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)
                    print(f"Loaded face for: {name}")
                else:
                    print(f"Warning: No faces found in {filename}.")
            except Exception as e:
                print(f"Error loading face from {filename}: {e}")
    if not known_face_names:
        print("Warning: No known faces loaded.")
    else:
        print(f"Loaded {len(known_face_names)} known faces.")
    return known_face_encodings, known_face_names

def play_beep_alert():
    # (This function is unchanged, using simpleaudio)
    global last_beep_alert_time
    current_time = time.time()
    alert_file_path = 'alert.wav'
    if (current_time - last_beep_alert_time) > BEEP_ALERT_COOLDOWN:
        print("Playing beep alert...")
        try:
            if os.path.exists(alert_file_path):
                wave_obj = sa.WaveObject.from_wave_file(alert_file_path)
                play_obj = wave_obj.play()
                last_beep_alert_time = current_time
            else:
                print(f"Error: Alert sound file not found at {alert_file_path}")
                last_beep_alert_time = current_time
        except Exception as e:
            print(f"Error playing sound: {e}")
    else:
        print("Beep alert is in cooldown.")

def send_intruder_alert(name):
    # (This function is unchanged)
    global last_sms_alert_time
    current_time = time.time()
    if (current_time - last_sms_alert_time) > SMS_ALERT_COOLDOWN:
        if not twilio_client or not ADMIN_PHONE_NUMBER:
            print("SMS alert not sent (Twilio not configured or no admin number).")
            return
        print(f"Sending Twilio alert for {name}...")
        try:
            message_body = f"ALERT: {name} detected at your location!"
            message = twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=ADMIN_PHONE_NUMBER
            )
            print(f"Intruder alert SMS sent successfully! SID: {message.sid}")
            last_sms_alert_time = current_time
        except Exception as e:
            print(f"Error sending Twilio SMS: \n{e}")
    else:
        print("SMS alert is in cooldown.")

def send_intruder_email_with_attachment(image_path):
    # (This function is unchanged)
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD or not ADMIN_EMAIL:
        print("Email credentials not set. Email alert will be disabled.")
        return
    print(f"Preparing to send email alert with image: {image_path}")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = "INTRUDER ALERT! - Unauthorized Person Detected"
        body = "An unauthorized person was detected by your security system. An image is attached."
        msg.attach(MIMEText(body, 'plain'))
        with open(image_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype="jpg")
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
            msg.attach(attachment)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_HOST_USER, ADMIN_EMAIL, msg.as_string())
            print("Email alert sent successfully!")
    except Exception as e:
        print(f"An error occurred sending email: {e}")

def init_db():
    # (This function is unchanged)
    try:
        conn = sqlite3.connect('security.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                image_path TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        c.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES ('status', 'ARMED')")
        conn.commit()
        conn.close()
        print("Database 'security.db' initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def log_event(event_type, details=None, image_path=None):
    # (This function is unchanged)
    try:
        conn = sqlite3.connect('security.db')
        c = conn.cursor()
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            INSERT INTO events (timestamp, event_type, details, image_path)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, event_type, details, image_path))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging event to database: {e}")

def get_system_status():
    # (This function is unchanged)
    status = "ARMED" 
    try:
        conn = sqlite3.connect('security.db', timeout=1.0) 
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT value FROM system_state WHERE key = 'status'")
        row = c.fetchone()
        conn.close()
        if row:
            status = row['value']
    except Exception as e:
        print(f"Error getting system status: {e}")
    return status

def run_all_alerts(name, image_path):
    # (This function is unchanged)
    print("ALERT THREAD: Starting all alerts...")
    try:
        play_beep_alert()
        send_intruder_alert(name)
        if image_path:
            send_intruder_email_with_attachment(image_path)
        print("ALERT THREAD: All alerts sent.")
    except Exception as e:
        print(f"ALERT THREAD: Error: {e}")


# ---
# --- NEW MULTI-THREADED VideoCamera CLASS ---
# ---

class VideoCamera:
    def __init__(self):
        print("Initializing VideoCamera (Multi-Threaded)...")
        
        # --- Basic Setup ---
        self.known_face_encodings, self.known_face_names = load_known_faces()
        init_db()
        log_event("SYSTEM_STARTUP", "Security system started.")

        # --- Video Source ---
        video_source = IP_CAMERA_URL
        if IP_CAMERA_URL == '0': video_source = 0
        elif IP_CAMERA_URL == '-1': video_source = -1
        
        self.video = cv2.VideoCapture(video_source)
        if not self.video.isOpened():
            print("Warning: Could not open primary video source. Trying fallback...")
            self.video = cv2.VideoCapture(1 if video_source == 0 else 0)
            if not self.video.isOpened():
                raise IOError("Cannot open video stream or webcam.")
        
        print("Successfully connected to video stream.")
        
        # --- Detection Variables ---
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        self.intruder_deque = deque([False] * DETECTION_THRESHOLD_FRAMES, maxlen=DETECTION_THRESHOLD_FRAMES)
        self.intruder_status = False
        self.intruder_last_seen_time = None
        self.frame_count = 0

        # --- Threading-Specific Variables ---
        
        # The latest raw frame from the camera
        (self.grabbed, self.frame) = self.video.read()
        
        # The latest *processed* data (boxes, names, etc.)
        self.last_known_face_locations = []
        self.last_known_face_names = []
        self.motion_contours = []
        self.current_status_text = "ARMED"
        self.patience_text = ""
        
        # A lock to prevent race conditions
        self.lock = threading.Lock()
        
        # A signal to tell threads to stop
        self.stop_event = threading.Event()

        # --- Start the Background Threads ---
        
        # 1. Thread for grabbing frames from camera
        self.grab_thread = threading.Thread(target=self._grab_frames, daemon=True)
        self.grab_thread.start()
        
        # 2. Thread for processing frames (heavy lifting)
        self.process_thread = threading.Thread(target=self._process_frames, daemon=True)
        self.process_thread.start()

        print("VideoCamera initialized successfully.")

    def __del__(self):
        print("Stopping VideoCamera threads...")
        self.stop_event.set()  # Signal threads to stop
        if self.video.isOpened():
            self.video.release()
        print("VideoCamera released.")

    def _grab_frames(self):
        """This function runs in a background thread."""
        print("GRAB THREAD: Started...")
        while not self.stop_event.is_set():
            ret, frame = self.video.read()
            if not ret:
                print("GRAB THREAD: Frame not received. Reconnecting...")
                self.video.release()
                time.sleep(2)
                # Re-initialize
                video_source = IP_CAMERA_URL
                if IP_CAMERA_URL == '0': video_source = 0
                elif IP_CAMERA_URL == '-1': video_source = -1
                self.video = cv2.VideoCapture(video_source)
                if not self.video.isOpened():
                    print("GRAB THREAD: Could not reconnect. Exiting.")
                    break
                continue
            
            # Use a lock to safely update the shared frame
            with self.lock:
                self.grabbed = ret
                self.frame = frame
        print("GRAB THREAD: Stopped.")

    def _process_frames(self):
        """This function runs in a background thread."""
        print("PROCESS THREAD: Started...")
        while not self.stop_event.is_set():
            try:
                # Get the latest frame
                with self.lock:
                    if not self.grabbed or self.frame is None:
                        continue # Wait for a frame
                    frame = self.frame.copy()
                
                # --- This is all your logic from the old loop ---
                
                current_status = get_system_status()
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                
                self.frame_count += 1
                motion_detected_this_frame = False
                current_frame_has_intruder = False

                fg_mask = self.bg_subtractor.apply(small_frame)
                _, thresh_mask = cv2.threshold(fg_mask, 244, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(thresh_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                local_motion_contours = []
                for contour in contours:
                    if cv2.contourArea(contour) > MIN_CONTOUR_AREA:
                        motion_detected_this_frame = True
                        local_motion_contours.append(contour)
                
                local_face_locations = []
                local_face_names = []
                
                if motion_detected_this_frame:
                    if self.frame_count % FACE_REC_FRAME_SKIP == 0:
                        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                        local_face_locations = face_recognition.face_locations(rgb_small_frame)
                        face_encodings = face_recognition.face_encodings(rgb_small_frame, local_face_locations)

                        for face_encoding in face_encodings:
                            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.45)
                            name = "Unknown"
                            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                            if len(face_distances) > 0:
                                best_match_index = np.argmin(face_distances)
                                if matches[best_match_index]:
                                    name = self.known_face_names[best_match_index]
                            
                            local_face_names.append(name)
                            if name == "Unknown":
                                current_frame_has_intruder = True
                    else:
                        # On skipped frames, use the last known results
                        local_face_locations = self.last_known_face_locations
                        local_face_names = self.last_known_face_names
                        if "Unknown" in local_face_names:
                            current_frame_has_intruder = True
                
                self.intruder_deque.appendleft(current_frame_has_intruder)
                    
                if sum(self.intruder_deque) == DETECTION_THRESHOLD_FRAMES and not self.intruder_status and current_status == "ARMED":
                    self.intruder_status = True
                    print("--- INTRUDER CONFIRMED (SYSTEM ARMED) ---")
                    
                    full_image_path = None
                    try:
                        now_dt = timezone.now()
                        filename = f"intruder_{now_dt.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                        if not os.path.exists("intruders"):
                            os.makedirs("intruders")
                        full_image_path = os.path.join("intruders", filename)
                        cv2.imwrite(full_image_path, frame) # Save the full original frame
                        print(f"Saved intruder image: {filename}")
                    except Exception as e:
                        print(f"Error saving intruder image: {e}")

                    # --- Start alerts in a non-blocking thread ---
                    threading.Thread(
                        target=run_all_alerts,
                        args=("Unknown person", full_image_path)
                    ).start()
                    log_event("INTRUDER_DETECTED", "Unknown person confirmed.", full_image_path)

                elif current_status == "DISARMED":
                    if self.intruder_status:
                        print("--- System is DISARMED. Resetting alert status. ---")
                        self.intruder_status = False
                        self.intruder_last_seen_time = None
                        self.intruder_deque.clear()
                        self.intruder_deque.extend([False] * DETECTION_THRESHOLD_FRAMES)
                
                if self.intruder_status and not current_frame_has_intruder:
                    if self.intruder_last_seen_time is None:
                        self.intruder_last_seen_time = time.time()
                    if (time.time() - self.intruder_last_seen_time) >= PATIENCE_SECONDS:
                        print("--- Intruder has left. Resetting status. ---")
                        log_event("SYSTEM_RESET", "Intruder no longer seen.")
                        self.intruder_status = False
                        self.intruder_last_seen_time = None
                        self.intruder_deque.clear()
                        self.intruder_deque.extend([False] * DETECTION_THRESHOLD_FRAMES)
                
                if self.intruder_status and current_frame_has_intruder:
                    self.intruder_last_seen_time = None

                # --- Update Status Text ---
                local_status_text = f"Status: {current_status}"
                local_patience_text = ""
                if current_status == "DISARMED":
                    pass # Handled
                if self.intruder_status:
                    local_status_text = "Status: INTRUDER ALERT!"
                if self.intruder_last_seen_time is not None:
                    patience_left = max(0, PATIENCE_SECONDS - (time.time() - self.intruder_last_seen_time))
                    local_patience_text = f"Resetting in: {patience_left:.1f}s"
                
                # --- Safely update the shared "drawing" variables ---
                with self.lock:
                    self.last_known_face_locations = local_face_locations
                    self.last_known_face_names = local_face_names
                    self.motion_contours = local_motion_contours
                    self.current_status_text = local_status_text
                    self.patience_text = local_patience_text

            except Exception as e:
                print(f"PROCESS THREAD: Error: {e}")
                time.sleep(1) # Don't spam errors
        
        print("PROCESS THREAD: Stopped.")

    def stream_frames(self):
        """
        This is the generator function that Django streams.
        It's now very fast and lightweight.
        """
        while not self.stop_event.is_set():
            with self.lock:
                if not self.grabbed or self.frame is None:
                    continue
                # Make a copy to draw on
                frame = self.frame.copy()
            
            # --- Draw the *last known* results ---
            # This is super fast, no "thinking"
            
            # 1. Draw motion
            for contour in self.motion_contours:
                contour_scaled = contour * 4
                cv2.drawContours(frame, [contour_scaled], -1, (0, 255, 255), 1)

            # 2. Draw faces
            for (top, right, bottom, left), name in zip(self.last_known_face_locations, self.last_known_face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                color = (0, 0, 255) if name == "Unknown" else (0, 255, 0)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 1)

            # 3. Draw status text
            status_color = (0, 255, 0) # Green
            if "DISARMED" in self.current_status_text:
                status_color = (255, 200, 0) # Blue
            if "INTRUDER" in self.current_status_text:
                status_color = (0, 0, 255) # Red
            
            cv2.putText(frame, self.current_status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2, cv2.LINE_AA)
            cv2.putText(frame, self.patience_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

            # --- Encode and Yield the Frame ---
            ret, jpeg_bytes = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame.")
                continue

            frame_data = jpeg_bytes.tobytes()
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n'
                b'Content-Length: ' + f"{len(frame_data)}".encode() + b'\r\n'
                b'\r\n' + frame_data + b'\r\n'
            )