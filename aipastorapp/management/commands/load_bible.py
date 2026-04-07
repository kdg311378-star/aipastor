from django.core.management.base import BaseCommand
from aipastorapp.models import BibleVerse
import requests

class Command(BaseCommand):
    help = '인터넷에서 한글 성경(개역한글) JSON을 다운로드하여 DB에 저장합니다.'

    def handle(self, *args, **kwargs):
        # ✅ 확인된 작동 주소
        url = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/ko_ko.json"
        
        self.stdout.write(self.style.WARNING(f'🌐 성경 데이터를 다운로드 중입니다... (URL: {url})'))
        
        try:
            # 1. 데이터 다운로드
            response = requests.get(url)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR('❌ 다운로드 실패! 인터넷 연결을 확인하세요.'))
                return
            
            bible_data = response.json()
            self.stdout.write(self.style.SUCCESS('✅ 다운로드 완료! DB 입력을 시작합니다...'))

            # 2. 기존 데이터 삭제 (중복 방지)
            if BibleVerse.objects.exists():
                self.stdout.write(self.style.WARNING('🧹 기존 성경 데이터를 비우는 중...'))
                BibleVerse.objects.all().delete()

            # 3. 데이터 입력 시작
            batch_list = []
            total_count = 0

            for book_info in bible_data:
                book_name = book_info['name'] # 예: 창세기
                chapters = book_info['chapters']
                
                for chapter_idx, verses in enumerate(chapters):
                    chapter_num = chapter_idx + 1
                    
                    for verse_idx, content in enumerate(verses):
                        verse_num = verse_idx + 1
                        
                        # DB에 넣을 객체 생성
                        verse_obj = BibleVerse(
                            book=book_name,
                            chapter=chapter_num,
                            verse=verse_num,
                            content=content
                        )
                        batch_list.append(verse_obj)
                        total_count += 1

                        # 1,000개씩 모아서 한 번에 저장 (속도 향상)
                        if len(batch_list) >= 1000:
                            BibleVerse.objects.bulk_create(batch_list)
                            batch_list = []
                            print(f"🚀 {book_name} {chapter_num}장 저장 중... (누적 {total_count}개)")

            # 남은 데이터 떨이 저장
            if batch_list:
                BibleVerse.objects.bulk_create(batch_list)

            self.stdout.write(self.style.SUCCESS(f'🎉 축하합니다! 총 {total_count}개의 성경 구절이 입력되었습니다!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 오류 발생: {str(e)}'))