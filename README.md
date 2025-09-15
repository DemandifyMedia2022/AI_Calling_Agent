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
   ```

2. **Environment Variables**:
   Create a `.env` file with your LiveKit credentials:
   ```
   LIVEKIT_API_KEY=your_api_key_here
   LIVEKIT_API_SECRET=your_api_secret_here
   LIVEKIT_URL=your_livekit_url_here
   ```

3. **Run the Application**:
   ```bash
   python app.py
   python .\agent.py console 
   python .\agent.py dev
   ```

4. **Access the Interface**:
   Open your browser and go to: `http://localhost:5000`

## Usage

- Type your messages in the chat input
- Press Enter or click the send button
- Athena will respond with helpful assistance
- The interface includes typing indicators and smooth animations

## Customization

- **Character**: Modify `prompts.py` to change Athena's personality
- **Voice**: Update the voice in `agent.py` (available: Puck, Charon, Kore, Fenrir, Aoede, Leda, Oru, Zephyr)
- **UI**: Customize the interface in `templates/index.html`

## Files Structure

```
├── app.py              # Flask web application
├── agent.py            # LiveKit agent configuration
├── prompts.py          # AI assistant personality
├── tools.py            # Available tools/functions
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Web interface
└── README.md           # This file
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