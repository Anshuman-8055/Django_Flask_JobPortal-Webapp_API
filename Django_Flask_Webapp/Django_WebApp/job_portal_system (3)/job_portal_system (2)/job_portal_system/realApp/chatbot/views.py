import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

@csrf_exempt
def chat_with_gemini(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message', '')

        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        payload = {
            "prompt": {
                "text": user_input
            }
        }

        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
        try:
            gemini_reply = response.json()['candidates'][0]['output']
        except (KeyError, IndexError, json.JSONDecodeError):
            gemini_reply = "Sorry, I couldn't process that."

        return JsonResponse({"reply": gemini_reply})
    return JsonResponse({"error": "Invalid request"}, status=400)
