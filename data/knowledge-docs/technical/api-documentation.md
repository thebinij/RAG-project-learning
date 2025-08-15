# LegendaryCorp API Documentation

## Overview
The LegendaryCorp API provides programmatic access to our AI services, allowing developers to integrate our capabilities into their applications. This documentation covers authentication, endpoints, request/response formats, and best practices.

## Base URL
```
Production: https://api.legendarycorp.com/v1
Sandbox: https://api-sandbox.legendarycorp.com/v1
```

## Authentication
All API requests require authentication using API keys.

### API Key Authentication
```http
Authorization: Bearer YOUR_API_KEY
```

### Getting Your API Key
1. Log into your LegendaryCorp account
2. Navigate to API Keys section
3. Generate a new API key
4. Store securely - keys cannot be retrieved after creation

### Rate Limits
- **Free Tier**: 1,000 requests/month
- **Pro Tier**: 10,000 requests/month
- **Enterprise**: Custom limits
- **Rate Limit Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Core Endpoints

### Chat Completion
Generate AI responses using our chat models.

#### Endpoint
```http
POST /chat/completions
```

#### Request Body
```json
{
  "model": "legendary-gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "max_tokens": 1000,
  "temperature": 0.7,
  "stream": false
}
```

#### Response
```json
{
  "id": "chatcmpl-1234567890",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "legendary-gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 15,
    "total_tokens": 40
  }
}
```

### Text Generation
Generate text using our language models.

#### Endpoint
```http
POST /completions
```

#### Request Body
```json
{
  "model": "legendary-text-davinci",
  "prompt": "Write a professional email requesting a meeting:",
  "max_tokens": 200,
  "temperature": 0.8,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

### Embeddings
Generate vector embeddings for text.

#### Endpoint
```http
POST /embeddings
```

#### Request Body
```json
{
  "model": "legendary-embedding-ada",
  "input": "The quick brown fox jumps over the lazy dog."
}
```

#### Response
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023064255, -0.009327292, ...],
      "index": 0
    }
  ],
  "model": "legendary-embedding-ada",
  "usage": {
    "prompt_tokens": 9,
    "total_tokens": 9
  }
}
```

## Available Models

### Chat Models
| Model | Description | Max Tokens | Cost per 1K tokens |
|-------|-------------|------------|-------------------|
| `legendary-gpt-4` | Most capable model | 8,192 | $0.03 |
| `legendary-gpt-3.5-turbo` | Fast and efficient | 4,096 | $0.002 |
| `legendary-claude-3` | Anthropic's latest | 16,000 | $0.015 |

### Text Models
| Model | Description | Max Tokens | Cost per 1K tokens |
|-------|-------------|------------|-------------------|
| `legendary-text-davinci` | High-quality text generation | 4,097 | $0.02 |
| `legendary-text-curie` | Balanced performance | 2,049 | $0.01 |
| `legendary-text-babbage` | Fast generation | 2,049 | $0.005 |

### Embedding Models
| Model | Description | Dimensions | Cost per 1K tokens |
|-------|-------------|------------|-------------------|
| `legendary-embedding-ada` | General purpose | 1,536 | $0.0001 |
| `legendary-embedding-curie` | High quality | 4,096 | $0.0002 |

## Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

### Error Response Format
```json
{
  "error": {
    "message": "Invalid API key",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

### Common Error Codes
| Code | Description | Solution |
|------|-------------|----------|
| `invalid_api_key` | API key is invalid or expired | Check your API key |
| `rate_limit_exceeded` | Rate limit exceeded | Wait or upgrade plan |
| `insufficient_quota` | Monthly quota exceeded | Upgrade plan or wait |
| `model_not_found` | Model name is invalid | Check model names |

## Best Practices

### Performance Optimization
1. **Use appropriate models** for your use case
2. **Set reasonable max_tokens** to control costs
3. **Implement caching** for repeated requests
4. **Use streaming** for long responses

### Security
1. **Never expose API keys** in client-side code
2. **Use environment variables** for API keys
3. **Implement rate limiting** in your application
4. **Validate all inputs** before sending to API

### Cost Management
1. **Monitor usage** with rate limit headers
2. **Set up alerts** for quota thresholds
3. **Use appropriate temperature** settings
4. **Implement request batching** when possible

## SDKs and Libraries

### Official SDKs
- **Python**: `pip install legendarycorp`
- **JavaScript**: `npm install @legendarycorp/sdk`
- **Go**: `go get github.com/legendarycorp/go-sdk`
- **Java**: Available in Maven Central

### Community Libraries
- **Ruby**: `gem install legendarycorp-ruby`
- **PHP**: `composer require legendarycorp/php-sdk`
- **C#**: `dotnet add package LegendaryCorp.SDK`

## Examples

### Python Example
```python
import legendarycorp

client = legendarycorp.Client(api_key="your-api-key")

response = client.chat.completions.create(
    model="legendary-gpt-4",
    messages=[
        {"role": "user", "content": "Explain quantum computing in simple terms"}
    ]
)

print(response.choices[0].message.content)
```

### JavaScript Example
```javascript
import { LegendaryCorp } from '@legendarycorp/sdk';

const client = new LegendaryCorp('your-api-key');

const response = await client.chat.completions.create({
    model: 'legendary-gpt-4',
    messages: [
        { role: 'user', content: 'Explain quantum computing in simple terms' }
    ]
});

console.log(response.choices[0].message.content);
```

## Support and Resources

### Documentation
- **API Reference**: https://docs.legendarycorp.com/api
- **Examples**: https://github.com/legendarycorp/examples
- **SDK Documentation**: https://docs.legendarycorp.com/sdks

### Community
- **Discord**: https://discord.gg/legendarycorp
- **GitHub**: https://github.com/legendarycorp
- **Blog**: https://blog.legendarycorp.com

### Support
- **Email**: api-support@legendarycorp.com
- **Status Page**: https://status.legendarycorp.com
- **Developer Portal**: https://developers.legendarycorp.com

---

*Last Updated: January 2024*
*API Version: v1.0*
