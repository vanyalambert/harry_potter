import os
import json
import uuid
import logging
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import time
import google.generativeai as genai

# --- Configuration & Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

MODEL = os.getenv("MODEL", "gemini-2.5-flash-preview-09-2025")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Use mock mode if API key is not set
MOCK_MODE = not GEMINI_API_KEY

# --- LLM and Prompt Logic (Using Gemini API) ---

# Note: The 'speaker' for LLM prompts will be the NPC name (e.g., 'Draco Malfoy')
SYSTEM_INSTRUCTION_BASE = (
    "You are an NPC in a magical-school murder mystery game. Keep replies strictly in-character and conversational. "
    "Your response must be a maximum of 3 sentences. "
    "Do NOT add any explanation outside of the dialogue and the final JSON object. "
    "On the last line of your entire output, output a single JSON object with the following keys and values: "
    "1. 'npc_reply': The text of your reply (DO NOT include the speaker name here). "
    "2. 'mentions': A list of crucial object or suspect names mentioned in your reply (e.g., ['ancient map', 'Professor S']). "
    "3. 'tone': A single word describing your current tone (e.g., 'nervous', 'calm', 'arrogant')."
)

# Configure the Gemini client
llm_model = None
if not MOCK_MODE:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        llm_model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=SYSTEM_INSTRUCTION_BASE
        )
        logging.info(f"Gemini API configured successfully for model: {MODEL}")
    except Exception as e:
        logging.warning(f"Failed to configure Gemini API: {e}. Forcing MOCK_MODE.")
        MOCK_MODE = True
else:
    logging.info("GEMINI_API_KEY not set. Running in MOCK_MODE.")


# --- Backend Utilities and State ---
SESSIONS: Dict[str, Dict] = {}
LOCATIONS = {
    "great hall": {"display": "The Great Hall", "description": "The Great Hall is magnificent as always, with floating candles illuminating the enchanted ceiling. You feel a chill here."},
    "library": {"display": "The Library", "description": "Thousands of dusty books line the shelves. Madam Pince watches you suspiciously."},
    "courtyard": {"display": "The Courtyard", "description": "The open courtyard is cold, with a stone fountain at its center. Students rush to and fro."},
    "dumbledore's office": {"display": "Dumbledore's Office", "description": "A circular room filled with ancient, whirring instruments and the sound of a sleeping phoenix."},
}
NPCS = {
    "professor dumbledore": {"display": "Professor Dumbledore", "avatar": "purple", "persona": "Wise, calm, and slightly detached headmaster. Speaks in a reassuring but enigmatic tone."},
    "draco": {"display": "Draco Malfoy", "avatar": "green", "persona": "Sly, arrogant, and easily panicked. Will deny everything and try to shift blame."},
    "evelyn": {"display": "Evelyn (Fellow Student)", "avatar": "brown", "persona": "A studious and quiet Ravenclaw. Observant but nervous about speaking out."},
}

# --- Pydantic Models ---
class Action(BaseModel):
    session_id: str
    text: str

class Message(BaseModel):
    speaker: str
    text: str
    avatar_type: str

class State(BaseModel):
    location: str
    clues_found: int
    timeline: List[Message]
    evidence: List[str]
    npcs: Dict[str, Dict]

# --- FastAPI App Setup ---
app = FastAPI(title="Hogwarts Mystery Backend")
origins = ["*"] # Be more restrictive in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Game State Management ---
def create_initial_session(player_name: str = "You"):
    sid = str(uuid.uuid4())
    timeline = [
        Message(
            speaker="Professor Dumbledore",
            text="Welcome, young wizard, to Hogwarts School of Witchcraft and Wizardry. A mysterious artifact has gone missing from the castle, and we need your help to find it. Your journey begins here in the Great Hall. What would you like to do?",
            avatar_type="purple"
        ).dict()
    ]
    doc = {
        "session_id": sid,
        "player_name": player_name,
        "location": "great hall",
        "clues_found": 0,
        "timeline": timeline,
        "evidence": [],
        "npcs": {k: v for k, v in NPCS.items()},
        "locations": {k: v for k, v in LOCATIONS.items()},
    }
    SESSIONS[sid] = doc
    return sid, doc

