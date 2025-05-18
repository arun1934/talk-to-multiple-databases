from typing import List, Dict, Any
import os
import litellm
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import json
import redis

from app.config import REDIS, LLM, CACHE


class SuggestionService:
    def __init__(self):
        # Configure LiteLLM directly instead of using LangChain integration
        litellm.api_key = LLM["api_key"]
        litellm.api_base = LLM["api_base"]

        # Set custom headers if provided
        if LLM["auth_header"]:
            litellm.headers = {"Authorization": LLM["auth_header"]}

        # Store model name and temperature for later use
        self.model = LLM["model"]
        self.temperature = LLM["suggestion_temperature"]

        self.redis_client = redis.Redis.from_url(
            REDIS["url"],
            decode_responses=True
        )
        self.suggestion_cache_ttl = CACHE["llm_cache_ttl"]

    def generate_suggestions(self, query: str, answer: str, history: List[Dict[str, Any]]) -> List[str]:
        """Generate follow-up suggestions based on the current context"""

        # Check cache first if caching is enabled
        if CACHE["enable_llm_cache"]:
            cache_key = f"suggestions:{hash(query + answer)}"
            cached_suggestions = self.redis_client.get(cache_key)
            if cached_suggestions:
                try:
                    return json.loads(cached_suggestions)
                except json.JSONDecodeError:
                    pass

        # Build context from history
        context = self._build_context(history)

        # Create prompt
        prompt_content = f"""You are a Net Promoter Score (NPS) analytics expert that suggests relevant follow-up questions to help users gain more insights from their NPS data.

Based on the current conversation, suggest 3 relevant follow-up questions that would help the user dive deeper into the NPS data.

# NPS Domain Knowledge
Net Promoter Score (NPS) is a customer loyalty metric ranging from -100 to +100:
- Promoters: Customers who rated 9-10 (loyal enthusiasts who will refer others)
- Passives: Customers who rated 7-8 (satisfied but unenthusiastic customers)
- Detractors: Customers who rated 0-6 (unhappy customers who can damage brand)
- NPS Score = (% Promoters - % Detractors) * 100

# NPS Analysis Follow-up Types:
1. Segmentation questions - breaking down NPS by category, region, time period
   Example: "How does the NPS vary across different product categories?"

2. Trend analysis questions - looking at changes in NPS over time
   Example: "What's the month-over-month trend in NPS for the furniture category?"

3. Root cause questions - exploring reasons behind high/low NPS
   Example: "What are the most common themes in the comments from detractors?"

4. Correlational questions - exploring relationships between NPS and other factors
   Example: "Is there a correlation between delivery time and NPS rating?"

5. Demographic analysis - how NPS varies by customer segment
   Example: "How does NPS differ between new customers and repeat customers?"

6. Benchmark questions - comparing NPS against standards
   Example: "How does our NPS compare to the industry average?"

7. Action-oriented questions - exploring potential improvements
   Example: "Which product category has the lowest NPS and needs attention?"

8. Loyalty impact questions - how NPS affects customer behavior
   Example: "Do customers who give higher NPS scores make repeat purchases?"

Make suggestions specific, actionable, and follow the user's current analytical thread.
Each suggestion should be a complete question related to NPS.
Keep each question concise (under 15 words if possible).

Current query: {query}
Answer: {answer}
Recent conversation context: {context}

Generate 3 follow-up NPS-related questions:"""

        # Call LiteLLM directly
        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt_content}],
                temperature=self.temperature
            )

            # Extract text content from response
            response_content = response.choices[0].message.content

            # Parse suggestions
            suggestions = self._parse_suggestions(response_content)

            # Cache the suggestions if caching is enabled
            if CACHE["enable_llm_cache"]:
                self.redis_client.setex(
                    cache_key,
                    self.suggestion_cache_ttl,
                    json.dumps(suggestions)
                )

            return suggestions

        except Exception as e:
            print(f"Error generating suggestions: {str(e)}")
            return []

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

        return suggestions[:3]  # Return maximum 3 suggestions