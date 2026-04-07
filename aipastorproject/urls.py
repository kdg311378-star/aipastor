"""
URL configuration for aipastorproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include # include를 꼭 불러와야 합니다!

urlpatterns = [
    path('admin/', admin.site.urls),
    # 빈 문자열('')은 기본 주소(127.0.0.1:8000/)를 의미합니다.
    # 이 주소로 들어오는 모든 요청을 aipastorapp의 urls.py로 보냅니다.
    path('', include('aipastorapp.urls')), 
]