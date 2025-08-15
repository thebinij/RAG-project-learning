"""
Chat Engine - Handles the RAG pipeline and response generation
"""

import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from openai import OpenAI

from app.core.cost_tracker import CostBreakdown, CostTracker
from app.utils.token_counter import TokenCounter


class ChatEngine:
    def __init__(self, vector_engine):
        self.vector_engine = vector_engine

        # Initialize OpenAI client using environment variables directly
        # No .env file needed - uses system environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = OpenAI(api_key=api_key, base_url=api_base)

        print(f"[ChatEngine] Using API endpoint: {api_base}")

        # Initialize cost tracking and token counting
        self.cost_tracker = CostTracker()
        self.token_counter = TokenCounter()
        
        # Current model configuration
        self.model = "deepseek/deepseek-chat"
        self.provider = "deepseek"

        # System prompt for the assistant
        self.system_prompt = """You are the LegendaryCorp AI Assistant, a helpful and knowledgeable assistant that answers questions about LegendaryCorp's company information, policies, products, and technical specifications.

Your knowledge base includes:
- Company overview, mission, vision, and core values
- Employment details, compensation, and benefits
- Employee handbook and onboarding procedures
- Product catalog (LegendaryAI Core, Studio, SDK, CLI)
- Technical specifications and API documentation
- Remote work guidelines and company policies

When answering questions:
1. Be accurate and cite specific information from the provided context
2. If the information isn't in the context, say so clearly
3. Be friendly and professional
4. Format responses clearly with bullet points or numbered lists when appropriate
5. Keep responses concise but comprehensive

Context from relevant documents will be provided with each query."""

    def get_response(self, user_query: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Main RAG pipeline with cost tracking:
        1. Retrieve relevant documents
        2. Augment the prompt with context
        3. Generate response
        4. Track costs and usage
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Step 1: Retrieval
        relevant_docs = self.vector_engine.search(user_query, limit=5)

        # Deduplicate sources by title
        unique_docs = []
        seen_titles = set()
        for doc in relevant_docs:
            title = doc["metadata"].get("title", "Document")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_docs.append(doc)

        # Step 2: Augmentation - Create context from retrieved documents
        context = self._create_context(unique_docs)
        augmented_prompt = self._create_augmented_prompt(user_query, context)

        # Step 3: Generation with cost tracking
        try:
            # Count input tokens before API call
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": augmented_prompt},
            ]
            input_tokens = self.token_counter.count_message_tokens(messages, self.model)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            answer = response.choices[0].message.content
            output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
            total_tokens = response.usage.total_tokens if hasattr(response, 'usage') else (input_tokens + output_tokens)

            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(unique_docs)

            # Track costs
            self._track_request_cost(
                request_id, input_tokens, output_tokens, total_tokens,
                user_query, answer, start_time, user_id, session_id
            )

            return {
                "answer": answer, 
                "sources": unique_docs, 
                "confidence": confidence,
                "cost_info": {
                    "request_id": request_id,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost": self._get_estimated_cost(input_tokens, output_tokens)
                }
            }

        except Exception as e:
            # Fallback response if LLM fails
            processing_time = time.time() - start_time
            
            # Track failed request (with estimated tokens)
            estimated_tokens = self.token_counter.count_tokens(user_query, self.model)
            self._track_request_cost(
                request_id, estimated_tokens, 0, estimated_tokens,
                user_query, "FAILED", start_time, user_id, session_id
            )
            
            return {
                "answer": self._create_fallback_response(user_query, unique_docs),
                "sources": unique_docs,
                "confidence": 0.5,
                "error": str(e),
                "cost_info": {
                    "request_id": request_id,
                    "input_tokens": estimated_tokens,
                    "output_tokens": 0,
                    "total_tokens": estimated_tokens,
                    "estimated_cost": self._get_estimated_cost(estimated_tokens, 0)
                }
            }

    def _create_context(self, documents: List[Dict[str, Any]]) -> str:
        """Create context string from retrieved documents"""
        if not documents:
            return "No relevant documents found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Document {i}] {doc['metadata']['title']}")
            context_parts.append(f"Category: {doc['metadata']['category']}")
            context_parts.append(f"Content: {doc['text']}")
            context_parts.append("")  # Empty line for separation

        return "\n".join(context_parts)

    def _create_augmented_prompt(self, query: str, context: str) -> str:
        """Create the augmented prompt with query and context"""
        return f"""Based on the following context from LegendaryCorp documents, please answer the user's question.

CONTEXT:
{context}

USER QUESTION:
{query}

Please provide a helpful and accurate answer based on the context provided. If the information needed to answer the question is not in the context, please state that clearly."""

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieval quality"""
        if not documents:
            return 0.0

        # Average of top 3 document scores
        scores = [doc["score"] for doc in documents[:3]]
        return sum(scores) / len(scores)

    def _create_fallback_response(
        self, query: str, documents: List[Dict[str, Any]]
    ) -> str:
        """Create a fallback response when LLM is unavailable"""
        if not documents:
            return "I couldn't find any relevant information about your question in the LegendaryCorp knowledge base."

        # Improved fallback response with better formatting
        response = (
            "Based on the LegendaryCorp documents, here's the relevant information:\n\n"
        )

        # Get the most relevant document
        top_doc = documents[0]
        response += f"**{top_doc['metadata']['title']}**\n\n"

        # Show more content from the top document
        text = top_doc["text"]
        # Try to show complete sentences
        if len(text) > 400:
            text = text[:400]
            last_period = text.rfind(".")
            if last_period > 200:
                text = text[: last_period + 1]
        response += text + "\n\n"

        # Add other relevant sources if available
        if len(documents) > 1:
            response += "**Related information:**\n"
            for doc in documents[1:3]:
                response += f"• {doc['metadata']['title']}: {doc['text'][:100]}...\n"

        return response

    def _track_request_cost(self, request_id: str, input_tokens: int, output_tokens: int, 
                           total_tokens: int, user_query: str, answer: str, 
                           start_time: float, user_id: str = None, session_id: str = None):
        """Track the cost of a request"""
        try:
            processing_time = time.time() - start_time
            
            # Calculate costs
            costs = self._get_estimated_cost(input_tokens, output_tokens)
            
            # Create cost breakdown
            cost_breakdown = CostBreakdown(
                request_id=request_id,
                timestamp=datetime.now(),
                model=self.model,
                provider=self.provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=costs["input_cost"],
                output_cost=costs["output_cost"],
                total_cost=costs["total_cost"],
                user_query=user_query[:500],  # Truncate long queries
                response_length=len(answer),
                processing_time=processing_time,
                user_id=user_id,
                session_id=session_id,
                tags=["rag", "chat"]
            )
            
            # Track the cost
            self.cost_tracker.track_request(cost_breakdown)
            
        except Exception as e:
            print(f"Error tracking cost: {e}")
    
    def _get_estimated_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Get estimated cost for token usage"""
        try:
            return self.token_counter.estimate_cost(
                input_tokens, output_tokens, self.model, self.provider
            )
        except Exception as e:
            print(f"Error calculating cost: {e}")
            return {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get cost summary for the last N days"""
        return self.cost_tracker.get_cost_summary(days)
    
    def get_model_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get cost breakdown by model"""
        return self.cost_tracker.get_model_breakdown(days)
    
    def export_cost_data(self, format: str = "json", days: int = 30) -> str:
        """Export cost data in various formats"""
        return self.cost_tracker.export_cost_data(format, days)
    
    def get_cost_alerts(self, threshold: float = 10.0) -> List[Dict[str, Any]]:
        """Get cost alerts for high-spending periods"""
        return self.cost_tracker.get_cost_alerts(threshold)
