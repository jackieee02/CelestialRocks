from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Drink, Category, Ingredient, Seat, DrinkProposal

class BartenderForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'bartender'
        if commit:
            user.save()
        return user

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

class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class DrinkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Choose Category"

    class Meta:
        model = Drink
        fields = ['name', 'category', 'price', 'image', 'is_available']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'stock_level', 'low_stock_threshold', 'image']

class EditBartenderForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-white'}),
        }

class SeatForm(forms.ModelForm):
    class Meta:
        model = Seat
        fields = ['seat_number', 'is_active', 'seat_type', 'x_coord', 'y_coord']

class DrinkProposalForm(forms.ModelForm):
    class Meta:
        model = DrinkProposal
        fields = ['name', 'ingredients', 'suggested_price']
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 3}),
        }
