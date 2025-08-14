"""
Chat Engine - Handles the RAG pipeline and response generation
"""

import os
from typing import List, Dict, Any
from openai import OpenAI

class ChatEngine:
    def __init__(self, vector_engine):
        self.vector_engine = vector_engine
        
        # Initialize OpenAI client using environment variables directly
        # No .env file needed - uses system environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        
        print(f"[ChatEngine] Using API endpoint: {api_base}")
        
        # System prompt for the assistant
        self.system_prompt = """You are the LegendaryCorp AI Assistant, a helpful and knowledgeable assistant that answers questions about LegendaryCorp's policies, products, and company information.

Your knowledge base includes:
- Employee handbook (pet policy, remote work, benefits)
- Product specifications
- Meeting notes and decisions
- Customer FAQs

When answering questions:
1. Be accurate and cite specific information from the provided context
2. If the information isn't in the context, say so clearly
3. Be friendly and professional
4. Format responses clearly with bullet points or numbered lists when appropriate
5. Keep responses concise but comprehensive

Context from relevant documents will be provided with each query."""
    
    def get_response(self, user_query: str) -> Dict[str, Any]:
        """
        Main RAG pipeline:
        1. Retrieve relevant documents
        2. Augment the prompt with context
        3. Generate response
        """
        
        # Step 1: Retrieval
        relevant_docs = self.vector_engine.search(user_query, limit=5)
        
        # Deduplicate sources by title
        unique_docs = []
        seen_titles = set()
        for doc in relevant_docs:
            title = doc['metadata'].get('title', 'Document')
            if title not in seen_titles:
                seen_titles.add(title)
                unique_docs.append(doc)
        
        # Step 2: Augmentation - Create context from retrieved documents
        context = self._create_context(unique_docs)
        augmented_prompt = self._create_augmented_prompt(user_query, context)
        
        # Step 3: Generation
        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat",  # Using DeepSeek model
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": augmented_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(unique_docs)
            
            return {
                "answer": answer,
                "sources": unique_docs,
                "confidence": confidence
            }
            
        except Exception as e:
            # Fallback response if LLM fails
            return {
                "answer": self._create_fallback_response(user_query, unique_docs),
                "sources": unique_docs,
                "confidence": 0.5
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
        scores = [doc['score'] for doc in documents[:3]]
        return sum(scores) / len(scores)
    
    def _create_fallback_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Create a fallback response when LLM is unavailable"""
        if not documents:
            return "I couldn't find any relevant information about your question in the LegendaryCorp knowledge base."
        
        # Improved fallback response with better formatting
        response = "Based on the LegendaryCorp documents, here's the relevant information:\n\n"
        
        # Get the most relevant document
        top_doc = documents[0]
        response += f"**{top_doc['metadata']['title']}**\n\n"
        
        # Show more content from the top document
        text = top_doc['text']
        # Try to show complete sentences
        if len(text) > 400:
            text = text[:400]
            last_period = text.rfind('.')
            if last_period > 200:
                text = text[:last_period + 1]
        response += text + "\n\n"
        
        # Add other relevant sources if available
        if len(documents) > 1:
            response += "**Related information:**\n"
            for doc in documents[1:3]:
                response += f"• {doc['metadata']['title']}: {doc['text'][:100]}...\n"
        
        return response
        