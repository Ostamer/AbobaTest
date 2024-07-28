import io
import re
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os
from django.conf import settings

# Ensure that necessary resources are downloaded
nltk.download('stopwords')
nltk.download('wordnet')


class AudioUploadView(APIView):
    parser_classes = (JSONParser,)
    keywords = {
        'Электрика': ['электрика', 'электричество', 'проводка', 'розетка', 'щиток', 'кабель', 'свет'],
        'Водоснабжение': ['водоснабжение', 'вода', 'канализация', 'труба', 'сантехника', 'водопровод', 'слив'],
        'Лифт': ['лифт', 'этаж', 'кнопка', 'кабина', 'подъем', 'лифтовая шахта', 'лифтёр']
    }

    def clean_text(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        text = text.lower()
        stop_words = set(stopwords.words('russian'))
        words = [word for word in text.split() if word not in stop_words]
        lemmatizer = WordNetLemmatizer()
        words = [lemmatizer.lemmatize(word) for word in words]
        prohibited_words = {'блять'}
        words = [word for word in words if word not in prohibited_words]
        return ' '.join(words)

    def classify_text(self, text):
        words = text.split()
        scores = {category: 0 for category in self.keywords}

        for word in words:
            for category, keywords in self.keywords.items():
                if word in keywords:
                    scores[category] += 1

        best_category = max(scores, key=scores.get)
        return best_category if scores[best_category] > 0 else 'Неопределенная категория'

    def post(self, request, *args, **kwargs):
        text = request.data.get('text', '')
        if not text:
            return HttpResponse("Нет предоставленного текста", status=400)

        cleaned_text = self.clean_text(text)

        category = self.classify_text(cleaned_text)
        classification_message = f"Данный текст принадлежит следующей инстанции: {category}"

        pdf_output = io.BytesIO()
        doc = SimpleDocTemplate(pdf_output, pagesize=letter)
        font_path = os.path.join(settings.BASE_DIR, 'static', 'DejaVuSans.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))


        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleN.fontName = 'DejaVuSans'
        styleN.fontSize = 12

        story = [
            Paragraph(cleaned_text, styleN),
            Spacer(1, 12),
            Paragraph(classification_message, styleN)
        ]
        doc.build(story)

        pdf_output.seek(0)
        response = HttpResponse(pdf_output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transcription.pdf"'
        return response
