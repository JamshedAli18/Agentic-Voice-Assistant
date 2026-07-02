# Agentic Voice Assistant

### A powerful, full-stack real-time voice and text conversational AI application. This system integrates advanced Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities powered by Groq and Cartesia, orchestrated through a LangGraph agentic backend, and presented in a sleek, responsive React frontend.
---

## Features
 
- **Real-Time Voice Interaction:** Seamlessly record audio, transcribe it via Groq Whisper, and receive human-like vocal responses powered by Cartesia.
- **Agentic Capabilities:** The AI doesn't just chat—it thinks. Powered by LangGraph, it can utilize tools like Tavily for live web searches.
- **Streaming Text Chat:** A text-fallback mode that streams LLM responses in real-time via Server-Sent Events (SSE).
- **Session Memory:** Built-in conversation memory management to maintain context across multiple interactions.
- **Modern UI:** A clean, glassmorphism-inspired React interface with custom animations and responsive design.

---

## Technology Stack

### **Frontend**
- **Framework:** React 19 + Vite
- **Styling:** Vanilla CSS (Custom modern UI system)
- **Icons:** Lucide React
- **Deployment:** Vercel

### **Backend**
- **Framework:** FastAPI
- **LLM & STT Engine:** Groq (`llama-3.3-70b-versatile`, `whisper-large-v3-turbo`)
- **TTS Engine:** Cartesia (`sonic-3.5`)
- **Agent Orchestration:** LangChain / LangGraph
- **Search Tool:** Tavily / SerpAPI
- **Deployment:** Render

---

## 📁 Project Structure

```text
voice-ai-chatbot/
├── backend/                 # FastAPI Backend Application
│   ├── main.py              # Application entry point & API routes
│   ├── agent.py             # LangGraph agent setup & logic
│   ├── memory.py            # Session-based context management
│   ├── config.py            # Environment & Pydantic settings
│   ├── stt.py               # Groq audio transcription module
│   ├── tts.py               # Cartesia speech synthesis module
│   ├── tools.py             # Tools provided to the agent (e.g., Search)
│   ├── requirements.txt     # Python dependencies for deployment
│   └── pyproject.toml       # Local development dependencies
│
└── frontend/                # React Vite Frontend Application
    ├── public/              # Static assets
    ├── src/
    │   ├── components/      # Reusable UI components
    │   ├── hooks/           # Custom React hooks (e.g., useVoiceChat)
    │   ├── App.jsx          # Main application component
    │   ├── index.css        # Global styles & design system
    │   └── main.jsx         # React DOM entry point
    ├── package.json         # Node.js dependencies
    └── vite.config.js       # Vite configuration
```

---

## 🚀 Local Development Guide

### 1. Backend Setup

Open a terminal and navigate to the `backend` directory:
```bash
cd backend
```

Create a `.env` file based on the required variables:
```env
GROQ_API_KEY=your_groq_api_key
CARTESIA_API_KEY=your_cartesia_api_key
TAVILY_API_KEY=your_tavily_api_key
CORS_ORIGINS=["http://localhost:5173"]
```

Install dependencies and run the server:
```bash
# Using pip
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
The backend will be available at `http://localhost:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend
```

Create a `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

Install dependencies and start the Vite dev server:
```bash
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`.

---

## 🌐 Deployment Instructions

### Backend (Render)
1. Create a new Web Service on Render connected to your repository.
2. Set Root Directory to `backend`.
3. Set Build Command to `pip install -r requirements.txt`.
4. Set Start Command to `uvicorn main:app --host 0.0.0.0 --port 10000`.
5. Add all API keys to the Environment Variables. Ensure `CORS_ORIGINS` is formatted as a valid JSON list (e.g., `["https://your-frontend.vercel.app"]`).

### Frontend (Vercel)
1. Import the repository into Vercel.
2. Set the Root Directory to `frontend`.
3. Add the `VITE_API_URL` environment variable pointing to your deployed Render backend URL.
4. Deploy!

---

## 📄 License
This project is open-source and available under the MIT License.
