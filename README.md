# Oracle-X Financial Intelligence Terminal

A zero-cost, local-first Financial Intelligence Terminal combining Stocks, Crypto, RAG AI, and Blockchain verification.

![Oracle-X](https://img.shields.io/badge/Oracle--X-Financial%20Intelligence-6366f1)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Blockchain](https://img.shields.io/badge/Blockchain-Sepolia-purple)

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Ollama** (for local LLM - Phase 2)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API docs (Swagger UI): http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📁 Project Structure

```
crypto-stock-lens/
├── backend/                    # Python FastAPI Backend
│   ├── main.py                # Entry point with API routes
│   ├── requirements.txt       # Python dependencies
│   └── models/
│       └── schemas.py         # Pydantic models
│
├── frontend/                   # Next.js 14 App Router
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main dashboard
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── NewsFeed.tsx       # Left Panel - The Feed
│   │   ├── ChartPanel.tsx     # Middle Panel - TradingView
│   │   └── OraclePanel.tsx    # Right Panel - AI Analysis
│   ├── store/
│   │   └── useStore.ts        # Zustand state
│   └── lib/
│       └── api.ts             # API utilities
│
└── contracts/                  # Smart Contracts (Phase 3)
```

## 🎨 Features

- **3-Column Dashboard Layout**: News Feed (20%) | Chart (50%) | Oracle (30%)
- **Real-Time TradingView Charts**: Dynamic symbol updates
- **AI-Powered Analysis**: Sentiment, confidence scores, historical context
- **Blockchain Verification**: Record predictions on-chain (Sepolia)

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Zustand |
| Backend | Python, FastAPI, Uvicorn |
| AI/RAG | Ollama (Llama 3), LangChain, ChromaDB |
| Blockchain | Solidity, Hardhat, Ethers.js |
| Data | yfinance, RSS feeds |

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/news` | GET | Fetch news feed |
| `/api/news/{id}` | GET | Get specific news item |
| `/api/analyze` | POST | Analyze news with AI |
| `/api/symbols` | GET | List tracked symbols |

## 🔜 Roadmap

- [x] Phase 1: Project structure & mock endpoints
- [ ] Phase 2: RAG pipeline (ChromaDB + Ollama)
- [ ] Phase 3: Smart contract verification
- [ ] Phase 4: Live data feeds

---

Built with ❤️ using Oracle-X
