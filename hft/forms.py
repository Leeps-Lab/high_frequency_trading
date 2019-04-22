from django import forms

class ExogenousEventForm(forms.Form):
    files = forms.FileField(label='Upload configuration', 
        widget=forms.ClearableFileInput(attrs={'multiple': True}), max_length=100)

class CustomConfigForm(forms.Form):
    files = forms.FileField(label='Upload your session configuration')
