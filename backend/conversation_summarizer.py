"""
Leo 2.0 - Conversation Summarizer
==================================
Summarizes long conversations into concise summaries.
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


class ConversationSummarizer:
    """Summarizes conversation history."""
    
    def __init__(self):
        self.summary_history: List[Dict] = []
        self.max_history = 100
    
    def summarize(self, messages: List[Dict], max_length: int = 200) -> Dict:
        """Summarize a list of messages."""
        if not messages:
            return {
                'summary': 'No conversation to summarize.',
                'topic': 'None',
                'key_points': [],
                'sentiment': 'neutral',
                'message_count': 0
            }
        
        # Extract key information
        topics = self._extract_topics(messages)
        key_points = self._extract_key_points(messages)
        sentiment = self._analyze_sentiment(messages)
        
        # Generate summary
        summary_parts = []
        
        if len(messages) > 1:
            summary_parts.append(f"Conversation with {len(messages)} messages")
        
        if topics:
            summary_parts.append(f"Main topics: {', '.join(topics[:3])}")
        
        if key_points:
            summary_parts.append(f"Key points: {key_points[0]}")
        
        summary = '. '.join(summary_parts) if summary_parts else "General conversation"
        
        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        result = {
            'summary': summary,
            'topic': topics[0] if topics else 'General',
            'topics': topics,
            'key_points': key_points[:5],
            'sentiment': sentiment,
            'message_count': len(messages),
            'timestamp': datetime.now().isoformat()
        }
        
        self.summary_history.append(result)
        if len(self.summary_history) > self.max_history:
            self.summary_history = self.summary_history[-self.max_history:]
        
        return result
    
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract main topics from messages."""
        # Simple keyword-based topic extraction
        topic_keywords = {
            'coding': ['code', 'python', 'javascript', 'program', 'function', 'bug', 'error'],
            'learning': ['learn', 'study', 'understand', 'explain', 'teach'],
            'search': ['search', 'find', 'lookup', 'google'],
            'files': ['file', 'read', 'write', 'save', 'create'],
            'chat': ['chat', 'talk', 'message', 'conversation'],
            'memory': ['remember', 'forget', 'memory', 'save'],
        }
        
        # Count keyword occurrences
        topic_counts = defaultdict(int)
        
        for msg in messages:
            content = msg.get('content', '').lower()
            content += msg.get('message', '').lower()
            
            for topic, keywords in topic_keywords.items():
                if any(kw in content for kw in keywords):
                    topic_counts[topic] += 1
        
        # Sort by count and return topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics if t[1] > 0]
    
    def _extract_key_points(self, messages: List[Dict]) -> List[str]:
        """Extract key points from messages."""
        key_points = []
        
        for msg in messages:
            content = msg.get('content', '') or msg.get('message', '')
            
            # Look for statements with important keywords
            important_starts = [
                'the ', 'this ', 'i ', 'we ', 'you ', 'it '
            ]
            
            if any(content.lower().startswith(start) for start in important_starts):
                if len(content) > 20 and len(content) < 150:
                    key_points.append(content.strip())
        
        return key_points[:10]
    
    def _analyze_sentiment(self, messages: List[Dict]) -> str:
        """Analyze overall sentiment of conversation."""
        positive_words = {'good', 'great', 'thanks', 'thank', 'happy', 'love', 'nice', 'perfect'}
        negative_words = {'bad', 'wrong', 'error', 'problem', 'issue', 'hate', 'stupid', 'angry'}
        
        pos_count = 0
        neg_count = 0
        
        for msg in messages:
            content = (msg.get('content', '') + ' ' + msg.get('message', '')).lower()
            pos_count += sum(1 for w in positive_words if w in content)
            neg_count += sum(1 for w in negative_words if w in content)
        
        if pos_count > neg_count + 1:
            return 'positive'
        elif neg_count > pos_count + 1:
            return 'negative'
        else:
            return 'neutral'
    
    def get_summary_for_resume(self, messages: List[Dict]) -> str:
        """Get a short summary for resuming conversation."""
        summary = self.summarize(messages, max_length=100)
        
        parts = []
        if summary['topic'] != 'General':
            parts.append(f"Discussed: {summary['topic']}")
        if summary['key_points']:
            parts.append(f"Key: {summary['key_points'][0][:50]}")
        
        return ' | '.join(parts) if parts else "General chat"
    
    def get_history(self) -> List[Dict]:
        """Get summary history."""
        return self.summary_history


# Singleton
_summarizer = None

def get_conversation_summarizer() -> ConversationSummarizer:
    global _summarizer
    if _summarizer is None:
        _summarizer = ConversationSummarizer()
    return _summarizer


# Convenience functions
def summarize_conversation(messages: List[Dict]) -> Dict:
    """Summarize a conversation."""
    return get_conversation_summarizer().summarize(messages)


def get_resume_summary(messages: List[Dict]) -> str:
    """Get summary for resuming conversation."""
    return get_conversation_summarizer().get_summary_for_resume(messages)
