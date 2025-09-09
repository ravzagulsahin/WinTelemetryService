# =========================
# Geliştirilmiş Soru Türü Tespit Sistemi
# =========================

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple

class QuestionType(Enum):
    SHORT_ANSWER = "short_answer"      # Kısa cevap gerektiren sorular
    STYLISH = "stylish"               # Şık/detaylı açıklama gerektiren
    LAB_SKELETON = "lab_skeleton"     # Lab iskelet tamamlama
    CODE_COMPLETION = "code_completion" # Kod tamamlama
    ESSAY = "essay"                   # Makale/essay türü
    MULTIPLE_CHOICE = "multiple_choice" # Çoktan seçmeli
    CALCULATION = "calculation"       # Matematik/hesaplama
    UNKNOWN = "unknown"

@dataclass
class QuestionClassification:
    type: QuestionType
    confidence: float  # 0-1 arası
    indicators: List[str]  # Tespit edilen ipuçları
    suggested_prompt_style: str

class ImprovedQuestionClassifier:
    def __init__(self):
        # Kısa cevap ipuçları
        self.short_answer_patterns = [
            r'\b(what is|who is|when was|where is|how many|which)\b',
            r'\b(define|explain briefly|in one word|true or false)\b',
            r'\b(yes or no|correct answer|simple answer)\b',
            r'\?.*\?',  # Birden fazla kısa soru
        ]
        
        # Şık/detaylı cevap ipuçları  
        self.stylish_patterns = [
            r'\b(explain in detail|elaborate|discuss|analyze)\b',
            r'\b(compare and contrast|evaluate|critically examine)\b',
            r'\b(provide examples|give reasons|justify your answer)\b',
            r'\b(essay|report|detailed explanation|comprehensive)\b',
        ]
        
        # Lab iskelet ipuçları (mevcut sistemden geliştirilmiş)
        self.lab_patterns = [
            r'class\s+\w+.*\{',
            r'public\s+class|private\s+class',
            r'attributes:\s*$|methods:\s*$',
            r'lab\s+report|lab\s+assignment',
            r'part\s+[1-9].*part\s+[2-9]',
            r'___+|____+',  # Boş doldurma alanları
            r'```[\s\S]*?```',  # Kod blokları
            r'todo\s*:|fixme\s*:|complete\s+this',
        ]
        
        # Çoktan seçmeli ipuçları
        self.multiple_choice_patterns = [
            r'\b[a-d]\)|[a-d]\.|\([a-d]\)',
            r'choose.*correct|select.*best|mark.*right',
            r'which.*following|all.*except|none.*above',
        ]
        
        # Matematik/hesaplama ipuçları
        self.calculation_patterns = [
            r'\d+.*[+\-*/].*\d+',
            r'calculate|compute|solve|find.*value',
            r'equation|formula|derivative|integral',
            r'\$\d+|\d+%|\d+\s*(kg|cm|km|mph)',
        ]

    def classify_question(self, text: str) -> QuestionClassification:
        """Ana sınıflandırma fonksiyonu"""
        text_clean = self._clean_text(text)
        text_lower = text_clean.lower()
        
        # Her kategori için skor hesapla
        scores = {
            QuestionType.SHORT_ANSWER: self._calculate_score(text_lower, self.short_answer_patterns),
            QuestionType.STYLISH: self._calculate_score(text_lower, self.stylish_patterns),
            QuestionType.LAB_SKELETON: self._calculate_lab_score(text_clean),
            QuestionType.MULTIPLE_CHOICE: self._calculate_score(text_lower, self.multiple_choice_patterns),
            QuestionType.CALCULATION: self._calculate_score(text_lower, self.calculation_patterns),
        }
        
        # En yüksek skoru bul
        best_type = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_type]
        
        # Eşik kontrolü
        if best_score < 0.3:
            best_type = QuestionType.UNKNOWN
            best_score = 0.0
            
        # İpuçlarını topla
        indicators = self._get_indicators(text_lower, best_type)
        
        # Prompt önerisi
        prompt_style = self._get_prompt_style(best_type, text_clean)
        
        return QuestionClassification(
            type=best_type,
            confidence=best_score,
            indicators=indicators,
            suggested_prompt_style=prompt_style
        )

    def _clean_text(self, text: str) -> str:
        """Metni temizle (PART işaretlerini çıkar vs.)"""
        # PART işaretlerini çıkar
        text = re.sub(r'<<<PART\s+\d+\s+(START|END)>>>', '', text, flags=re.IGNORECASE)
        return text.strip()

    def _calculate_score(self, text: str, patterns: List[str]) -> float:
        """Pattern'lere göre skor hesapla"""
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
                
        return matches / total_patterns if total_patterns > 0 else 0.0

    def _calculate_lab_score(self, text: str) -> float:
        """Lab iskelet skorunu hesapla (özel mantık)"""
        score = 0.0
        text_lower = text.lower()
        
        # Temel lab ipuçları
        basic_score = self._calculate_score(text_lower, self.lab_patterns)
        score += basic_score * 0.7
        
        # Ek kriterler
        if len(text) > 500:  # Uzun metinler lab olabilir
            score += 0.1
            
        if text.count('{') > 2 or text.count('}') > 2:  # Çok blok var
            score += 0.1
            
        if 'java' in text_lower or 'python' in text_lower or 'class' in text_lower:
            score += 0.1
            
        return min(score, 1.0)

    def _get_indicators(self, text: str, question_type: QuestionType) -> List[str]:
        """Tespit edilen ipuçlarını döndür"""
        indicators = []
        
        if question_type == QuestionType.SHORT_ANSWER:
            for pattern in self.short_answer_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    indicators.append(f"Short answer pattern: {pattern}")
                    
        elif question_type == QuestionType.STYLISH:
            for pattern in self.stylish_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    indicators.append(f"Detailed explanation pattern: {pattern}")
                    
        elif question_type == QuestionType.LAB_SKELETON:
            for pattern in self.lab_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    indicators.append(f"Lab skeleton pattern: {pattern}")
                    
        return indicators[:3]  # En fazla 3 göster

    def _get_prompt_style(self, question_type: QuestionType, text: str) -> str:
        """Soru türüne göre prompt önerisi"""
        
        if question_type == QuestionType.SHORT_ANSWER:
            if len(text) < 50:
                return "ultra_short"  # Tek kelime/cümle
            else:
                return "short"  # Kısa paragraf
                
        elif question_type == QuestionType.STYLISH:
            return "detailed"  # Detaylı açıklama
            
        elif question_type == QuestionType.LAB_SKELETON:
            return "lab_completion"  # Lab tamamlama
            
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            return "multiple_choice"  # Seçenek analizi
            
        elif question_type == QuestionType.CALCULATION:
            return "step_by_step"  # Adım adım çözüm
            
        else:
            return "general"  # Genel yaklaşım


