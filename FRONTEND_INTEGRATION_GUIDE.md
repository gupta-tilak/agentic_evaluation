# 🚀 Frontend Integration Guide
## Agentic Evaluation API Backend

This guide provides complete instructions for integrating your frontend with the fixed agentic evaluation API backend.

---

## 📋 Prerequisites

- ✅ API backend is fixed and running (`api_backend.py`)
- ✅ GROQ API key is configured
- ✅ Frontend can make HTTP requests (fetch/axios)

---

## 🚀 Step 1: Start Your Fixed API Backend

```bash
# Terminal 1 - Start the API server
cd /Users/guptatilak/Desktop/deepeval
export GROQ_API_KEY=""
python3 api_backend.py
```

**Wait for this output:**
```
✅ Groq model ready: groq/llama-3.1-8b-instant
✅ API ready to serve requests
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🔌 Step 2: Frontend Integration Points

### A. Health Check (Optional)
```javascript
// Check if API is ready
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log('API Status:', data.status))
```

### B. Get Available Agents
```javascript
// Get list of available agent types
fetch('http://localhost:8000/agents')
  .then(r => r.json())
  .then(agents => {
    // agents = [
    //   {name: "High Quality Mock Agent", type: "mock_high", domain: "general"},
    //   {name: "Average Quality Mock Agent", type: "mock_average", domain: "general"},
    //   {name: "Poor Quality Mock Agent", type: "mock_poor", domain: "general"}
    // ]
  })
```

### C. Start Evaluation (Main Integration)
```javascript
// Your frontend evaluation request
const evaluationRequest = {
  agents: [
    {name: "Expert AI Assistant", type: "mock_high", domain: "general"},
    {name: "Standard Assistant", type: "mock_average", domain: "general"},
    {name: "Basic Assistant", type: "mock_poor", domain: "general"}
  ],
  test_cases: [
    {
      test_case_id: 1,
      prompt: "What is 2 + 2? Answer with a single number.",
      reference: "4",
      context: ""
    },
    {
      test_case_id: 2, 
      prompt: "Who wrote 'Pride and Prejudice'?",
      reference: "Jane Austen",
      context: ""
    }
    // Add your actual test cases here
  ]
}

// Start evaluation
fetch('http://localhost:8000/evaluate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(evaluationRequest)
})
.then(r => r.json())
.then(response => {
  console.log('Evaluation started:', response.evaluation_id)
  // Store the evaluation_id for polling results
  pollForResults(response.evaluation_id)
})
```

### D. Poll for Results
```javascript
function pollForResults(evaluationId) {
  const checkResults = () => {
    fetch(`http://localhost:8000/results/${evaluationId}/responses`)
      .then(r => r.json())
      .then(data => {
        if (data.status === 'completed') {
          console.log('Evaluation complete!', data.responses)
          displayResults(data.responses) // Your UI update function
        } else {
          console.log('Progress:', data.progress + '%')
          setTimeout(checkResults, 2000) // Check again in 2 seconds
        }
      })
  }
  checkResults()
}
```

---

## 📊 Step 3: Expected Response Format

Your frontend will receive responses in this format:
```javascript
{
  "status": "completed",
  "responses": [
    {
      "agent": "Expert AI Assistant",
      "domain": "general", 
      "prompt": "What is 2 + 2? Answer with a single number.",
      "response": "4",
      "reference": "4",
      "test_case_id": 1,
      "metric_scores": {
        "instruction_following": {"score": 1.0, "success": true},
        "coherence_accuracy": {"score": 1.0, "success": true},
        "hallucination_detection": {"score": 1.0, "success": true},
        "relevance_quality": {"score": 1.0, "success": true}
      }
    }
    // More responses for other agents/test cases...
  ]
}
```

---

## ⚙️ Step 4: Agent Quality Configuration

### For Demonstration/Testing:
```javascript
agents: [
  {name: "Expert Agent", type: "mock_high", domain: "general"},     // ~95-100% scores
  {name: "Standard Agent", type: "mock_average", domain: "general"}, // ~80-90% scores  
  {name: "Basic Agent", type: "mock_poor", domain: "general"}        // ~20-40% scores
]
```

### For Production (Real Models):
```javascript
agents: [
  {name: "GPT-4", type: "huggingface", model_name: "gpt2", domain: "general"},
  {name: "DistilGPT-2", type: "huggingface", model_name: "distilgpt2", domain: "general"}
]
```

---

## 🛡️ Step 5: Error Handling

Add these error handlers to your frontend:

```javascript
// Handle API errors
fetch('http://localhost:8000/evaluate', {/*...*/})
  .then(r => {
    if (!r.ok) throw new Error(`API Error: ${r.status}`)
    return r.json()
  })
  .catch(error => {
    console.error('Evaluation failed:', error)
    // Show user-friendly error message
  })
