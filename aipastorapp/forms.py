# aipastorapp/forms.py (새로 만들기)

from django import forms
from .models import FaithProfile

class FaithProfileForm(forms.ModelForm):
    class Meta:
        model = FaithProfile
        # 입력받을 항목들만 골라줍니다
        fields = ['faith_stage', 'interests', 'favorite_verse']
        
        # 화면에 보일 한국어 이름표
        labels = {
            'faith_stage': '신앙 단계 (예: 초신자, 집사, 권사)',
            'interests': '주요 관심사 (예: 기도, 찬양, 육아)',
            'favorite_verse': '좋아하는 성경 구절',
        }
        # 입력창 모양 꾸미기 (선택사항)
        widgets = {
            'interests': forms.Textarea(attrs={'rows': 3, 'placeholder': '요즘 고민이나 관심사를 적어주세요.'}),
        }