# =========================
# Entegrasyon için yardımcı fonksiyonlar
# =========================

# Global classifier instance
_classifier = ImprovedQuestionClassifier()

def classify_text(text: str) -> QuestionClassification:
    """Kolay kullanım için wrapper"""
    return _classifier.classify_question(text)

def get_appropriate_prompt(text: str) -> str:
    """Metin için uygun prompt'u döndür"""
    classification = classify_text(text)
    
    prompts = {
        "ultra_short": "Answer in maximum 5 words:",
        "short": "Answer briefly in 1-2 sentences:",
        "detailed": "Provide a comprehensive explanation with examples:",
        "lab_completion": "Complete the lab skeleton maintaining the existing structure:",
        # IMPORTANT: For MCQ, force a single-letter output only
        "multiple_choice": (
            "You are answering a multiple-choice question. "
            "Return ONLY the letter of the correct option (A/B/C/D/E). "
            "Output exactly one uppercase letter and nothing else."
        ),
        "step_by_step": "Solve step by step showing all work:",
        "general": "Provide an appropriate response:"
    }
    
    base_prompt = prompts.get(classification.suggested_prompt_style, prompts["general"])
    
    return f"{base_prompt}\n\n{text}"

def should_use_lab_prompt(text: str) -> bool:
    """Lab prompt kullanılıp kullanılmayacağını belirle"""
    classification = classify_text(text)
    return (classification.type == QuestionType.LAB_SKELETON and 
            classification.confidence > 0.5)

# Test fonksiyonu
def test_classifier():
    test_cases = [
        "What is the capital of France?",
        "Explain in detail the process of photosynthesis with examples.",
        "class Student { // TODO: complete this class }",
        "Which of the following is correct? a) Paris b) London c) Berlin d) Madrid",
        "Calculate the area of a circle with radius 5cm."
    ]
    
    for text in test_cases:
        result = classify_text(text)
        print(f"\nText: {text[:50]}...")
        print(f"Type: {result.type.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Prompt Style: {result.suggested_prompt_style}")
        print(f"Indicators: {result.indicators}")

if __name__ == "__main__":
    test_classifier()
