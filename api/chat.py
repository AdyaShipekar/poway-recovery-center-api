""" Support assistant API: forwards the site chatbot conversation to Google Gemini.

The Gemini key lives only in .env (GEMINI_API_KEY) so it is never exposed in the GitHub Pages frontend.
"""
import json
import urllib.error
import urllib.request

from flask import Blueprint, request, current_app
from flask_restful import Api, Resource


chat_api = Blueprint('chat_api', __name__, url_prefix='/api')
api = Api(chat_api)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_MESSAGES = 20
MAX_MESSAGE_CHARS = 1000

SYSTEM_PROMPT = """You are the support assistant on the Poway Recovery Center website, a compassionate,
trauma-informed peer recovery and mental-health community in Poway, California.

- Be warm, calm, non-judgmental, and brief (2-5 short sentences). Write plain text, no markdown.
- Offer practical grounding, coping, and next-step ideas, and point people to the site's pages when helpful:
  Resources (Mood Room, reflection wall, resource directory), Programs (community meetings, wellness
  workshops, care connections, meeting schedule), and About Us.
- You are not a therapist, doctor, or crisis service. Do not diagnose, and do not give medication or dosing
  advice; encourage contacting a medical professional for medical concerns such as severe withdrawal.
- If someone mentions suicide, self-harm, overdose, being in danger, or harming others, respond with care and
  clearly encourage them to call or text 988 (Suicide & Crisis Lifeline) right now, or call 911 if they are in
  immediate danger.
"""

CRISIS_REPLY = ("I want to make sure you get the right support. If you are thinking about harming yourself "
                "or are in crisis, please call or text 988 now, or call 911 if you are in immediate danger.")


class _Chat(Resource):
    def post(self):
        api_key = current_app.config['GEMINI_API_KEY']
        if not api_key:
            return {"message": "The support assistant is not configured: set GEMINI_API_KEY in .env"}, 503

        body = request.get_json(silent=True) or {}
        messages = body.get('messages')
        if not isinstance(messages, list) or not messages:
            return {"message": "messages must be a non-empty list"}, 400

        contents = []
        for message in messages[-MAX_MESSAGES:]:
            if not isinstance(message, dict):
                return {"message": "Each message needs a role and text"}, 400
            role = 'model' if message.get('role') == 'model' else 'user'
            text = str(message.get('text') or '').strip()[:MAX_MESSAGE_CHARS]
            if text:
                contents.append({"role": role, "parts": [{"text": text}]})
        # Gemini expects the conversation to start with the user
        while contents and contents[0]["role"] != 'user':
            contents.pop(0)
        if not contents:
            return {"message": "messages must include text from the user"}, 400

        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400},
        }
        url = GEMINI_URL.format(model=current_app.config['GEMINI_MODEL'])
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as error:
            detail = error.read().decode('utf-8', 'replace')
            current_app.logger.error(f"Gemini error {error.code}: {detail}")
            return {"message": f"The support assistant is unavailable (Gemini error {error.code})."}, 502
        except (urllib.error.URLError, TimeoutError) as error:
            current_app.logger.error(f"Gemini unreachable: {error}")
            return {"message": "The support assistant could not reach Gemini."}, 502

        candidates = data.get('candidates') or []
        parts = (candidates[0].get('content') or {}).get('parts', []) if candidates else []
        reply = ''.join(part.get('text', '') for part in parts).strip()
        # Empty when Gemini's safety filters block the reply; still point the person to real help
        return {"reply": reply or CRISIS_REPLY}


api.add_resource(_Chat, '/chat')
