from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static  
from django.views.generic import TemplateView
from chatbot import views  # Import the views module from the chatbot app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('MainApp.urls')),
    path('chatbot/', include('chatbot.urls')),  # Resolve the conflicting route
    path('chat/', views.chat_with_gemini, name='chat_with_gemini'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)