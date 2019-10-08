from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from portal.forms import UploadFileForm
from portal.models import LoanApplication
from boxsdk import OAuth2, Client
import logging
from django.contrib import messages
import random

# Create your views here.
def index(request):
	return render(request, 'index.html')

@login_required
def home(request):
    return render(request, 'home.html')
    logging.debug('We are going to load the page for', user)

def upload_file(request):
	user = request.user
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		logging.debug(request, request.POST, 'now', request.FILES)
		if form.is_valid():
			handle_uploaded_file(request.FILES['file'], user)
			logging.debug("This is good", form)
			return HttpResponseRedirect('/success/url')
		else:
			logging.debug("invalid", form.errors)
			messages.error(request, "Error", form.errors)
	else:
		logging.debug("maybe not")
		form = UploadFileForm()
	return render(request, 'home.html', {'form': form})

def handle_uploaded_file(f, user):

	auth = OAuth2(
	    client_id='ruaf123v1puenhi42ey8qmfyqwd3r7w4',
	    client_secret='Xc4EMVxss7DStL7CHqO74zKcYgJkfB84',
	    access_token='dE5kSQabzIoRIOLrVpNiVLHa0CAwNUXZ',
	)
	client = Client(auth)
	stream = f


	file_name = user.last_name + ", " + user.first_name + " Loan Application.pdf"
	subfolder = client.folder('0').create_subfolder('My Stuff' + str(random.randint(1,100001)))
	folder_id = subfolder.id
	new_file = client.folder(folder_id).upload_stream(f, file_name)
	logging.debug('File "{0}" uploaded to Box with file ID {1}'.format(new_file.name, new_file.id)) 
	new_loan = LoanApplication(applicant=user, application_file_id = new_file.id)
	new_loan.save()
