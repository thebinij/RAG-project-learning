"""
Cost Analytics API - Provides cost tracking and analytics endpoints
Similar to LangSmith's cost dashboard but open-source
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from app.core.engines.chat_engine import ChatEngine
from app.core.engines.vector_engine import VectorEngine

router = APIRouter(prefix="/costs", tags=["costs"])

# Initialize engines (in production, this would be dependency injection)
vector_engine = VectorEngine()
chat_engine = ChatEngine(vector_engine)


@router.get("/summary")
async def get_cost_summary(days: int = Query(30, ge=1, le=365, description="Number of days to analyze")):
    """Get cost summary for the last N days"""
    try:
        summary = chat_engine.get_cost_summary(days)
        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost summary: {str(e)}")


@router.get("/breakdown")
async def get_model_breakdown(days: int = Query(30, ge=1, le=365, description="Number of days to analyze")):
    """Get cost breakdown by model and provider"""
    try:
        breakdown = chat_engine.get_model_breakdown(days)
        return JSONResponse(content=breakdown)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model breakdown: {str(e)}")


@router.get("/alerts")
async def get_cost_alerts(threshold: float = Query(10.0, ge=0.1, description="Cost threshold for alerts")):
    """Get cost alerts for high-spending periods"""
    try:
        alerts = chat_engine.get_cost_alerts(threshold)
        return JSONResponse(content={"alerts": alerts, "threshold": threshold})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost alerts: {str(e)}")


@router.get("/export")
async def export_cost_data(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    days: int = Query(30, ge=1, le=365, description="Number of days to export")
):
    """Export cost data in various formats"""
    try:
        if format == "csv":
            csv_data = chat_engine.export_cost_data("csv", days)
            return PlainTextResponse(content=csv_data, media_type="text/csv")
        else:
            json_data = chat_engine.export_cost_data("json", days)
            return JSONResponse(content=json_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting cost data: {str(e)}")


@router.get("/realtime")
async def get_realtime_metrics():
    """Get real-time cost metrics for the current day"""
    try:
        # Get today's costs
        today_summary = chat_engine.get_cost_summary(1)
        
        # Handle case where no data exists yet
        if "error" in today_summary:
            return JSONResponse(content={
                "current_time": datetime.now().isoformat(),
                "today_total_cost": 0.0,
                "today_total_requests": 0,
                "today_total_tokens": 0,
                "hourly_average_cost": 0.0,
                "projected_daily_cost": 0.0,
                "cost_per_request": 0.0,
                "note": "No cost data available yet. Start making requests to see metrics."
            })
        
        # Calculate hourly breakdown for today
        current_hour = datetime.now().hour
        total_cost = today_summary["total_summary"]["total_cost"]
        total_requests = today_summary["total_summary"]["total_requests"]
        total_tokens = today_summary["total_summary"]["total_tokens"]
        
        hourly_estimate = total_cost / 24 if current_hour > 0 else 0
        
        realtime_metrics = {
            "current_time": datetime.now().isoformat(),
            "today_total_cost": total_cost,
            "today_total_requests": total_requests,
            "today_total_tokens": total_tokens,
            "hourly_average_cost": hourly_estimate,
            "projected_daily_cost": hourly_estimate * 24,
            "cost_per_request": total_cost / total_requests if total_requests > 0 else 0.0
        }
        
        return JSONResponse(content=realtime_metrics)
    except Exception as e:
        print(f"Realtime metrics error: {e}")
        return JSONResponse(content={
            "current_time": datetime.now().isoformat(),
            "today_total_cost": 0.0,
            "today_total_requests": 0,
            "today_total_tokens": 0,
            "hourly_average_cost": 0.0,
            "projected_daily_cost": 0.0,
            "cost_per_request": 0.0,
            "error": f"Error getting realtime metrics: {str(e)}"
        }, status_code=500)


@router.get("/efficiency")
async def get_efficiency_metrics(days: int = Query(30, ge=1, le=365, description="Number of days to analyze")):
    """Get efficiency metrics for cost optimization"""
    try:
        summary = chat_engine.get_cost_summary(days)
        breakdown = chat_engine.get_model_breakdown(days)
        
        # Handle case where no data exists yet
        if "error" in summary or "error" in breakdown:
            # Return default efficiency metrics for new systems
            return JSONResponse(content={
                "period_days": days,
                "cost_efficiency": {
                    "cost_per_request": 0.0,
                    "cost_per_token": 0.0,
                    "tokens_per_request": 0
                },
                "model_efficiency": [],
                "optimization_suggestions": [
                    "No cost data available yet. Start making requests to see efficiency metrics.",
                    "Consider using cost-effective models like DeepSeek for initial testing."
                ],
                "note": "System is new with no cost data yet"
            })
        
        total_cost = summary["total_summary"]["total_cost"]
        total_requests = summary["total_summary"]["total_requests"]
        total_tokens = summary["total_summary"]["total_tokens"]
        
        # Handle division by zero cases
        if total_requests == 0 or total_tokens == 0:
            return JSONResponse(content={
                "period_days": days,
                "cost_efficiency": {
                    "cost_per_request": 0.0,
                    "cost_per_token": 0.0,
                    "tokens_per_request": 0
                },
                "model_efficiency": [],
                "optimization_suggestions": [
                    "No requests or tokens recorded yet. Start making requests to see efficiency metrics."
                ],
                "note": "No usage data available"
            })
        
        efficiency_metrics = {
            "period_days": days,
            "cost_efficiency": {
                "cost_per_request": total_cost / total_requests,
                "cost_per_token": total_cost / total_tokens,
                "tokens_per_request": total_tokens / total_requests
            },
            "model_efficiency": [],
            "optimization_suggestions": []
        }
        
        # Analyze model efficiency
        for model_data in breakdown.get("models", []):
            if model_data.get("requests", 0) > 0 and model_data.get("tokens", 0) > 0:
                model_efficiency = {
                    "model": model_data["model"],
                    "provider": model_data["provider"],
                    "cost_per_request": model_data["cost"] / model_data["requests"],
                    "cost_per_token": model_data["cost"] / model_data["tokens"],
                    "requests_percentage": (model_data["requests"] / total_requests * 100)
                }
                efficiency_metrics["model_efficiency"].append(model_efficiency)
        
        # Generate optimization suggestions
        if total_cost > 50:  # If spending more than $50
            efficiency_metrics["optimization_suggestions"].append(
                "Consider using more cost-effective models for simple queries"
            )
        
        if total_tokens / total_requests > 2000: # If average tokens per request is high
            efficiency_metrics["optimization_suggestions"].append(
                "Optimize prompts to reduce token usage"
            )
        
        return JSONResponse(content=efficiency_metrics)
    except Exception as e:
        # Log the actual error for debugging
        print(f"Efficiency metrics error: {e}")
        return JSONResponse(content={
            "period_days": days,
            "error": f"Error getting efficiency metrics: {str(e)}",
            "cost_efficiency": {
                "cost_per_request": 0.0,
                "cost_per_token": 0.0,
                "tokens_per_request": 0
            },
            "model_efficiency": [],
            "optimization_suggestions": [
                "Unable to calculate efficiency metrics due to an error."
            ]
        }, status_code=500)


@router.get("/health")
async def health_check():
    """Health check for cost tracking system"""
    try:
        # Test basic functionality
        summary = chat_engine.get_cost_summary(1)
        return JSONResponse(content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cost_tracking": "active" if "error" not in summary else "error"
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }, status_code=500)
