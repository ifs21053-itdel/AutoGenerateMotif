"""Website URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from Website import views
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import generate_ulos_pdf
from .views import get_progress_view

urlpatterns = [
    # =================== ADMIN & AUTHENTICATION ===================
    path('admin/', admin.site.urls,),
    path('', views.LoginPage, name='login'),
    path('logout/', views.LogoutPage, name='logout'),
    path('register/', views.SignupPage, name='signup'),
    
    # =================== MAIN NAVIGATION ===================
    path('generator', views.image, name="generator"),
    path('home/', views.generator, name="home"),
    path('Monitoring', views.loading, name="Monitoring"),
    
    # =================== MOTIF GENERATION (EXISTING) ===================
    path('external', views.external),
    path('save', views.save),
    path('PostImage', views.PostImage),
    path('post', views.createpost),
    path('tes', views.tes),
    
    # =================== MOTIF LISTING & MANAGEMENT ===================
    path('list', views.show, name="list1"),
    path('list/<str:id>', views.motif, name="list"),
    path('list/Nama/<str:user>', views.tagName, name="tagUser"),
    path('list/JumlahBaris/<str:jmlBaris>', views.tagJmlBaris, name="tagJmlBaris"),
    path('list/waktu/<str:time>', views.tagWaktu, name="tagTime"),
    path('delete/', views.deleteMotif, name="delete"),
    path('update/<int:id>', views.UpdateUser, name='update'),
    path('update/updaterecord/<int:id>', views.updaterecord, name='updaterecord'),
    path('list1', views.showTest),
    path('search', views.Search, name="search"),
    
    # =================== HELP SECTION ===================
    path('help', views.help, name="help"),
    path('help/generator', views.help_generate, name="help-generator"),
    path('help/lidi', views.help_lidi, name="help-lidi"),
    path('help/search', views.help_search, name="help-search"),
    path('help/download', views.help_download, name="help-download"),
    
    # =================== COLORING SYSTEM ===================
    path('pewarnaan/', views.coloring_view, name='pewarnaan'),
    path('get_motifs/', views.get_ulos_motifs, name='get_ulos_motifs'),
    path('pewarnaan/progress/<str:task_id>/', get_progress_view, name='pewarnaan_progress'),
    path('generate-pdf/', generate_ulos_pdf, name='generate_pdf'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)