from django import forms

class ExogenousOrderForm(forms.Form):
    files = forms.FileField(label='Upload exogenous order flow configuration', 
        widget=forms.ClearableFileInput(attrs={'multiple': True}), max_length=100)

class CustomConfigForm(forms.Form):
    files = forms.FileField(label='Upload your session configuration')
