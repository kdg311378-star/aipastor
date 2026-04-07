# aipastorapp/management/commands/update_bible_names.py
from django.core.management.base import BaseCommand
from aipastorapp.models import BibleVerse

class Command(BaseCommand):
    help = 'DB에 영어로 저장된 성경 책 이름을 한글로 일괄 변경합니다.'

    def handle(self, *args, **kwargs):
        # 영어 -> 한글 변환표
        bible_map = {
            'Genesis': '창세기', 'Exodus': '출애굽기', 'Leviticus': '레위기', 'Numbers': '민수기', 'Deuteronomy': '신명기',
            'Joshua': '여호수아', 'Judges': '사사기', 'Ruth': '룻기', '1 Samuel': '사무엘상', '2 Samuel': '사무엘하',
            '1 Kings': '열왕기상', '2 Kings': '열왕기하', '1 Chronicles': '역대상', '2 Chronicles': '역대하',
            'Ezra': '에스라', 'Nehemiah': '느헤미야', 'Esther': '에스더', 'Job': '욥기', 'Psalms': '시편',
            'Proverbs': '잠언', 'Ecclesiastes': '전도서', 'Song of Solomon': '아가', 'Isaiah': '이사야',
            'Jeremiah': '예레미야', 'Lamentations': '예레미야애가', 'Ezekiel': '에스겔', 'Daniel': '다니엘',
            'Hosea': '호세아', 'Joel': '요엘', 'Amos': '아모스', 'Obadiah': '오바댜', 'Jonah': '요나',
            'Micah': '미가', 'Nahum': '나훔', 'Habakkuk': '하박국', 'Zephaniah': '스바냐', 'Haggai': '학개',
            'Zechariah': '스가랴', 'Malachi': '말라기',
            'Matthew': '마태복음', 'Mark': '마가복음', 'Luke': '누가복음', 'John': '요한복음', 'Acts': '사도행전',
            'Romans': '로마서', '1 Corinthians': '고린도전서', '2 Corinthians': '고린도후서', 'Galatians': '갈라디아서',
            'Ephesians': '에베소서', 'Philippians': '빌립보서', 'Colossians': '골로새서',
            '1 Thessalonians': '데살로니가전서', '2 Thessalonians': '데살로니가후서',
            '1 Timothy': '디모데전서', '2 Timothy': '디모데후서', 'Titus': '디도서', 'Philemon': '빌레몬서',
            'Hebrews': '히브리서', 'James': '야고보서', '1 Peter': '베드로전서', '2 Peter': '베드로후서',
            '1 John': '요한일서', '2 John': '요한이서', '3 John': '요한삼서', 'Jude': '유다서', 'Revelation': '요한계시록'
        }

        self.stdout.write(self.style.WARNING('🔄 성경 책 이름을 한글로 변환 중입니다...'))

        total_changed = 0
        for eng, kor in bible_map.items():
            # DB에서 'Genesis'를 찾아서 '창세기'로 한 번에 업데이트 (속도 매우 빠름)
            updated_count = BibleVerse.objects.filter(book=eng).update(book=kor)
            if updated_count > 0:
                self.stdout.write(f"✅ {eng} -> {kor} ({updated_count}구절 변경)")
                total_changed += updated_count

        self.stdout.write(self.style.SUCCESS(f'🎉 총 {total_changed}개의 구절이 한글 책 이름으로 변경되었습니다!'))