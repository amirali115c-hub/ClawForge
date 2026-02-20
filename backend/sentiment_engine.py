"""
Leo 2.0 - Sentiment Analysis Engine
====================================
Analyzes user emotions from text input.
"""

import re
from typing import Dict, List, Tuple
from enum import Enum


class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    HAPPY = "happy"
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    SAD = "sad"
    EXCITED = "excited"
    CONFUSED = "confused"


class SentimentAnalyzer:
    """Analyzes sentiment and emotions from text."""
    
    # Sentiment keywords (expandable)
    POSITIVE_WORDS = {
        'good', 'great', 'awesome', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'loved', 'like', 'liked', 'perfect', 'best', 'better', 'nice', 'cool',
        'happy', 'glad', 'pleased', 'satisfied', 'helpful', 'thanks', 'thank', 'appreciate',
        'brilliant', 'superb', 'outstanding', 'incredible', 'marvelous', 'terrific'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'worse', 'hate', 'hated',
        'dislike', 'disappointed', 'frustrating', 'frustrated', 'angry', 'annoyed',
        'annoying', 'useless', 'broken', 'stupid', 'dumb', 'idiot', 'fool', 'waste',
        'problem', 'issue', 'bug', 'error', 'fail', 'failed', 'sucks', 'suck', 'pathetic',
        'unacceptable', 'disgusting', 'horrendous', 'dreadful', 'miserable'
    }
    
    EMOTION_WORDS = {
        # Happy
        'happy': Sentiment.HAPPY, 'glad': Sentiment.HAPPY, 'joy': Sentiment.HAPPY,
        'excited': Sentiment.EXCITED, 'thrilled': Sentiment.EXCITED, 'pumped': Sentiment.EXCITED,
        # Angry
        'angry': Sentiment.ANGRY, 'furious': Sentiment.ANGRY, 'mad': Sentiment.ANGRY,
        'irritated': Sentiment.ANGRY, 'annoyed': Sentiment.ANGRY,
        # Frustrated
        'frustrated': Sentiment.FRUSTRATED, 'fed up': Sentiment.FRUSTRATED,
        'sick of': Sentiment.FRUSTRATED, 'done': Sentiment.FRUSTRATED,
        # Sad
        'sad': Sentiment.SAD, 'upset': Sentiment.SAD, 'depressed': Sentiment.SAD,
        'disappointed': Sentiment.SAD, 'hurt': Sentiment.SAD,
        # Confused
        'confused': Sentiment.CONFUSED, 'puzzled': Sentiment.CONFUSED, 'lost': Sentiment.CONFUSED,
        'don\'t understand': Sentiment.CONFUSED, 'what do you mean': Sentiment.CONFUSED,
    }
    
    # Intensity modifiers
    INTENSIFIERS = {'very', 'really', 'extremely', 'absolutely', 'totally', 'completely', 'highly'}
    NEGATORS = {'not', 'no', 'never', 'neither', 'nobody', 'nothing', 'nowhere', 'don\'t', 'doesn\'t', 'didn\'t', 'won\'t', 'wouldn\'t', 'can\'t', 'couldn\'t'}
    
    def __init__(self):
        self.analysis_count = 0
    
    def analyze(self, text: str) -> Dict:
        """Analyze sentiment of given text."""
        self.analysis_count += 1
        
        # Preprocess
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Calculate scores
        positive_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        
        # Check for emotions
        detected_emotions = []
        for emotion_word, emotion_type in self.EMOTION_WORDS.items():
            if emotion_word in text_lower:
                detected_emotions.append(emotion_type.value)
        
        # Determine primary sentiment
        if positive_count > negative_count + 1:
            sentiment = Sentiment.POSITIVE.value
            confidence = min(0.95, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count + 1:
            sentiment = Sentiment.NEGATIVE.value
            confidence = min(0.95, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = Sentiment.NEUTRAL.value
            confidence = 0.6
        
        # Override with specific emotion if detected
        if detected_emotions:
            # Prioritize stronger emotions
            priority_emotions = [Sentiment.ANGRY.value, Sentiment.FRUSTRATED.value, 
                              Sentiment.SAD.value, Sentiment.EXCITED.value, Sentiment.HAPPY.value]
            for emotion in priority_emotions:
                if emotion in detected_emotions:
                    sentiment = emotion
                    confidence = min(0.95, confidence + 0.15)
                    break
        
        # Calculate intensity (all caps, exclamation marks)
        intensity = 0.5
        if text.isupper() and len(text) > 5:
            intensity = min(1.0, intensity + 0.2)
        intensity += text.count('!') * 0.1
        intensity = min(1.0, intensity)
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'intensity': round(intensity, 2),
            'emotions': list(set(detected_emotions)),
            'scores': {
                'positive': positive_count,
                'negative': negative_count
            },
            'is_toxic': negative_count >= 3 and confidence > 0.7,
            'needs_attention': sentiment in [Sentiment.ANGRY.value, Sentiment.FRUSTRATED.value]
        }
    
    def get_response_tone(self, sentiment_data: Dict) -> str:
        """Get appropriate response tone based on sentiment."""
        sentiment = sentiment_data.get('sentiment', 'neutral')
        
        tone_map = {
            'happy': 'warm and enthusiastic',
            'excited': 'energetic and encouraging',
            'positive': 'friendly and helpful',
            'neutral': 'professional and clear',
            'confused': 'patient and clarifying',
            'sad': 'empathetic and supportive',
            'frustrated': 'apologetic and solution-focused',
            'angry': 'calm, apologetic, and immediate'
        }
        
        return tone_map.get(sentiment, 'professional')


# Singleton instance
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


# Convenience functions
def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of text."""
    return get_sentiment_analyzer().analyze(text)


def get_response_tone(text: str) -> str:
    """Get appropriate tone for response."""
    sentiment_data = analyze_sentiment(text)
    return get_sentiment_analyzer().get_response_tone(sentiment_data)