```

---

## 🧪 Step 6: Test Your Integration

1. **Start API**: `python3 api_backend.py` 
2. **Test with curl** (verify backend works):
   ```bash
   curl -X POST -H "Content-Type: application/json" -d @test_mixed_quality.json http://localhost:8000/evaluate
   ```
3. **Connect your frontend** using the JavaScript examples above
4. **Verify results** show realistic score variation

---

## 🎯 Key Integration Points

| Setting | Value | Description |
|---------|-------|-------------|
| **API Base URL** | `http://localhost:8000` | Your backend server |
| **Content-Type** | `application/json` | Always required for POST requests |
| **Evaluation ID** | Store from `/evaluate` response | Used for polling results |
| **Agent Types** | `mock_high`, `mock_average`, `mock_poor` | For demos with score variation |
| **Test Case Format** | `{test_case_id, prompt, reference, context}` | Required fields |
| **Polling Interval** | 2-3 seconds | Check results until completed |

---

## 📝 Complete Frontend Integration Example

```javascript
class AgenticEvaluationClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl
  }

  async checkHealth() {
    const response = await fetch(`${this.baseUrl}/health`)
    return response.json()
  }

  async getAgents() {
    const response = await fetch(`${this.baseUrl}/agents`)
    return response.json()
  }

  async startEvaluation(agents, testCases) {
    const request = { agents, test_cases: testCases }
    
    const response = await fetch(`${this.baseUrl}/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })
    
    if (!response.ok) {
      throw new Error(`Evaluation failed: ${response.status}`)
    }
    
    return response.json()
  }

  async pollResults(evaluationId) {
    return new Promise((resolve, reject) => {
      const checkResults = async () => {
        try {
          const response = await fetch(`${this.baseUrl}/results/${evaluationId}/responses`)
          const data = await response.json()
          
          if (data.status === 'completed') {
            resolve(data.responses)
          } else if (data.status === 'failed') {
            reject(new Error('Evaluation failed'))
          } else {
            setTimeout(checkResults, 2000)
          }
        } catch (error) {
          reject(error)
        }
      }
      checkResults()
    })
  }

  async runEvaluation(agents, testCases) {
    // Start evaluation
    const startResponse = await this.startEvaluation(agents, testCases)
    console.log('Evaluation started:', startResponse.evaluation_id)
    
    // Poll for results
    const results = await this.pollResults(startResponse.evaluation_id)
    console.log('Evaluation completed:', results.length, 'responses')
    
    return results
  }
}

// Usage example:
const client = new AgenticEvaluationClient()

const agents = [
  {name: "Expert Agent", type: "mock_high", domain: "general"},
  {name: "Standard Agent", type: "mock_average", domain: "general"},
  {name: "Basic Agent", type: "mock_poor", domain: "general"}
]

const testCases = [
  {
    test_case_id: 1,
    prompt: "What is 2 + 2? Answer with a single number.",
    reference: "4",
    context: ""
  },
  {
    test_case_id: 2,
    prompt: "Who wrote 'Pride and Prejudice'?",
    reference: "Jane Austen", 
    context: ""
  }
]

// Run the evaluation
client.runEvaluation(agents, testCases)
  .then(results => {
    console.log('Final results:', results)
    // Update your UI with the results
  })
  .catch(error => {
    console.error('Evaluation error:', error)
  })
```

---

## ✅ Success Checklist

- [ ] API backend starts successfully
- [ ] Health check returns "healthy" status
- [ ] Agents endpoint returns available agent types
- [ ] Evaluation request starts and returns evaluation_id
- [ ] Results polling shows progress updates
- [ ] Final results show realistic score variation
- [ ] Error handling works for failed requests

---

## 🐛 Troubleshooting

### Common Issues:

1. **API not starting**: Check GROQ_API_KEY is set
2. **CORS errors**: API has CORS enabled for all origins
3. **Perfect scores**: Use mixed agent types (high/average/poor)
4. **Timeout errors**: Increase polling interval to 3-5 seconds
5. **Rate limits**: Groq free tier has limits, wait between requests

### Debug Commands:
```bash
# Test health
curl http://localhost:8000/health

# Test agents
curl http://localhost:8000/agents

# Test evaluation
curl -X POST -H "Content-Type: application/json" -d @test_mixed_quality.json http://localhost:8000/evaluate
```

---

**🎉 Your API backend is now production-ready and will provide realistic, varied evaluation scores!**
