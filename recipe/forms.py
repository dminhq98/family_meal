from django import forms
import re
from recipe.models import User
from django.contrib.auth.forms import PasswordChangeForm

class RegistrationForm(forms.Form):
    username = forms.CharField(label='User name')
    name = forms.CharField(label='Full name')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput())
    address = forms.CharField(label='Address')
    birthday = forms.DateTimeField(label='Birth Day', widget=forms.DateInput(attrs={'type': 'date'}))

    def clean_password2(self):
        if 'password1' in self.cleaned_data:
            password1 = self.cleaned_data['password1']
            password2 = self.cleaned_data['password2']
            if password1 == password2 and password1:
                return password2
        raise forms.ValidationError("Invalid password")

    def clean_user_name(self):
        username = self.cleaned_data['username']
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError("The account name has special characters")
        try:
            User.objects.get(user_name=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("Account already exists")

    def save(self):
        user = User()
        user.username = self.cleaned_data['username']
        user.name = self.cleaned_data['name']
        user.address = self.cleaned_data['address']
        user.birthday = self.cleaned_data['birthday']
        user.set_password(self.cleaned_data['password1'])
        user.level = 2
        user.save()

# class PassForm(PasswordChangeForm):

