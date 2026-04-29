from django.contrib import admin
from django.urls import path, include
from django.http import FileResponse
from pathlib import Path

# Путь к index.html
FRONTEND = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'index.html'

def index(request):
    return FileResponse(open(FRONTEND, 'rb')) 
    
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('', index)
]