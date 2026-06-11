from django import forms
from .models import User

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_image']
        widgets = {
            'profile_image': forms.FileInput(attrs={'class': 'w-full p-2 bg-gray-700 rounded text-white'}),
        }
