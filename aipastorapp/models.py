from django.db import models
from django.contrib.auth.models import User

# 1. 신앙 프로필 테이블
class FaithProfile(models.Model):
    profile_id = models.AutoField(primary_key=True, null=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id')
    faith_stage = models.CharField(max_length=20, default='초신자') 
    interests = models.TextField(null=True, blank=True)
    favorite_verse = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'faith_profiles'

# 2. 설교 이력 테이블
class Sermon(models.Model):
    sermon_id = models.AutoField(primary_key=True, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    topic = models.CharField(max_length=100, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sermons'

# 3. 기도문 이력 테이블
class Prayer(models.Model):
    prayer_id = models.AutoField(primary_key=True, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    situation = models.CharField(max_length=100, null=True)
    prayer_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prayers'

# 4. 상담 세션 테이블
class ChatSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, default="새로운 상담", blank=True)

    class Meta:
        db_table = 'chat_sessions'
        
    def __str__(self):
        return f"[{self.session_id}] {self.user.username} - {self.title}"

# 5. 상담 메시지 테이블
class ChatMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=[('USER', 'User'), ('AI', 'AI')])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:20]}"

# 6. 활동 로그 테이블
class ActivityLog(models.Model):
    log_id = models.AutoField(primary_key=True, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    activity_type = models.CharField(max_length=20)
    duration_minutes = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'

# ==========================================
# 7. ★ (새로 추가) 성경 구절 데이터베이스
# ==========================================
class BibleVerse(models.Model):
    book = models.CharField(max_length=20)   # 예: 시편, 마태복음
    chapter = models.IntegerField()          # 장
    verse = models.IntegerField()            # 절
    content = models.TextField()             # 내용 (말씀)

    class Meta:
        db_table = 'bible_verses'
        # 검색 속도를 위해 인덱스 설정
        indexes = [
            models.Index(fields=['content']), 
        ]

    def __str__(self):
        return f"{self.book} {self.chapter}:{self.verse}"