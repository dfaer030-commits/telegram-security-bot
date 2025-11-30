import os
import requests
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FraudAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('HF_API_KEY')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        } if self.api_key else {}
        
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        # Расширенная база знаний с социальной инженерией
        self.fraud_patterns = [
            # Явные финансовые требования
            {"pattern": r"перевед[иьте]\s+деньги", "weight": 0.9, "type": "financial"},
            {"pattern": r"оплат[иьте]\s+(штраф|счет|долг)", "weight": 0.8, "type": "financial"},
            {"pattern": r"на\s+карт[уе]\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}", "weight": 1.0, "type": "financial"},
            
            # Социальная инженерия и авторитет
            {"pattern": r"служб[аы]\s+безопасности", "weight": 0.7, "type": "authority"},
            {"pattern": r"техническ[ая|ой]\s+поддержк", "weight": 0.6, "type": "authority"},
            {"pattern": r"юридическ[ая|ой]\s+компани", "weight": 0.7, "type": "authority"},
            {"pattern": r"представитель\s+\w+", "weight": 0.5, "type": "authority"},
            {"pattern": r"сбой\s+в\s+системе", "weight": 0.6, "type": "technical"},
            {"pattern": r"обновлени[ея]\s+безопасности", "weight": 0.6, "type": "technical"},
            
            # Скрытые угрозы и давление
            {"pattern": r"во\s+избежание\s+последствий", "weight": 0.8, "type": "pressure"},
            {"pattern": r"правов[ы]?\s+последствий", "weight": 0.7, "type": "pressure"},
            {"pattern": r"рекомендуем\s+связаться", "weight": 0.5, "type": "pressure"},
            {"pattern": r"требуется\s+ваша\s+реакция", "weight": 0.6, "type": "urgency"},
            {"pattern": r"в\s+течение\s+\d+\s+час", "weight": 0.7, "type": "urgency"},
            
            # Личные данные и подтверждения
            {"pattern": r"подтверждени[ея]\s+данн", "weight": 0.6, "type": "personal_data"},
            {"pattern": r"верификаци[яи]\s+профил", "weight": 0.6, "type": "personal_data"},
            {"pattern": r"ответьте\s+цифрой", "weight": 0.5, "type": "confirmation"},
            {"pattern": r"оставьте\s+комментарий", "weight": 0.4, "type": "confirmation"},
            
            # Финансовые соблазны
            {"pattern": r"супер\s+выгодную\s+акцию", "weight": 0.7, "type": "reward"},
            {"pattern": r"уникальная\s+возможность", "weight": 0.6, "type": "reward"},
            {"pattern": r"частный\s+инвестор", "weight": 0.5, "type": "investment"},
            {"pattern": r"надежных\s+партнеров", "weight": 0.5, "type": "investment"},
        ]
        
        # Расширенные ключевые слова для контекстного анализа
        self.red_flags = [
            'срочно', 'немедленно', 'переведите', 'оплатите', 'заблокирован',
            'выиграл', 'приз', 'штраф', 'долг', 'банк', 'карт', 'паспорт',
            'разблокировки', 'счет', 'деньги', 'перевод', 'безопасност',
            'подтверждени', 'верификац', 'реквизит', 'данн', 'проверк',
            'акци', 'выгодн', 'возможност', 'инвест', 'партнер'
        ]
        
        # Контекстные триггеры для социальной инженерии
        self.context_triggers = {
            'authority_impersonation': ['служба безопасности', 'техническая поддержка', 'юридическая', 'представитель'],
            'urgency_pressure': ['срочно', 'немедленно', 'в течение', 'скорее', 'последний шанс'],
            'confirmation_tricks': ['ответьте', 'подтвердите', 'ведите код', 'оставьте комментарий'],
            'financial_enticement': ['выгодно', 'акция', 'бонус', 'приз', 'доходность'],
            'technical_pretext': ['сбой', 'обновление', 'проверка', 'верификация']
        }

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Улучшенный анализ с контекстным пониманием
        """
        if not message or len(message.strip()) < 3:
            return self._create_response(False, 0.0, "Сообщение слишком короткое")
        
        # Глубокий контекстный анализ
        context_result = self._contextual_analysis(message)
        
        # AI анализ если доступен
        if self.api_key:
            ai_result = self._analyze_with_ai(message)
            if ai_result:
                return self._combine_results(context_result, ai_result)
        
        return context_result

    def _contextual_analysis(self, message: str) -> Dict[str, Any]:
        """
        Глубокий контекстный анализ социальной инженерии
        """
        text_lower = message.lower()
        total_score = 0.0
        detected_patterns = []
        context_indicators = []
        
        # 1. Базовый анализ паттернов
        for pattern_info in self.fraud_patterns:
            if re.search(pattern_info["pattern"], text_lower, re.IGNORECASE):
                total_score += pattern_info["weight"]
                detected_patterns.append(pattern_info["type"])
        
        # 2. Анализ контекстных триггеров
        for context_type, triggers in self.context_triggers.items():
            for trigger in triggers:
                if trigger in text_lower:
                    total_score += 0.3
                    context_indicators.append(context_type)
                    break  # Не начисляем много раз за один тип
        
        # 3. Анализ структуры сообщения
        structure_score = self._analyze_message_structure(message)
        total_score += structure_score
        
        # 4. Анализ психологического давления
        pressure_score = self._analyze_psychological_pressure(message)
        total_score += pressure_score
        
        # 5. Ключевые слова
        red_flag_count = sum(1 for word in self.red_flags if word in text_lower)
        total_score += red_flag_count * 0.2
        
        # 6. Дополнительные проверки
        if re.search(r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b', text_lower):
            total_score += 0.8
            
        if re.search(r'\d+\s*(рубл|руб|₽|рублей|р\.|₽)', text_lower):
            total_score += 0.4
        
        total_score = min(total_score, 1.0)
        
        reason = self._generate_detailed_reason(detected_patterns, context_indicators, red_flag_count, structure_score, pressure_score)
        
        return self._create_response(
            is_fraud=total_score > 0.3,  # Понижаем порог для сложных случаев
            confidence=total_score,
            reason=reason,
            ai_used=False
        )

    def _analyze_message_structure(self, message: str) -> float:
        """
        Анализ структуры сообщения на признаки мошенничества
        """
        score = 0.0
        
        # Официальное начало без персонализации
        if re.match(r'(Здравствуйте|Уважаем|Добрый день).*!', message):
            score += 0.2
        
        # Много формальных выражений
        formal_phrases = ['в рамках', 'по нашим данным', 'требуется', 'рекомендуем', 'предлагаем']
        if sum(1 for phrase in formal_phrases if phrase in message.lower()) >= 2:
            score += 0.3
        
        # Сочетание официальности и срочности
        if any(word in message.lower() for word in ['срочно', 'немедленно']) and any(word in message.lower() for word in ['требуется', 'рекомендуем']):
            score += 0.4
            
        return score

    def _analyze_psychological_pressure(self, message: str) -> float:
        """
        Анализ психологического давления
        """
        score = 0.0
        text_lower = message.lower()
        
        # Угрозы последствиями
        if any(phrase in text_lower for phrase in ['во избежание', 'последствий', 'правовых']):
            score += 0.4
        
        # Создание искусственной срочности
        if any(phrase in text_lower for phrase in ['в течение часа', 'скорее', 'последний шанс']):
            score += 0.3
            
        # Просьба о простом действии для маскировки
        if any(phrase in text_lower for phrase in ['просто ответьте', 'ведите цифру', 'оставьте комментарий']):
            score += 0.3
            
        return score

    def _generate_detailed_reason(self, patterns: list, contexts: list, red_flags: int, structure: float, pressure: float) -> str:
        """
        Генерирует детальное объяснение
        """
        reasons = []
        
        if patterns:
            reasons.append(f"паттерны: {', '.join(set(patterns))}")
            
        if contexts:
            reasons.append(f"контекст: {', '.join(set(contexts))}")
            
        if red_flags > 0:
            reasons.append(f"ключевые слова: {red_flags}")
            
        if structure > 0.3:
            reasons.append("подозрительная структура")
            
        if pressure > 0.3:
            reasons.append("психологическое давление")
        
        if not reasons:
            return "Контекстный анализ: признаки не обнаружены"
            
        return "Контекстный анализ: " + ", ".join(reasons)

    def _analyze_with_ai(self, message: str) -> Dict[str, Any]:
        """
        AI анализ с улучшенным промптом
        """
        try:
            # Более детальный промпт для сложных случаев
            prompt = f"""
            Analyze this Russian message for sophisticated fraud techniques including social engineering, authority impersonation, and psychological pressure.
            
            Message: "{message}"
            
            Consider:
            - Is someone pretending to be from official organization?
            - Is there artificial urgency created?
            - Are they asking for any confirmation or simple action?
            - Is there hidden financial motive?
            
            Response format: FRAUD: yes/no, CONFIDENCE: 0-100%, REASON: brief explanation
            """
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 400,
                    "temperature": 0.4,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=25
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_ai_response(result, message)
            else:
                logger.warning(f"AI API недоступно: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Ошибка AI анализа: {e}")
            return None

    def _parse_ai_response(self, ai_data: Any, original_message: str) -> Dict[str, Any]:
        """
        Парсит ответ от AI
        """
        try:
            if isinstance(ai_data, list) and len(ai_data) > 0:
                generated_text = ai_data[0].get('generated_text', '')
                
                # Упрощенный анализ ответа AI
                text_lower = generated_text.lower()
                
                if 'fraud: yes' in text_lower or 'мошенничество' in text_lower:
                    confidence = 0.7
                    reason = "AI: обнаружены признаки социальной инженерии"
                else:
                    confidence = 0.3
                    reason = "AI: возможны элементы манипуляции"
                
                return {
                    'is_fraud': confidence > 0.5,
                    'confidence': confidence,
                    'reason': reason,
                    'ai_used': True
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга AI ответа: {e}")
            return None

    def _combine_results(self, contextual: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        """
        Комбинирует результаты контекстного и AI анализа
        """
        combined_confidence = (contextual['confidence'] + ai['confidence']) / 2
        
        return {
            'is_fraud': combined_confidence > 0.4,
            'confidence': combined_confidence,
            'reason': f"{contextual['reason']} | {ai['reason']}",
            'risk_level': self._get_risk_level(combined_confidence),
            'ai_used': True
        }

    def _create_response(self, 
                        is_fraud: bool, 
                        confidence: float, 
                        reason: str, 
                        ai_used: bool = False,
                        risk_level: str = None) -> Dict[str, Any]:
        """
        Создает ответ
        """
        if risk_level is None:
            risk_level = self._get_risk_level(confidence)
            
        return {
            'is_fraud': is_fraud,
            'confidence': confidence,
            'risk_level': risk_level,
            'reason': reason,
            'ai_used': ai_used
        }

    def _get_risk_level(self, score: float) -> str:
        if score > 0.7:
            return "высокий"
        elif score > 0.5:
            return "средний" 
        elif score > 0.3:
            return "низкий"
        else:
            return "минимальный"
