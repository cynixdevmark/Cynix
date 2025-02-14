<div align="center">
 <img src="/cynix.png" alt="Cynix Logo" width="400px" />

 [![Website](https://img.shields.io/badge/website-cynix.io-blue)](https://cynix.io/)
 [![X(Twitter)](https://img.shields.io/badge/X-Cynix__io-black?logo=x)](https://x.com/Cynix__io)
 [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
 [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
 [![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)

</div>

Cynix is an advanced analytics platform that leverages AI to analyze Solana meme tokens, providing real-time insights through specialized AI agents. The platform includes token-gated premium features and comprehensive data analysis capabilities.

## Features

### AI Agents
- **Aura** - Code and Contract Analysis Agent
  - Repository analysis
  - Smart contract validation
  - Alpha signal detection
  
- **Myca** - Meme Analysis Agent
  - Image originality verification
  - Virality prediction
  - Trend analysis
  
- **Infy** - Influencer Analysis Agent
  - Credibility scoring
  - Writing style analysis
  - Historical verification

### Token Utilities
- Premium alpha access (15-minute advantage)
- Raw data access
- API usage rights
- Community governance
- Promotional opportunities

## Installation

### Prerequisites
- Python 3.9+
- Redis
- Solana Tools

### Setup
1. Clone the repository
```bash
git clone https://github.com/cynixdevmark/Cynix.git
cd cynix
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Unix
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application
```bash
python main.py
```

## Configuration

Create appropriate YAML files in the `config` directory:
- `development.yaml`
- `production.yaml`


## API Documentation

### Authentication
All API endpoints require an API key passed in the `X-API-Key` header.

### Endpoints

#### Code Analysis
```http
POST /api/v1/analyze/code
```
Analyzes GitHub repositories and smart contracts.

#### Meme Analysis
```http
POST /api/v1/analyze/meme
```
Analyzes meme images for virality and originality.

#### Influencer Analysis
```http
POST /api/v1/analyze/influencer
```
Analyzes influencer credibility and historical data.

#### Raw Data Access
```http
GET /api/v1/data/{data_type}
```
Provides access to raw analysis data (requires token staking).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- Project Link: [https://github.com/cynixdevmark/Cynix](https://github.com/cynixdevmark/Cynix)
