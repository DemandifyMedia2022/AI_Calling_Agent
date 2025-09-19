# Athena - Your Personal AI Assistant

A beautiful web interface for your personal AI assistant powered by LiveKit and Google's Realtime AI.

## Features

- 🎨 **Modern UI**: Beautiful, responsive chat interface
- 🤖 **AI Assistant**: Powered by LiveKit and Google Realtime AI
- 💬 **Real-time Chat**: Smooth messaging experience with typing indicators
- 📱 **Mobile Responsive**: Works perfectly on all devices
- 🎯 **Personalized**: Customized for your needs as an AI Engineer

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   # The web UI fetches the LiveKit JS via HTTP; install httpx if not present
   pip install httpx
   ```

2. **Environment Variables**:
   Create a `.env` file in the project root with your LiveKit credentials (used by the Web UI token endpoint and browser call):
   ```
   LIVEKIT_API_KEY=your_api_key_here
   LIVEKIT_API_SECRET=your_api_secret_here
   LIVEKIT_URL=your_livekit_wss_or_https_url_here
   # Optional: override path to leads CSV
   LEADS_CSV_PATH=d:/path/to/leads.csv
   ```

3. **Run the Web UI (FastAPI + Uvicorn)**:
   From the project root (`AI_Calling_Agent/`):
   ```bash
   uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload
   ```
   This serves the dashboard at `/` and the browser call flow at `/browser/call`.

   python -m uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload

   py -m uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload


   Optional: start the agent from the console (for direct audio I/O testing):
   ```bash
   python .\agent.py console
   ```

4. **Access the Interface**:
   Open your browser and go to: `http://localhost:8000`

## Usage

- **Dashboard**: Shows paginated leads from `leads.csv` (or `LEADS_CSV_PATH`).
- **Campaign**: Use the dropdown to select a campaign (maps to different prompt modules).
- **Call (Console)**: Clicking a lead’s Call button spawns a one-off console agent using `agent.py`.
- **Call (Browser)**: Use the Browser Call action to open a tab that connects your browser to the LiveKit room where the agent joins. Requires valid `LIVEKIT_*` variables.

## Customization

- **Character**: Modify `prompts.py` (and `prompts2.py`, `prompts3.py`, `prompts4.py`) to change campaign personalities.
- **Voice**: Update the voice in `agent.py` (available: Puck, Charon, Kore, Fenrir, Aoede, Leda, Oru, Zephyr). Default is `Leda`.
- **UI**: Customize templates in `webui/templates/` (`index.html`, `browser_call.html`) and assets in `webui/static/`.

## Files Structure

```
├── agent.py                 # LiveKit agent + Google Realtime integration
├── prompts.py               # Default campaign prompts
├── prompts2.py              # Alt campaign prompts (e.g., SplashBI)
├── prompts3.py              # Alt campaign prompts (e.g., KonfHub)
├── prompts4.py              # Alt campaign prompts (e.g., Zoom Phone)
├── leads.csv                # Leads data (editable)
├── requirements.txt         # Python dependencies
├── webui/
│   ├── app.py               # FastAPI web application (dashboard + browser call)
│   ├── templates/
│   │   ├── index.html       # Dashboard UI
│   │   └── browser_call.html# Browser call UI
│   └── static/              # Static assets
└── README.md                # This file
```

## Voice Options

Available voices for your assistant:
- **Charon** - Deep, authoritative (recommended for professional assistant)
- **Oru** - Mysterious, wise
- **Fenrir** - Strong, powerful
- **Puck** - Default, balanced
- **Zephyr** - Light, gentle
- **Kore** - Female voice
- **Aoede** - Musical, melodic
- **Leda** - Gentle, nurturing

Enjoy your personalized AI assistant! 🚀