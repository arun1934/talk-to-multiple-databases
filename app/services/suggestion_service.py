from typing import List, Dict, Any
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import json
import redis

class SuggestionService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7
        )
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True
        )
        self.suggestion_cache_ttl = 300  # 5 minutes
    
    def generate_suggestions(self, query: str, answer: str, history: List[Dict[str, Any]]) -> List[str]:
        """Generate follow-up suggestions based on the current context"""
        
        # Check cache first
        cache_key = f"suggestions:{hash(query + answer)}"
        cached_suggestions = self.redis_client.get(cache_key)
        if cached_suggestions:
            try:
                return json.loads(cached_suggestions)
            except json.JSONDecodeError:
                pass
        
        # Build context from history
        context = self._build_context(history)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a helpful assistant that suggests relevant follow-up questions for a furniture delivery NPS analysis system.
            
Based on the current conversation, suggest 3 relevant follow-up questions that would help the user dive deeper into the data.

Consider:
1. Drilling down into specific regions, products, or time periods
2. Exploring correlations between different factors
3. Identifying trends and patterns
4. Comparing different segments
5. Investigating outliers or interesting findings
6. Make suggestions that are relevant to the current query and answer.
7. Make them concise and clear. 
8. Dont give long strings of text or explanations.

Make suggestions specific and actionable. Each suggestion should be a complete question."""),
            HumanMessage(content=f"""
Current query: {query}
Answer: {answer}
Recent conversation context: {context}

Generate 3 follow-up questions:""")
        ])
        
        # Format the prompt before sending
        formatted_prompt = prompt.format_messages()
        response = self.llm.invoke(formatted_prompt)
        
        # Parse suggestions
        suggestions = self._parse_suggestions(response.content)
        
        # Cache the suggestions
        self.redis_client.setex(
            cache_key,
            self.suggestion_cache_ttl,
            json.dumps(suggestions)
        )
        
        return suggestions
    
    def _build_context(self, history: List[Dict[str, Any]]) -> str:
        """Build context from conversation history"""
        if not history:
            return "No previous conversation"
        
        context_parts = []
        for conv in history[-3:]:  # Last 3 conversations
            context_parts.append(f"Q: {conv['query']}\nA: {conv['answer'][:200]}...")
        
        return "\n\n".join(context_parts)
    
    def _parse_suggestions(self, content: str) -> List[str]:
        """Parse suggestions from LLM response"""
        suggestions = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove numbering and bullets
            if line and any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '-', '*', '•']):
                cleaned_line = line.lstrip('1234567890.-*• ').strip()
                if cleaned_line and '?' in cleaned_line:
                    suggestions.append(cleaned_line)
            elif line and '?' in line:
                suggestions.append(line)
        
        return suggestions[:4]  # Return maximum 4 suggestions