def get_current_state(session: Dict) -> State:
    return State(
        location=session["locations"][session["location"]]["display"],
        clues_found=session["clues_found"],
        timeline=session["timeline"],
        evidence=session["evidence"],
        npcs=session["npcs"],
    )

def add_message(session: Dict, speaker: str, text: str, avatar_type: str):
    session["timeline"].append(Message(speaker=speaker, text=text, avatar_type=avatar_type).dict())


# --- LLM Prompt & Call Functions (FIXED) ---

def build_user_prompt(session: Dict, npc_name: str, player_text: str) -> str:
    """Constructs the USER part of the prompt for the LLM."""
    
    npc_key = None
    for key, npc_data in session["npcs"].items():
        if npc_data.get("display", "").lower() == npc_name.lower():
            npc_key = key
            break
    
    persona = session["npcs"].get(npc_key, {}).get("persona", "A standard Hogwarts student. Respond truthfully but briefly.") if npc_key else "A standard Hogwarts student. Respond truthfully but briefly."
    
    recent_history = "\n".join([
        f"{msg['speaker']}: {msg['text']}" for msg in session["timeline"][-5:]
    ])
    
    evidence_list = "\n- " + "\n- ".join(session["evidence"]) if session["evidence"] else "None."
    
    # This is the prompt that will be sent as the "user" message
    prompt = (
        f"--- CURRENT CONTEXT ---\n"
        f"NPC NAME: {npc_name}\n"
        f"NPC PERSONA: {persona}\n"
        f"PLAYER LOCATION: {session['locations'][session['location']]['display']}\n"
        f"EVIDENCE COLLECTED:\n{evidence_list}\n"
        f"--- CONVERSATION HISTORY (Most Recent) ---\n"
        f"{recent_history}\n\n"
        f"--- PLAYER ACTION ---\n"
        f"PLAYER: {player_text}\n"
        f"NPC REPLY AND JSON METADATA:"
    )
    return prompt

def call_gemini_llm(user_prompt: str) -> str:
    """Calls the Gemini API or returns a mock response."""
    if MOCK_MODE or not llm_model:
        logging.info("Using MOCK_MODE for LLM call.")
        time.sleep(1)
        mock_reply = "I was in the library when I heard the commotion. I didn't see anything unusual, I swear."
        mock_metadata = {"npc_reply": mock_reply, "mentions": ["library"], "tone": "nervous"}
        return json.dumps(mock_metadata)
    
    try:
        logging.info("Calling Gemini API...")
        # Define the generation config to expect a JSON text response
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json" 
        )
        
        response = llm_model.generate_content(
            user_prompt,
            generation_config=generation_config
        )
        
        # The response.text will be the JSON string
        if response.candidates and response.candidates[0].content.parts:
            api_response_text = response.candidates[0].content.parts[0].text
            logging.info("Gemini API call successful.")
            return api_response_text
        else:
            raise Exception("No valid response from API.")
    
    except Exception as e:
        logging.error(f"Gemini API call failed: {e}")
        # Fallback to a mock error message
        return json.dumps({
            "npc_reply": f"(OOC: My AI brain fizzled. I couldn't process that. Error: {e})",
            "mentions": [],
            "tone": "confused"
        })

def parse_llm_response(raw_text: str) -> tuple:
    """Parses the expected JSON metadata from the raw LLM output."""
    try:
        # raw_text is now expected to be a JSON string
        data = json.loads(raw_text)
        reply = data.get("npc_reply", "I can't answer that right now.")
        mentions = data.get("mentions", [])
        tone = data.get("tone", "neutral")
        return reply, mentions, tone
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse LLM JSON response: {e}")
        logging.error(f"Raw text was: {raw_text}")
        return f"(OOC: My AI brain malfunctioned and returned invalid JSON: {raw_text})", [], "confused"

