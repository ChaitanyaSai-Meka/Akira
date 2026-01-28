import os
import logging
import json
from groq import Groq, APIError
from typing import Optional
from .tavily_search import TavilySearch

logger = logging.getLogger(__name__)


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
                    "content": "You are Akira, a voice assistant. Answer in 1-2 short sentences. Avoid filler, repetition, and disclaimers. When you need current information or facts you don't know, use the tavily_search tool."
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
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "tavily_search":
                        search_query = function_args.get("query")
                        logger.info(f"Performing Tavily search for: {search_query}")
                        search_results = self.tavily.search(search_query)
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": search_results or "No results found"
                        })
                
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
