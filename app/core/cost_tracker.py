"""
Cost Tracker - Tracks API costs for LLM requests
Provides detailed cost breakdown similar to LangSmith
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a single request"""
    request_id: str
    timestamp: datetime
    model: str
    provider: str
    
    # Token counts
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Costs
    input_cost: float
    output_cost: float
    total_cost: float
    
    # Request details
    user_query: str
    response_length: int
    processing_time: float
    
    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None


class CostCalculator:
    """Calculates costs for different LLM providers"""
    
    # Pricing per 1K tokens (as of 2024 - update as needed)
    PRICING = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        },
        "deepseek": {
            "deepseek/deepseek-chat": {"input": 0.00014, "output": 0.00028},
            "deepseek/deepseek-coder": {"input": 0.00014, "output": 0.00028},
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        },
        "google": {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro-vision": {"input": 0.0005, "output": 0.0015},
        },
        "custom": {
            "default": {"input": 0.001, "output": 0.002},
        }
    }
    
    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int, provider: str = "custom") -> Dict[str, float]:
        """Calculate cost for a request"""
        
        # Find pricing for the model
        pricing = cls._get_pricing(model, provider)
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6)
        }
    
    @classmethod
    def _get_pricing(cls, model: str, provider: str) -> Dict[str, float]:
        """Get pricing for a specific model"""
        
        # Try provider-specific pricing first
        if provider in cls.PRICING and model in cls.PRICING[provider]:
            return cls.PRICING[provider][model]
        
        # Try to find model in any provider
        for prov, models in cls.PRICING.items():
            if model in models:
                return models[model]
        
        # Fallback to default pricing
        return cls.PRICING["custom"]["default"]


class CostTracker:
    """Main cost tracking system"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use configuration from settings
            try:
                from app.core.config import settings
                data_dir = Path(settings.cost_db_path)
            except ImportError:
                # Fallback to default data directory
                data_dir = Path("./data/costs")
            
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "cost_tracking.db")
        else:
            self.db_path = db_path
        
        self._init_database()
        self._setup_logging()
    
    def _init_database(self):
        """Initialize SQLite database for cost tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create costs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costs (
                request_id TEXT PRIMARY KEY,
                timestamp TEXT,
                model TEXT,
                provider TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                input_cost REAL,
                output_cost REAL,
                total_cost REAL,
                user_query TEXT,
                response_length INTEGER,
                processing_time REAL,
                user_id TEXT,
                session_id TEXT,
                tags TEXT
            )
        """)
        
        # Create daily_summary table for analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                date TEXT PRIMARY KEY,
                total_requests INTEGER,
                total_tokens INTEGER,
                total_cost REAL,
                avg_processing_time REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _setup_logging(self):
        """Setup logging for cost tracking"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def track_request(self, cost_breakdown: CostBreakdown):
        """Track a single request cost"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO costs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cost_breakdown.request_id,
                cost_breakdown.timestamp.isoformat(),
                cost_breakdown.model,
                cost_breakdown.provider,
                cost_breakdown.input_tokens,
                cost_breakdown.output_tokens,
                cost_breakdown.total_tokens,
                cost_breakdown.input_cost,
                cost_breakdown.output_cost,
                cost_breakdown.total_cost,
                cost_breakdown.user_query,
                cost_breakdown.response_length,
                cost_breakdown.processing_time,
                cost_breakdown.user_id,
                cost_breakdown.session_id,
                json.dumps(cost_breakdown.tags) if cost_breakdown.tags else None
            ))
            
            conn.commit()
            conn.close()
            
            # Log the cost
            logger.info(f"Cost tracked: ${cost_breakdown.total_cost:.6f} for {cost_breakdown.model}")
            
        except Exception as e:
            logger.error(f"Error tracking cost: {e}")
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get cost summary for the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get daily costs
            start_date = (datetime.now() - timedelta(days=days)).date()
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(total_cost) as cost,
                    AVG(processing_time) as avg_time
                FROM costs 
                WHERE DATE(timestamp) >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (start_date.isoformat(),))
            
            daily_data = cursor.fetchall()
            
            # Get total summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost) as total_cost,
                    AVG(processing_time) as avg_processing_time
                FROM costs 
                WHERE DATE(timestamp) >= ?
            """, (start_date.isoformat(),))
            
            total_summary = cursor.fetchone()
            
            conn.close()
            
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "daily_breakdown": [
                    {
                        "date": row[0],
                        "requests": row[1],
                        "tokens": row[2],
                        "cost": row[3],
                        "avg_time": row[4]
                    } for row in daily_data
                ],
                "total_summary": {
                    "total_requests": total_summary[0] or 0,
                    "total_tokens": total_summary[1] or 0,
                    "total_cost": total_summary[2] or 0.0,
                    "avg_processing_time": total_summary[3] or 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cost summary: {e}")
            return {"error": str(e)}
    
    def get_model_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """Get cost breakdown by model"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).date()
            cursor.execute("""
                SELECT 
                    model,
                    provider,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(total_cost) as cost,
                    AVG(processing_time) as avg_time
                FROM costs 
                WHERE DATE(timestamp) >= ?
                GROUP BY model, provider
                ORDER BY cost DESC
            """, (start_date.isoformat(),))
            
            model_data = cursor.fetchall()
            conn.close()
            
            return {
                "period_days": days,
                "models": [
                    {
                        "model": row[0],
                        "provider": row[1],
                        "requests": row[2],
                        "tokens": row[3],
                        "cost": row[4],
                        "avg_time": row[5]
                    } for row in model_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting model breakdown: {e}")
            return {"error": str(e)}
    
    def export_cost_data(self, format: str = "json", days: int = 30) -> str:
        """Export cost data in various formats"""
        summary = self.get_cost_summary(days)
        
        if format == "json":
            return json.dumps(summary, indent=2, default=str)
        elif format == "csv":
            # Convert to CSV format
            csv_lines = ["Date,Requests,Tokens,Cost,AvgTime"]
            for day in summary["daily_breakdown"]:
                csv_lines.append(f"{day['date']},{day['requests']},{day['tokens']},{day['cost']},{day['avg_time']}")
            return "\n".join(csv_lines)
        else:
            return str(summary)
    
    def get_cost_alerts(self, threshold: float = 10.0) -> List[Dict[str, Any]]:
        """Get cost alerts for high-spending periods"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(total_cost) as daily_cost,
                    COUNT(*) as requests
                FROM costs 
                WHERE DATE(timestamp) >= DATE('now', '-7 days')
                GROUP BY DATE(timestamp)
                HAVING daily_cost > ?
                ORDER BY daily_cost DESC
            """, (threshold,))
            
            alerts = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "date": row[0],
                    "daily_cost": row[1],
                    "requests": row[2],
                    "alert_type": "high_cost"
                } for row in alerts
            ]
            
        except Exception as e:
            logger.error(f"Error getting cost alerts: {e}")
            return []
