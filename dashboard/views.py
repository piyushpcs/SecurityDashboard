from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from .camera import VideoCamera
import sqlite3
from django.utils import timezone
import os

# --- Database Helper Functions (No changes) ---
def get_db():
    conn = sqlite3.connect('security.db', timeout=1.0)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_status():
    status = "UNKNOWN"
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT value FROM system_state WHERE key = 'status'")
        row = c.fetchone()
        conn.close()
        if row:
            status = row['value']
    except Exception as e:
        print(f"Error getting system status: {e}")
    return status

def log_event_from_web(event_type, details=None):
    try:
        conn = get_db()
        c = conn.cursor()
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            INSERT INTO events (timestamp, event_type, details)
            VALUES (?, ?, ?)
        ''', (timestamp, event_type, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging web event: {e}")

# --- File Upload Helper (MODIFIED) ---
def handle_uploaded_file(uploaded_file, person_name):
    """
    Saves the uploaded file and returns the saved filename.
    Raises an error if something goes wrong.
    """
    FACES_DIR = 'known_faces'
    if not os.path.exists(FACES_DIR):
        os.makedirs(FACES_DIR)
    
    # Sanitize the name to prevent path issues
    safe_name = "".join(c for c in person_name if c.isalnum() or c in (' ', '_')).rstrip()
    if not safe_name:
        raise ValueError("Invalid person name.")
        
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in ['.jpg', '.jpeg', '.png']:
        raise ValueError("Invalid file type. Only .jpg, .jpeg, .png are allowed.")

    filename = f"{safe_name}{extension}"
    filepath = os.path.join(FACES_DIR, filename)
    
    try:
        with open(filepath, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        print(f"Saved new face: {filename}")
        return filename  # Return the actual filename saved
    except Exception as e:
        print(f"Error saving file: {e}")
        raise e # Re-raise the exception to be caught by the view

# --- Views ---

def index(request):
    """
    Renders the main dashboard page (GET)
    and handles face uploads (POST) via AJAX.
    """
    
    # --- MODIFIED: Handle the file upload with JSON ---
    if request.method == 'POST':
        if 'face_image' in request.FILES and 'person_name' in request.POST:
            person_name = request.POST['person_name']
            uploaded_file = request.FILES['face_image']
            
            if person_name and uploaded_file:
                try:
                    filename = handle_uploaded_file(uploaded_file, person_name)
                    log_event_from_web("FACE_ADDED", f"Authorized person '{filename}' was added.")
                    # Send back a success response
                    return JsonResponse({'status': 'SUCCESS', 'filename': filename})
                except Exception as e:
                    return JsonResponse({'status': 'ERROR', 'message': str(e)}, status=400)
            else:
                return JsonResponse({'status': 'ERROR', 'message': 'Name and file are required.'}, status=400)
        
        # If it's a POST but not a file upload, it's an error
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid POST request'}, status=400)

    # --- This is the original GET request logic ---
    # (It runs when the page is first loaded)
    current_status = get_current_status()
    events = []
    known_faces_list = []
    try:
        conn = get_db()
        c_events = conn.cursor()
        c_events.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 20")
        events = [dict(row) for row in c_events.fetchall()] # Convert to dicts
        conn.close()
    except Exception as e:
        print(f"Error fetching events: {e}")

    FACES_DIR = 'known_faces'
    if os.path.exists(FACES_DIR):
        known_faces_list = [f for f in os.listdir(FACES_DIR) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

    context = {
        'current_status': current_status,
        'events': events, # Pass initial events
        'known_faces_list': known_faces_list,
    }
    return render(request, 'dashboard/index.html', context)

# --- NEW VIEW ---
def get_latest_events(request):
    """
    A new view that just returns the latest events as JSON.
    This is what the page will "poll" every few seconds.
    """
    events = []
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 20")
        # Convert sqlite3.Row objects to plain dictionaries
        events = [dict(row) for row in c.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error fetching events for JSON: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'SUCCESS', 'events': events})


# --- Other views (video_feed, set_status, delete_face) are unchanged ---

def video_feed(request):
    try:
        camera = VideoCamera()
        return StreamingHttpResponse(
            camera.stream_frames(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    except IOError as e:
        print(f"Error starting camera: {e}")
        return render(request, 'dashboard/index.html', {'error': 'Camera not found.'})

def set_status(request, new_status):
    new_status = new_status.upper()
    if new_status in ["ARMED", "DISARMED"]:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE system_state SET value = ? WHERE key = 'status'", (new_status,))
            conn.commit()
            conn.close()
            log_event_from_web(f"SYSTEM_{new_status}", f"System {new_status.lower()} from web dashboard.")
            return JsonResponse({'status': new_status})
        except Exception as e:
            print(f"Error setting status: {e}")
            return JsonResponse({'status': 'ERROR', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'ERROR', 'message': 'Invalid status'}, status=400)

def delete_face(request, filename):
    FACES_DIR = 'known_faces'
    filepath = os.path.join(FACES_DIR, filename)
    if not os.path.normpath(filepath).startswith(os.path.normpath(FACES_DIR)):
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid filename'}, status=400)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted face: {filename}")
            log_event_from_web("FACE_DELETED", f"Authorized person '{filename}' was removed.")
            return JsonResponse({'status': 'SUCCESS', 'filename': filename})
        else:
            return JsonResponse({'status': 'ERROR', 'message': 'File not found'}, status=404)
    except Exception as e:
        print(f"Error deleting face {filename}: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)}, status=500)