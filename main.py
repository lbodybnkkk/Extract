from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.disambig.mle import MLEDisambiguator
import re
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # أو ضع رابط GitHub Pages الخاص بك
    allow_methods=["*"],
    allow_headers=["*"],
)
app = FastAPI()

# تهيئة أدوات التحليل
analyzer = Analyzer.builtin_analyzer()
disambiguator = MLEDisambiguator.pretrained()

class AnalysisRequest(BaseModel):
    text: str
    analysis_types: List[str]
    special_request: Optional[str] = None

class AnalysisResult(BaseModel):
    token: str
    type: str
    details: Optional[str] = None
    additional_details: Optional[List[str]] = None

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    try:
        # تحليل الجملة
        disambig = disambiguator.disambiguate(request.text.split())
        results = []

        for word in disambig:
            analyses = word.analyses[0] if word.analyses else {}
            
            # التحقق من كل نوع مطلوب
            for analysis_type in request.analysis_types:
                if is_match(analysis_type, word.word, analyses):
                    results.append(create_result(analysis_type, word.word, analyses))
            
            # التحقق من الطلب الخاص إذا وجد
            if request.special_request and check_special_request(request.special_request, word.word, analyses):
                results.append(create_result(request.special_request, word.word, analyses))
        
        return {"results": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_result(analysis_type: str, word: str, analysis: dict) -> AnalysisResult:
    """إنشاء كائن نتيجة التحليل"""
    details = get_details(analysis_type, analysis)
    additional_details = get_additional_details(analysis_type, analysis)
    
    return AnalysisResult(
        token=word,
        type=analysis_type,
        details=details,
        additional_details=additional_details
    )

def is_match(analysis_type: str, word: str, analysis: dict) -> bool:
    """تحديد ما إذا كانت الكلمة تطابق النوع النحوي المطلوب"""
    if analysis_type == "اسم الفاعل":
        return analysis.get('pos') == 'NOUN' and 'فاعل' in analysis.get('pattern', '')
    
    elif analysis_type == "صيغ المبالغة":
        return analysis.get('pos') == 'NOUN' and any(
            p in analysis.get('pattern', '') 
            for p in ['فَعَّال', 'مِفْعَال', 'فَعُول', 'فَعِيل']
        )
    
    elif analysis_type == "اسم المفعول":
        return analysis.get('pos') == 'NOUN' and 'مفعول' in analysis.get('pattern', '')
    
    elif analysis_type == "اسم التفضيل":
        return analysis.get('pos') == 'NOUN' and 'أفعل' in analysis.get('pattern', '')
    
    elif analysis_type == "اسم الزمان والمكان":
        return analysis.get('pos') == 'NOUN' and analysis.get('pattern') in ['مَفعَل', 'مَفعِل']
    
    elif analysis_type == "المصدر الميمي":
        return analysis.get('pos') == 'NOUN' and analysis.get('pattern') == 'مَفعَل'
    
    elif analysis_type == "نائب الفاعل":
        return analysis.get('syntax_role') == 'نائب فاعل'
    
    elif analysis_type == "المفعول به":
        return analysis.get('syntax_role') == 'مفعول به'
    
    elif analysis_type == "المفعول المطلق":
        return analysis.get('syntax_role') == 'مفعول مطلق'
    
    elif analysis_type == "المفعول لأجله":
        return analysis.get('syntax_role') == 'مفعول لأجله'
    
    elif analysis_type == "الجملة الأسمية":
        # يمكن تطوير هذا الجزء ليتعرف على الجمل الأسمية
        return False
    
    elif analysis_type == "النواسخ":
        return word in ['كان', 'أصبح', 'أضحى', 'ظل', 'بات', 'صار', 'ليس', 'ما زال', 'ما برح', 'ما فتئ', 'ما انفك']
    
    # يمكن إضافة المزيد من الشروط لكل نوع نحوي
    # ...
    
    return False

def check_special_request(special_request: str, word: str, analysis: dict) -> bool:
    """التحقق من الطلب الخاص"""
    if special_request.lower() == "اسم كان":
        # هذا مثال بسيط، يحتاج لتطوير أكثر دقة
        return analysis.get('pos') == 'NOUN' and analysis.get('syntax_role') == 'مبتدأ'
    
    # يمكن إضافة المزيد من الشروط للطلبات الخاصة
    # ...
    
    return False

def get_details(analysis_type: str, analysis: dict) -> str:
    """الحصول على تفاصيل إضافية للتحليل"""
    if analysis_type == "اسم الفاعل":
        return f"وزن: {analysis.get('pattern', 'غير معروف')}"
    
    elif analysis_type == "اسم المفعول":
        return f"من الفعل: {analysis.get('source_verb', 'غير معروف')}"
    
    elif analysis_type == "اسم التفضيل":
        return f"صيغة التفضيل"
    
    elif analysis_type == "نائب الفاعل":
        return "يحل محل الفاعل عند بناء الفعل للمجهول"
    
    # يمكن إضافة المزيد من التفاصيل لكل نوع
    # ...
    
    return ""

def get_additional_details(analysis_type: str, analysis: dict) -> List[str]:
    """الحصول على تفاصيل إضافية للعرض"""
    details = []
    
    if analysis.get('root'):
        details.append(f"الجذر: {analysis['root']}")
    
    if analysis.get('pattern'):
        details.append(f"الوزن: {analysis['pattern']}")
    
    if analysis.get('pos'):
        details.append(f"نوع الكلمة: {analysis['pos']}")
    
    if analysis.get('lemma'):
        details.append(f"المصدر: {analysis['lemma']}")
    
    return details if details else None
