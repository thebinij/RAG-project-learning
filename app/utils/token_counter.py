"""
Token Counter - Estimates token counts for different LLM models
Essential for accurate cost calculation
"""

import re
import tiktoken
from typing import Dict, List, Tuple, Optional


class TokenCounter:
    """Counts tokens for different LLM models"""
    
    # Model to encoding mapping
    MODEL_ENCODINGS = {
        "gpt-4": "cl100k_base",
        "gpt-4-turbo": "cl100k_base", 
        "gpt-3.5-turbo": "cl100k_base",
        "deepseek/deepseek-chat": "cl100k_base",
        "deepseek/deepseek-coder": "cl100k_base",
        "claude-3-opus": "cl100k_base",
        "claude-3-sonnet": "cl100k_base", 
        "claude-3-haiku": "cl100k_base",
        "gemini-pro": "cl100k_base",
        "gemini-pro-vision": "cl100k_base"
    }
    
    def __init__(self):
        self.encoders = {}
        self._load_encoders()
    
    def _load_encoders(self):
        """Load encoders for different models"""
        try:
            for model, encoding in self.MODEL_ENCODINGS.items():
                try:
                    self.encoders[model] = tiktoken.get_encoding(encoding)
                except Exception as e:
                    print(f"Warning: Could not load encoder for {model}: {e}")
        except ImportError:
            print("Warning: tiktoken not available, using fallback token counting")
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens for a specific model"""
        try:
            if model in self.encoders:
                return len(self.encoders[model].encode(text))
            else:
                # Fallback to approximate counting
                return self._approximate_token_count(text)
        except Exception as e:
            print(f"Error counting tokens for {model}: {e}")
            return self._approximate_token_count(text)
    
    def count_message_tokens(self, messages: List[Dict[str, str]], model: str = "gpt-4") -> int:
        """Count tokens for a list of messages (system, user, assistant)"""
        try:
            if model in self.encoders:
                encoder = self.encoders[model]
                total_tokens = 0
                
                for message in messages:
                    # Add tokens for the message content
                    content_tokens = len(encoder.encode(message["content"]))
                    total_tokens += content_tokens
                    
                    # Add tokens for the role (typically 4 tokens)
                    role_tokens = len(encoder.encode(message["role"]))
                    total_tokens += role_tokens
                
                # Add tokens for the format (typically 3-4 tokens per message)
                format_tokens = len(messages) * 4
                total_tokens += format_tokens
                
                return total_tokens
            else:
                # Fallback calculation
                return self._approximate_message_tokens(messages)
                
        except Exception as e:
            print(f"Error counting message tokens: {e}")
            return self._approximate_message_tokens(messages)
    
    def _approximate_token_count(self, text: str) -> int:
        """Fallback token counting using word-based approximation"""
        # Rough approximation: 1 token ≈ 0.75 words for English text
        words = len(text.split())
        return int(words * 1.33)
    
    def _approximate_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Fallback message token counting"""
        total_tokens = 0
        
        for message in messages:
            # Count content tokens
            content_tokens = self._approximate_token_count(message["content"])
            total_tokens += content_tokens
            
            # Add role and format tokens (rough estimate)
            total_tokens += 8
        
        return total_tokens
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str, provider: str = "custom") -> Dict[str, float]:
        """Estimate cost based on token counts"""
        from app.core.cost_tracker import CostCalculator
        
        return CostCalculator.calculate_cost(model, input_tokens, output_tokens, provider)
    
    def get_token_usage_breakdown(self, text: str, model: str = "gpt-4") -> Dict[str, any]:
        """Get detailed token usage breakdown"""
        token_count = self.count_tokens(text, model)
        
        # Analyze text characteristics
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.splitlines())
        
        # Calculate ratios
        chars_per_token = char_count / token_count if token_count > 0 else 0
        words_per_token = word_count / token_count if token_count > 0 else 0
        
        return {
            "model": model,
            "tokens": token_count,
            "characters": char_count,
            "words": word_count,
            "lines": line_count,
            "chars_per_token": round(chars_per_token, 2),
            "words_per_token": round(words_per_token, 2),
            "estimated_cost_usd": self._estimate_cost_usd(token_count, model)
        }
    
    def _estimate_cost_usd(self, tokens: int, model: str) -> float:
        """Estimate cost in USD for a given number of tokens"""
        # Rough cost estimates per 1K tokens (update as needed)
        cost_per_1k = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0015,
            "deepseek/deepseek-chat": 0.00014,
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "gemini-pro": 0.0005
        }
        
        cost_per_token = cost_per_1k.get(model, 0.001) / 1000
        return round(tokens * cost_per_token, 6)
    
    def optimize_prompt(self, text: str, target_tokens: int, model: str = "gpt-4") -> str:
        """Optimize prompt to fit within token limit"""
        current_tokens = self.count_tokens(text, model)
        
        if current_tokens <= target_tokens:
            return text
        
        # Simple truncation strategy (you can implement more sophisticated ones)
        words = text.split()
        target_words = int(target_tokens * 0.75)  # Rough conversion
        
        if target_words >= len(words):
            return text
        
        # Truncate to target word count
        truncated_words = words[:target_words]
        truncated_text = " ".join(truncated_words)
        
        # Ensure we don't cut in the middle of a sentence
        last_period = truncated_text.rfind(".")
        if last_period > len(truncated_text) * 0.8:  # If period is in last 20%
            truncated_text = truncated_text[:last_period + 1]
        
        return truncated_text
    
    def get_model_info(self, model: str) -> Dict[str, any]:
        """Get information about a specific model"""
        model_info = {
            "gpt-4": {
                "max_tokens": 8192,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06,
                "provider": "openai"
            },
            "gpt-4-turbo": {
                "max_tokens": 128000,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03,
                "provider": "openai"
            },
            "deepseek/deepseek-chat": {
                "max_tokens": 32768,
                "cost_per_1k_input": 0.00014,
                "cost_per_1k_output": 0.00028,
                "provider": "deepseek"
            },
            "claude-3-opus": {
                "max_tokens": 200000,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075,
                "provider": "anthropic"
            }
        }
        
        return model_info.get(model, {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.001,
            "cost_per_1k_output": 0.002,
            "provider": "unknown"
        })
