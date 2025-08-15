# 💰 Cost Tracking System - LegendaryCorp RAG

This document explains how to use the built-in cost tracking system that provides **LangSmith-like cost analytics** without vendor lock-in.

## 🎯 What You Get

Your RAG system now includes comprehensive cost tracking that shows:

- **Real-time cost metrics** for each LLM request
- **Detailed cost breakdowns** by model and provider
- **Token usage analytics** with accurate counting
- **Cost alerts** for high-spending periods
- **Efficiency metrics** and optimization suggestions
- **Export capabilities** (JSON/CSV) for external analysis

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pipenv install tiktoken
```

### 2. Access the Cost Dashboard

Visit: `http://localhost:8000/costs`

### 3. View API Endpoints

Visit: `http://localhost:8000/redoc` and look for the "costs" section

## 📊 Cost Dashboard Features

### Real-time Metrics
- **Today's Cost**: Total spending in the last 24 hours
- **Total Requests**: Number of API calls today
- **Total Tokens**: Combined input/output tokens
- **Cost per Request**: Average cost per API call

### Interactive Charts
- **Daily Cost Trend**: Line chart showing spending over time
- **Model Cost Breakdown**: Doughnut chart by model/provider

### Cost Alerts
- Automatic alerts when daily spending exceeds thresholds
- Configurable alert levels (default: $10/day)

### Efficiency Metrics
- Cost per request, cost per token, tokens per request
- Optimization suggestions based on usage patterns

## 🔌 API Endpoints

### Cost Summary
```bash
GET /api/v1/costs/summary?days=30
```

Returns cost summary for the last N days with daily breakdown.

### Model Breakdown
```bash
GET /api/v1/costs/breakdown?days=30
```

Shows cost breakdown by model and provider.

### Real-time Metrics
```bash
GET /api/v1/costs/realtime
```

Current day's metrics with projections.

### Cost Alerts
```bash
GET /api/v1/costs/alerts?threshold=5.0
```

Alerts for spending above threshold.

### Export Data
```bash
GET /api/v1/costs/export?format=csv&days=30
GET /api/v1/costs/export?format=json&days=30
```

Export cost data in CSV or JSON format.

### Efficiency Metrics
```bash
GET /api/v1/costs/efficiency?days=30
```

Cost efficiency analysis and optimization suggestions.

## 💡 How It Works

### 1. **Token Counting**
- Uses `tiktoken` for accurate token counting
- Supports all major LLM models (GPT-4, Claude, DeepSeek, etc.)
- Fallback to word-based estimation if tiktoken unavailable

### 2. **Cost Calculation**
- Real-time pricing for different models and providers
- Separate input/output token pricing
- Automatic provider detection

### 3. **Data Storage**
- SQLite database for persistent storage
- Structured schema for easy querying
- Automatic cleanup and optimization

### 4. **Integration**
- Seamlessly integrated with your existing ChatEngine
- No changes needed to your current RAG pipeline
- Automatic cost tracking on every request

## 🔧 Configuration

### Model Pricing
Update pricing in `app/core/cost_tracker.py`:

```python
PRICING = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    },
    "deepseek": {
        "deepseek/deepseek-chat": {"input": 0.00014, "output": 0.00028},
    }
}
```

### Alert Thresholds
Configure in the API calls or modify the default values.

## 📈 Usage Examples

### Track a Single Request
```python
from app.core.cost_tracker import CostTracker, CostBreakdown
from datetime import datetime

tracker = CostTracker()

# Create cost breakdown
cost_breakdown = CostBreakdown(
    request_id="req_123",
    timestamp=datetime.now(),
    model="gpt-4",
    provider="openai",
    input_tokens=1000,
    output_tokens=500,
    total_tokens=1500,
    input_cost=0.03,
    output_cost=0.03,
    total_cost=0.06,
    user_query="What is AI?",
    response_length=250,
    processing_time=2.5
)

# Track it
tracker.track_request(cost_breakdown)
```

### Get Cost Analytics
```python
# Get 30-day summary
summary = tracker.get_cost_summary(30)
print(f"Total cost: ${summary['total_summary']['total_cost']}")

# Get model breakdown
breakdown = tracker.get_model_breakdown(30)
for model in breakdown['models']:
    print(f"{model['model']}: ${model['cost']}")

# Export to CSV
csv_data = tracker.export_cost_data("csv", 30)
with open("costs.csv", "w") as f:
    f.write(csv_data)
```

## 🧪 Testing

Run the test script to verify everything works:

```bash
python test_cost_tracking.py
```

This will test:
- Cost calculator
- Token counter
- Cost tracker
- Chat engine integration

## 🔍 Monitoring & Alerts

### Automatic Monitoring
- Every request is automatically tracked
- Real-time cost updates
- Automatic alert generation

### Manual Monitoring
- Check dashboard at `/costs`
- Use API endpoints for custom monitoring
- Export data for external analysis

### Alert Types
- **High Daily Cost**: Spending above threshold
- **Efficiency Issues**: High token usage per request
- **Model Performance**: Cost comparison between models

## 🚨 Troubleshooting

### Common Issues

1. **"tiktoken not available"**
   ```bash
   pipenv install tiktoken
   ```

2. **Database errors**
   - Check file permissions for `cost_tracking.db`
   - Ensure SQLite is available

3. **Cost calculation errors**
   - Verify model names match pricing table
   - Check provider configuration

### Debug Mode
Enable detailed logging in `app/core/cost_tracker.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Sample Output

### Cost Summary Response
```json
{
  "period_days": 30,
  "start_date": "2024-01-01",
  "daily_breakdown": [
    {
      "date": "2024-01-15",
      "requests": 25,
      "tokens": 12500,
      "cost": 0.375,
      "avg_time": 2.1
    }
  ],
  "total_summary": {
    "total_requests": 750,
    "total_tokens": 375000,
    "total_cost": 11.25,
    "avg_processing_time": 2.3
  }
}
```

### Efficiency Metrics
```json
{
  "cost_efficiency": {
    "cost_per_request": 0.015,
    "cost_per_token": 0.00003,
    "tokens_per_request": 500
  },
  "optimization_suggestions": [
    "Consider using more cost-effective models for simple queries"
  ]
}
```

## 🎉 Benefits Over LangSmith

### ✅ **Advantages**
- **No vendor lock-in**: You own all your data
- **No monthly fees**: One-time setup cost only
- **Full customization**: Modify any part of the system
- **Offline capability**: Works without external services
- **Privacy**: All data stays on your infrastructure

### ⚠️ **Trade-offs**
- **Self-maintained**: You handle updates and maintenance
- **Less polished**: May need UI improvements
- **Limited integrations**: No built-in third-party tools

## 🔮 Future Enhancements

Potential improvements you could add:

1. **Email/Slack alerts** for cost thresholds
2. **Budget management** with spending limits
3. **Cost forecasting** based on usage patterns
4. **Multi-tenant support** for different users/teams
5. **Advanced analytics** with machine learning insights
6. **Integration with billing systems** (Stripe, etc.)

## 📚 Additional Resources

- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [DeepSeek Pricing](https://platform.deepseek.com/pricing)
- [Token Counting Guide](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them)

---

**🎯 Goal**: You now have enterprise-grade cost tracking without the enterprise lock-in! 

Your RAG system tracks every penny spent on LLM APIs, provides beautiful dashboards, and gives you the insights you need to optimize costs - all while maintaining full control over your data and infrastructure.