# --- Deterministic Action Parser ---
def handle_deterministic_action(session: Dict, player_action: str) -> Optional[Message]:
    action = player_action.lower().strip()
    
    # 1. GO TO [LOCATION]
    if action.startswith("go to "):
        target_loc = action[6:].strip()
        for key, loc in LOCATIONS.items():
            if key in target_loc:
                if session["location"] == key:
                    return Message(speaker="Narrator", text=f"You are already in {loc['display']}.", avatar_type="brown")
                
                session["location"] = key
                add_message(session, "Narrator", f"You travel to **{loc['display']}**.", "brown")
                return Message(speaker="Narrator", text=loc["description"], avatar_type="brown")
        return Message(speaker="Narrator", text=f"You can't seem to find a path to '{target_loc}'. Try a common Hogwarts location.", avatar_type="brown")
    
    # 2. INSPECT / EXAMINE [OBJECT] (Simple Clue Logic)
    if action.startswith("inspect ") or action.startswith("examine "):
        item = action.split(maxsplit=1)[1].strip()
        
        if item == "shimmer" and session["location"] == "great hall":
            new_clue = "The magical trace of the missing artifact."
            if new_clue not in session["evidence"]:
                session["evidence"].append(new_clue)
                session["clues_found"] += 1
                return Message(speaker="Narrator", text=f"As you examine the area, you discover a peculiar shimmer! It leaves behind a magical trace—a new clue: **{new_clue}**.", avatar_type="brown")
            else:
                return Message(speaker="Narrator", text="You've already inspected the shimmer. It seems to point toward the library, but you have nothing new to learn here.", avatar_type="brown")
        
        return Message(speaker="Narrator", text=f"You carefully inspect the **{item}**. You find nothing out of the ordinary, but you feel like you should be looking for something else...", avatar_type="brown")
    
    return None

# --- API Endpoints ---
@app.post("/session/start")
def start_game_session():
    sid, doc = create_initial_session()
    return {"session_id": sid, "state": get_current_state(doc).dict()}

@app.post("/session/action")
def process_player_action(action: Action):
    sid = action.session_id
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    session = SESSIONS[sid]
    player_text = action.text
    player_name = session.get("player_name", "You")
    
    add_message(session, player_name, player_text, "blue")
    
    deterministic_reply = handle_deterministic_action(session, player_text)
    if deterministic_reply:
        return {"reply": [deterministic_reply.dict()], "state": get_current_state(session).dict()}
    
    target_npc_name = None
    matched_npc_key = None
    for npc_key, npc_data in NPCS.items():
        if npc_key in player_text.lower():
            target_npc_name = npc_data["display"]
            matched_npc_key = npc_key
            break
    
    if target_npc_name:
        # Build prompt and call LLM
        user_prompt = build_user_prompt(session, target_npc_name, player_text)
        
        try:
            llm_raw_json = call_gemini_llm(user_prompt)
            npc_reply, mentions, tone = parse_llm_response(llm_raw_json)
            
            npc_avatar = NPCS.get(matched_npc_key, {}).get("avatar", "green")
            add_message(session, target_npc_name, npc_reply, npc_avatar)
            
            for m in mentions:
                if m not in session["evidence"]:
                    session["evidence"].append(m)
                    session["clues_found"] += 1
            
            return {"reply": [Message(speaker=target_npc_name, text=npc_reply, avatar_type=npc_avatar).dict()], "state": get_current_state(session).dict()}
        
        except Exception as e:
            logging.error(f"Error in process_player_action: {e}")
            return {"reply": [Message(speaker="System Error", text=f"An unexpected error occurred: {e}", avatar_type="purple").dict()], "state": get_current_state(session).dict()}
    
    fallback_message = f"You try to execute the action, but it doesn't seem to have a clear effect. Try 'go to [location]', 'inspect [item]', or 'talk to [NPC]'."
    add_message(session, "Narrator", fallback_message, "brown")
    return {"reply": [Message(speaker="Narrator", text=fallback_message, avatar_type="brown").dict()], "state": get_current_state(session).dict()}

@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "Hogwarts Mystery Backend API", "status": "running", "mock_mode": MOCK_MODE}