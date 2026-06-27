# LLM Batch Processor

A multi-provider SDK for batch processing with Large Language Models (LLMs) across different providers like OpenAI, Claude, Gemini, and more.

## Features

✅ **Multi-Provider Support** - Unified interface for OpenAI, Claude, Gemini, and other LLM providers  
✅ **Batch Processing** - Submit and manage batch requests efficiently  
✅ **Parallel Execution** - Process multiple batches concurrently  
✅ **Rate Limiting** - Built-in rate limiting to respect API quotas  
✅ **Retry Mechanism** - Automatic retries with exponential backoff  
✅ **File Support** - Read/write batches from JSONL, JSON files  
✅ **Easy Integration** - Simple API for developers  

## Installation

```bash
# Clone repository
git clone <repo-url>
cd batch_multi_provider_support

# Install core package
pip install -e .

# For OpenAI support
pip install -e ".[openai]"

# For Claude support
pip install -e ".[anthropic]"

# For Gemini support
pip install -e ".[google]"

# For development
pip install -e ".[dev]"
```

## Quick Start

### 1. Basic Usage

```python
from llm_batch_processor.providers import ProviderFactory
import os

# Create provider
provider = ProviderFactory.create(
    provider_name="openai",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define batch requests
batch = [
    {
        "custom_id": "request-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
    }
]

# Submit batch
batch_id = provider.submit_batch(batch)
print(f"Batch ID: {batch_id}")

# Check status
status = provider.get_batch_status(batch_id)
print(f"Status: {status}")

# Get results
results = provider.get_batch_results(batch_id)
print(f"Results: {results}")
```

### 2. List Available Providers

```python
from llm_batch_processor.providers import ProviderFactory

providers = ProviderFactory.get_available_providers()
print(providers)  # ['openai']
```

## Project Structure

```
llm_batch_processor/
├── core/              # Base classes & interfaces
├── providers/         # Provider implementations
├── engine/           # Batch processing engine (coming)
├── middleware/       # Rate limiting, retries (coming)
├── storage/          # File I/O (coming)
└── config/           # Configuration (coming)

examples/             # Usage examples
tests/                # Unit & integration tests (coming)
```

## Providers

### ✅ Implemented
- **OpenAI** - ChatGPT, GPT-4, etc.

### 🔄 Coming Soon
- **Claude** (Anthropic)
- **Gemini** (Google)
- **LLaMA** (Meta)
- **Cohere**

## Configuration

Providers are configured via environment variables or config dictionaries:

```python
config = {
    "model": "gpt-4",
    "timeout": 30,
    "max_retries": 3,
}

provider = ProviderFactory.create(
    provider_name="openai",
    api_key="sk-...",
    config=config
)
```

## API Documentation

### ProviderFactory

```python
# Create a provider
provider = ProviderFactory.create(
    provider_name: str,      # "openai", "claude", etc.
    api_key: str,            # API key
    config: dict = None,     # Optional config
)

# Register new provider
ProviderFactory.register_provider("custom", CustomProvider)

# Check available providers
providers = ProviderFactory.get_available_providers()

# Check if provider exists
exists = ProviderFactory.is_registered("openai")
```

### BaseProvider Methods

All providers implement:

```python
# Submit a batch
batch_id = provider.submit_batch(requests)

# Get batch status
status = provider.get_batch_status(batch_id)

# Get results
results = provider.get_batch_results(batch_id)

# Validate request
provider.validate_request(request)
```

## Development

### Run Tests (Coming)
```bash
pytest
```

### Code Quality
```bash
black .           # Format
ruff check .      # Lint
mypy .            # Type check
```

### Build & Publish (Coming)
```bash
python -m build
twine upload dist/*
```

## Roadmap

- [x] Phase 1: Basic provider abstraction
- [x] Phase 1: OpenAI provider
- [ ] Phase 2: Batch processing engine
- [ ] Phase 2: Rate limiting & retries
- [ ] Phase 3: File I/O support
- [ ] Phase 3: Claude & Gemini providers
- [ ] Phase 4: Async/parallel support
- [ ] Phase 4: Tests & documentation

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a PR

## License

MIT License - see LICENSE file

## Support

- 📖 [Documentation](https://github.com/yourusername/llm-batch-processor#readme)
- 🐛 [Issues](https://github.com/yourusername/llm-batch-processor/issues)
- 💬 [Discussions](https://github.com/yourusername/llm-batch-processor/discussions)
