from django import forms
from .models import User

class BartenderProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
            'profile_image': forms.FileInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
        }
