from django.shortcuts import redirect
from django.urls import reverse

class AgeVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = [reverse('age_verify'), reverse('access_denied'), '/static/']
        if not request.session.get('is_of_age') and request.path not in allowed_paths:
            return redirect(reverse('age_verify'))
        
        return self.get_response(request)
