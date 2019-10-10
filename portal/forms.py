from django import forms

class UploadFileForm(forms.Form):
	# first_name = forms.CharField(max_length=24)
	# last_name = forms.CharField(max_length=36)
	Application_file = forms.FileField()