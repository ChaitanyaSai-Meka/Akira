import os
import logging
import json
import hashlib
from groq import Groq, APIError
from typing import Optional
from .tavily_search import TavilySearch

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 500


class LLMProcessor:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_LLM_API_KEY"))
        self.model = "llama-3.1-8b-instant"
        self.tavily = TavilySearch()
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": "Search the internet for current information, news, facts, or data that you don't have in your training data. Use this when the user asks about recent events, current information, real-time data, or anything you're unsure about.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def process(self, text: str) -> Optional[str]:
        if not text or not text.strip():
            return None

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are Akira, a high-performance voice assistant. "
                        "CORE INSTRUCTIONS:\n"
                        "1. **Conciseness:** Answer in 1-2 short sentences maximum. "
                        "2. **Voice Optimized:** Do NOT use markdown (*, #), lists, or emojis. Plain text only. "
                        "3. **Tool Usage:** If the user asks about current events, news, weather, or specific facts (e.g., 'who won the game', 'stock price'), "
                        "you MUST call the `tavily_search` tool. Do not guess. "
                        "4. **Directness:** Remove filler words like 'Sure', 'I can help', or 'According to my search'. Just give the answer."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=100,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    
                    if function_name == "tavily_search":
                        try:
                            if isinstance(tool_call.function.arguments, dict):
                                function_args = tool_call.function.arguments
                            else:
                                function_args = json.loads(tool_call.function.arguments)
                            
                            search_query = function_args.get("query")
                            
                            if not search_query or not isinstance(search_query, str):
                                logger.warning("Tool call validation failed: missing or invalid query")
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": "Invalid search query"
                                })
                                continue
                            
                            if len(search_query) > MAX_QUERY_LENGTH:
                                logger.warning(f"Tool call validation failed: query exceeds max length ({len(search_query)} > {MAX_QUERY_LENGTH})")
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": "Search query too long"
                                })
                                continue
                            
                            query_hash = hashlib.sha256(search_query.encode()).hexdigest()[:8]
                            logger.info(f"Tavily search invoked (query_length={len(search_query)}, query_hash={query_hash})")
                            
                            search_results = self.tavily.search(search_query)
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": search_results or "No results found"
                            })
                            
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.error(f"Tool call parsing error: {type(e).__name__}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": "Error parsing search request"
                            })
                            continue
                
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=100,
                )
                
                final_content = final_response.choices[0].message.content
                return final_content if final_content.strip() else None
            else:
                response_content = response_message.content
                return response_content if response_content.strip() else None

        except APIError as e:
            logger.error(f"Groq API error for model {self.model}: {e}", exc_info=True)
            return None
