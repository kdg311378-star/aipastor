# aipastorapp/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 1. 메인 (접속 시 강제 로그아웃 & 로그인 창)
    path('', views.force_logout_login, name='home'),

    # 2. 메인 페이지
    path('main/', views.main_page, name='main_page'),
    
    # 3. 로그인/로그아웃/회원가입
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # 4. 기능 페이지들
    path('chat/', views.chat_page, name='chat_page'),
    path('chat-api/', views.chat_api, name='chat_api'),
    path('history/', views.chat_history, name='chat_history'),
    path('bible/', views.bible_search, name='bible_search'),

    # 5. [NEW] 삭제 기능 URL 추가
    # ▼ [기존 삭제 기능들]
    path('history/delete/<int:session_id>/', views.delete_chat_session, name='delete_chat_session'),
    path('history/delete-all/', views.delete_all_chat_history, name='delete_all_chat_history'),

    # ▼ [NEW] 선택 삭제 기능 추가
    path('history/delete-selected/', views.delete_selected_chat_history, name='delete_selected_chat_history'),

    # 기존 화면 URL들 밑에 API URL 추가
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/delete_last_message/', views.delete_last_message, name='delete_last_message'),
]

