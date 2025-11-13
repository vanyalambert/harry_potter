# 🧙 The Hogwarts Mystery - Interactive Text Adventure Game

An immersive, AI-powered interactive mystery game set in the magical world of Hogwarts. Players explore the castle, question suspects, and uncover clues through natural language dialogue powered by Large Language Models.

## Features

- **Dynamic Dialogue System**: AI-generated responses from NPCs based on player interactions
- **Deterministic Actions**: Navigate locations (`go to library`), inspect objects (`inspect shimmer`)
- **State Tracking**: Persistent game sessions with evidence collection and clue tracking
- **Beautiful UI**: Immersive Hogwarts-themed interface with magical styling
- **Mock Mode**: Test the game without an API key using built-in mock responses

## Project Structure

```
Harry_Potter/
├── backend/
│   ├── app.py          # FastAPI backend server
│   └── .env            # Environment variables (create this)
├── hogwarts-mystery-game.html
├── styles.css          # Game styling
├── app.js              # Frontend JavaScript
├── requirements.txt    # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser

### Step 1: Set Up Backend

1. **Create and activate a virtual environment** (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:

The `.env` file should already exist in the `backend/` directory. If not, create it:

```bash
# In backend/.env
MODEL=gemini-2.5-flash-preview-09-2025
PORT=8000
GEMINI_API_KEY=  # Leave empty for mock mode, or add your key here
```

4. **Start the FastAPI server**:

```bash
uvicorn backend.app:app --reload --port 8000
```

You should see output indicating the server is running on `http://127.0.0.1:8000`.

### Step 2: Serve the Frontend

Open a **new terminal window** and navigate to the project directory.

**Option 1: Using Python's built-in server** (recommended):

```bash
python3 -m http.server 3000
```

**Option 2: Using Node.js http-server** (if you have Node.js):

```bash
npx http-server -p 3000
```

**Option 3: Open directly in browser** (may have CORS issues):

Simply open `hogwarts-mystery-game.html` in your browser.

### Step 3: Play the Game

1. Navigate to `http://localhost:3000` (or the port you chose) in your browser
2. The game will automatically start a new session
3. Try commands like:
   - `go to library`
   - `inspect shimmer`
   - `talk to draco`
   - `ask evelyn about the artifact`

## Game Commands

### Deterministic Actions

- **Movement**: `go to [location]`
  - Examples: `go to library`, `go to courtyard`, `go to dumbledore's office`
  
- **Inspection**: `inspect [object]` or `examine [object]`
  - Examples: `inspect shimmer`, `examine the books`

### Dialogue Actions

- **Talk to NPCs**: `talk to [npc]`, `ask [npc] [question]`, `speak with [npc]`
  - Examples: 
    - `talk to draco`
    - `ask evelyn where she was during the feast`
    - `speak with professor dumbledore`

## Configuration

### Mock Mode vs. Real LLM

The backend runs in **MOCK_MODE** by default (when `GEMINI_API_KEY` is empty). This allows you to test the game without an API key.

To use the real Gemini API:
1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to `backend/.env`:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Restart the backend server

### Adding New Locations

Edit `backend/app.py` and add to the `LOCATIONS` dictionary:

```python
LOCATIONS = {
    "your location": {
        "display": "Display Name",
        "description": "Description shown when player arrives"
    },
    # ... existing locations
}
```

### Adding New NPCs

Edit `backend/app.py` and add to the `NPCS` dictionary:

```python
NPCS = {
    "npc key": {
        "display": "NPC Name",
        "avatar": "purple",  # purple, blue, brown, green
        "persona": "Detailed persona description for the LLM"
    },
    # ... existing NPCs
}
```

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:
- Make sure you're serving the frontend through a web server (not opening the HTML file directly)
- Check that the backend is running and accessible at `http://127.0.0.1:8000`

### Backend Not Starting

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that port 8000 is not already in use
- Verify your Python version: `python3 --version` (should be 3.8+)

### Frontend Can't Connect to Backend

- Verify the backend is running: visit `http://127.0.0.1:8000` in your browser (should see a JSON response)
- Check the `BACKEND_URL` in `app.js` matches your backend URL
- Look for errors in the browser console (F12 → Console tab)

## API Endpoints

### `POST /session/start`
Creates a new game session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "state": {
    "location": "The Great Hall",
    "clues_found": 0,
    "timeline": [...],
    "evidence": [],
    "npcs": {...}
  }
}
```

### `POST /session/action`
Processes a player action.

**Request:**
```json
{
  "session_id": "uuid-string",
  "text": "go to library"
}
```

**Response:**
```json
{
  "reply": [
    {
      "speaker": "Narrator",
      "text": "You travel to **The Library**.",
      "avatar_type": "brown"
    }
  ],
  "state": {...}
}
```

## Customization

### Changing Colors

Edit `styles.css` to customize the color scheme. Key color variables:
- `#ffd700` - Gold (primary accent)
- `#b8860b` - Dark goldenrod (borders)
- `#1a1a2e` - Dark blue (background)
- `#8b4513` - Saddle brown (buttons)

### Modifying Prompts

Edit the `SYSTEM_INSTRUCTION_BASE` and `build_llm_prompt()` function in `backend/app.py` to change how NPCs respond.

## Future Enhancements

- [ ] Persistent database storage (MongoDB/Firestore)
- [ ] RAG integration for contextual evidence retrieval
- [ ] More locations and NPCs
- [ ] Contradiction detection system
- [ ] Endgame accusation mechanics
- [ ] Fine-tuned LLM models on HPAC dataset

## License

This project is for educational purposes.

## 👥 Team

Built as part of an interactive text mystery game project.

---

**Enjoy your magical adventure at Hogwarts!** ⚡🧙‍♂️

