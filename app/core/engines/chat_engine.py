"""
Chat Engine - Handles the RAG pipeline and response generation
"""

import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

from app.core.cost_tracker import CostBreakdown, CostTracker
from app.utils.token_counter import TokenCounter

load_dotenv()

class ChatEngine:
    def __init__(self, vector_engine):
        self.vector_engine = vector_engine

        # Initialize OpenAI client using environment variables directly
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
        self.model = "gpt-3.5-turbo-0125" 
        self.provider = "openai"
        # Dynamic system prompt that adapts to available knowledge
        self.system_prompt = """You are the LegendaryCorp AI Assistant, a helpful and knowledgeable assistant that answers questions based on the provided context from LegendaryCorp's knowledge base.

        Your knowledge base includes various categories of documents that will be provided in context. When answering questions:

        1. **Be accurate and cite specific information** from the provided context
        2. **If information isn't in the context**, say so clearly and suggest what might be available
        3. **Be friendly and professional** in your responses
        4. **Format responses clearly** with bullet points or numbered lists when appropriate
        5. **Keep responses concise but comprehensive**
        6. **Reference specific documents** when possible to build trust

        Context from relevant documents will be provided with each query. Use this context to provide accurate, helpful answers."""

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

            print(f"[ChatEngine] 🔍 Making API call to OpenAI")
            print(f"[ChatEngine] Model: {self.model}")
            print(f"[ChatEngine] API Base: {self.client.base_url}")
            print(f"[ChatEngine] Input tokens: {input_tokens}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            print(f"[ChatEngine] ✅ API Response received successfully!")
            print(f"[ChatEngine] Response type: {type(response)}")
            print(f"[ChatEngine] Response usage: {response.usage}")
            if hasattr(response.usage, '__dict__'):
                print(f"[ChatEngine] Usage attributes: {response.usage.__dict__}")

            answer = response.choices[0].message.content
            
            print(f"[ChatEngine] ✅ Generated response:")
            print(f"[ChatEngine] Response content: {answer[:200]}...")
            print(f"[ChatEngine] Response length: {len(answer)} characters")
            
            # Handle different response usage formats
            if hasattr(response, 'usage') and response.usage:
                # OpenAI API response format
                output_tokens = getattr(response.usage, 'completion_tokens', 0) or getattr(response.usage, 'output_tokens', 0)
                total_tokens = getattr(response.usage, 'total_tokens', 0) or (input_tokens + output_tokens)
            else:
                output_tokens = 0
                total_tokens = input_tokens

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
            
            print(f"[ChatEngine] ❌ API call failed!")
            print(f"[ChatEngine] Error type: {type(e).__name__}")
            print(f"[ChatEngine] Error message: {str(e)}")
            
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
        """Create intelligent context string from retrieved documents"""
        if not documents:
            return "No relevant documents found."

        context_parts = []
        context_parts.append("=== RELEVANT KNOWLEDGE BASE DOCUMENTS ===\n")
        
        for i, doc in enumerate(documents, 1):
            # Enhanced document header
            title = doc['metadata'].get('title', 'Untitled Document')
            category = doc['metadata'].get('category', 'Unknown Category')
            file_name = doc['metadata'].get('file', 'Unknown File')
            
            context_parts.append(f"📄 DOCUMENT {i}: {title}")
            context_parts.append(f"📁 Category: {category}")
            context_parts.append(f"📂 File: {file_name}")
            context_parts.append(f"🎯 Relevance Score: {(doc['score'] * 100):.1f}%")
            context_parts.append("─" * 50)
            
            # Smart content truncation based on category
            content = doc['text']
            if category.lower() == 'research':
                # For research papers, show more content
                if len(content) > 800:
                    content = content[:800] + "... [truncated for brevity]"
            else:
                # For other documents, standard truncation
                if len(content) > 500:
                    content = content[:500] + "... [truncated for brevity]"
            
            context_parts.append(f"📝 Content:\n{content}")
            context_parts.append("")  # Empty line for separation

        context_parts.append("=== END OF CONTEXT ===")
        return "\n".join(context_parts)

    def _create_augmented_prompt(self, query: str, context: str) -> str:
        """Create intelligent augmented prompt with query and context"""
        return f"""Based on the following context from LegendaryCorp's knowledge base, please answer the user's question.

        {context}

        USER QUESTION: {query}

        INSTRUCTIONS:
        1. **Answer based on the provided context** - use specific information from the documents
        2. **Cite sources** - mention which documents you're referencing
        3. **Be comprehensive** - provide detailed answers when the context supports it
        4. **If information is missing** - clearly state what's not available and suggest what might be found in other categories
        5. **Format appropriately** - use bullet points only for lists, not for every line
        6. **Be helpful** - even if the exact answer isn't in context, try to provide related information
        7. **Do not mention document names or include sources sections**

        Please provide a helpful and accurate answer based on the context provided."""

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
        """Create an intelligent fallback response when LLM is unavailable"""
        if not documents:
            return "I couldn't find any relevant information about your question in the LegendaryCorp knowledge base. Please try rephrasing your question or check if the information might be in a different category."

        # Enhanced fallback response with better formatting and category awareness
        response = "Based on the LegendaryCorp knowledge base, here's the relevant information:\n\n"

        # Get the most relevant document
        top_doc = documents[0]
        category = top_doc['metadata'].get('category', 'Unknown')
        title = top_doc['metadata'].get('title', 'Untitled Document')
        
        response += f"📄 **{title}** (Category: {category})\n\n"

        # Smart content display based on category
        text = top_doc["text"]
        if category.lower() == 'research':
            # For research papers, show more content and preserve structure
            if len(text) > 600:
                text = text[:600]
                last_period = text.rfind(".")
                if last_period > 300:
                    text = text[: last_period + 1]
            response += f"📝 **Abstract/Content:**\n{text}\n\n"
        else:
            # For other documents, standard truncation
            if len(text) > 400:
                text = text[:400]
                last_period = text.rfind(".")
                if last_period > 200:
                    text = text[: last_period + 1]
            response += f"📝 **Content:**\n{text}\n\n"

        # Add other relevant sources with category information
        if len(documents) > 1:
            response += "🔍 **Related Information:**\n"
            for doc in documents[1:3]:
                doc_category = doc['metadata'].get('category', 'Unknown')
                doc_title = doc['metadata'].get('title', 'Untitled')
                response += f"• **{doc_title}** ({doc_category}): {doc['text'][:120]}...\n"

        response += "\n💡 **Note**: This is a fallback response. For more detailed answers, please try again when the AI service is available."
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
