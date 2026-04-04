"""
Chatbot Views — API endpoint for the Nexus Banking AI Assistant.
"""
import json

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from .services import get_chatbot_response


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(LoginRequiredMixin, View):
    """
    POST /chat/
    Body: { "message": "..." }
    Response: { "reply": "..." }
    """

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            message = body.get('message', '').strip()
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse(
                {'reply': 'Invalid request format. Send JSON with a "message" field.'},
                status=400
            )

        if not message:
            return JsonResponse(
                {'reply': 'Please type a message! I\'m here to help. 😊'},
                status=200
            )

        reply = get_chatbot_response(message, request.user)
        return JsonResponse({'reply': reply}, status=200)

    def handle_no_permission(self):
        """Return JSON response for unauthenticated users instead of redirect."""
        return JsonResponse(
            {'reply': '🔒 Please log in to use the banking assistant.'},
            status=401
        )
