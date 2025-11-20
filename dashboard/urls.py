from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard page
    path('', views.index, name='index'), 
    
    # Video feed stream
    path('video_feed/', views.video_feed, name='video_feed'),
    
    # Path for setting the status
    path('set_status/<str:new_status>/', views.set_status, name='set_status'),
    
    # Path for deleting a face
    path('delete_face/<str:filename>/', views.delete_face, name='delete_face'),
    
    # --- NEW PATH ---
    # Path for fetching the latest events
    path('get_latest_events/', views.get_latest_events, name='get_latest_events'),
]