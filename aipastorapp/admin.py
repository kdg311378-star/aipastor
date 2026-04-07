from django.contrib import admin
from .models import FaithProfile, Sermon, Prayer, ChatSession, ChatMessage, ActivityLog

# 1. 신앙 프로필 관리
@admin.register(FaithProfile)
class FaithProfileAdmin(admin.ModelAdmin):
    list_display = ('profile_id', 'user', 'faith_stage', 'favorite_verse')
    list_filter = ('faith_stage',)
    search_fields = ('user__username', 'interests')

# 2. 설교 이력 관리
@admin.register(Sermon)
class SermonAdmin(admin.ModelAdmin):
    list_display = ('sermon_id', 'user', 'topic', 'created_at')
    search_fields = ('topic', 'content')

# 3. 기도문 이력 관리
@admin.register(Prayer)
class PrayerAdmin(admin.ModelAdmin):
    list_display = ('prayer_id', 'user', 'situation', 'created_at')
    search_fields = ('situation', 'prayer_text')

# 4. 상담 세션 관리 (session_id 적용)
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    # id 대신 session_id 사용
    list_display = ('session_id', 'user', 'title', 'created_at')
    search_fields = ('title',)

# 5. 상담 메시지 관리 (message_id 적용)
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    # id 대신 message_id 사용
    list_display = ('message_id', 'session', 'sender', 'created_at')
    list_filter = ('sender',) 
    search_fields = ('message',)

# 6. 활동 로그 관리
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('log_id', 'user', 'activity_type', 'duration_minutes', 'created_at')
    list_filter = ('activity_type',)