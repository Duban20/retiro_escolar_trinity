from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
# IMAGENES
from django.conf import settings 
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Pagina principal
    path('', include('retiros.urls')),
]

# ESTO PERMITE VER LAS FOTOS EN MODO DESARROLLO:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
