from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from portal.forms import UploadFileForm
from portal.models import LoanApplication, UserProfile
from boxsdk import OAuth2, Client, JWTAuth
from django.views.decorators.csrf import csrf_exempt
import logging, json, time
import random
from datetime import datetime, timedelta
from django.contrib import messages
import portal.creds as c
from django.utils import timezone


#Instantiate Box API client. 
auth = OAuth2(
    client_id='ruaf123v1puenhi42ey8qmfyqwd3r7w4',
    client_secret='XXXXXXXXX',
    access_token='XXXXXXXXX',
)
client = Client(auth)

# Create your views here.
def index(request):
	return render(request, 'index.html')

@login_required(login_url='/login')
def home(request):
    return render(request, 'home.html')
    logging.debug('We are going to load the page for', user)

#direct user to success message page after a succesful upload. 
def success(request):
	return render(request, 'success.html')


#Handle webhooks for completed tasks. Bug in Task Notification Webhooks since new notification service roll-out.
#Using File Preview as a proxy for demo purposes. Can be updated once COLLAB-1190 is resolved.  
@csrf_exempt
def handle_webhook(request):
	logging.debug("Webhook received", request.body)
	jsondata = request.body
	data = json.loads(jsondata)
	file_id = data["source"]["id"]
	logging.debug("we are going to get a record with file id: {0}".format(file_id))
	update_loan_application_status(file_id)

	return HttpResponse(status=200)

#function handles changing the review status and assigning a new task. 
def update_loan_application_status(file):
	record = get_object_or_404(LoanApplication, application_file_id=file)
	#Update Submitted to Pending once a Loan Officer begins review. 
	if record.status == "SUB":
		record.status = "PEND"
		logging.debug('Record Updated to {0}.'.format(record.status))
		record.save()
		create_and_assign_task("Complete initial review of the application", file)
		logging.debug('Record Updated to Pending and Saved')
	#Update Pending Applications to Approved. More detail can be added here once task notifications work.
	#Approve/Reject allows for another step, but not available with FILE.PREVIEW. 
	elif record.status == "PEND":
		logging.debug('Record updated to Approved')
		create_and_assign_task("Approve or reject the application", file)
		record.status = "APP"
		record.save()
	#Update Approved Records to Completed
	elif record.status == "APP":
		record.status = "COMP"
		logging.debug('Record updated to Completed')
		create_and_assign_task("Move application to completed/closed status", file)
		record.save()
	#Exhaustive IF/ELSE to avoid writing to objects when reviewing completed applications. 
	else:
		logging.debug('No record found')
		return



#Primary View for an authenticated users. This view contains the New Application form and the application history.
class HomeView(TemplateView):
	template_name = 'home.html'

#Handle binding the POST request to the form. 
	def post(self, request):
		user = request.user
		#context = self.get_context_data()
		if request.method == 'POST':
			form = UploadFileForm(request.POST, request.FILES)
			logging.debug(request, request.POST, 'now', request.FILES)
			if form.is_valid():
				self.handle_uploaded_file(request.FILES['Application_file'], user)
				logging.debug("This is good")
				messages.success(request, 'File Uploaded')
				return HttpResponseRedirect('/success/')
			else:
				logging.debug("invalid", form.errors)
				messages.error(request, "Error", form.errors)
		else:
			logging.debug("maybe not")
			form = UploadFileForm()
		return render(request, 'home.html', {'form': form})

	#Query list of applications submitted by current_user.
	def get(self, request):
		#Make sure user is authenticated. If not, redirect the user to /login. 
		if request.user.is_authenticated:
			form = UploadFileForm()
			applications = LoanApplication.objects.filter(applicant_id=request.user).order_by('-updated_at')[:10]
			logging.debug("Here are the apps", applications)
			args = {'form': form, 'applications': applications}
			return render(request, self.template_name, args)
		else:
			logging.debug("User not authenticated")
			return HttpResponseRedirect('/login/')


	#Upload the file to Box and create the Loan Application object. 
	def handle_uploaded_file(self, f, user):

		#This file is not being uploaded from disk and requires utilizing the streaming upload option through the Python SDK.
		stream = f
		user_id_number = user.id

		FORMAT='%Y-%m-%dT%H:%M:%S'
		file_name = user.last_name + ", " + user.first_name + " - " + str(datetime.strptime(time.strftime(FORMAT, time.localtime()),FORMAT)) + " - Loan Application.pdf"

		logging.debug("the user is ", user.id, user_id_number)

		#Could be more python-y but does the job for this purpose. Checks for the existence of a user profile.
		#A UserProfile allows us to tie an application user to the folder created for them. 
		if UserProfile.objects.filter(user_id=user.id).count() != 0:
			user_profile = UserProfile.objects.filter(user_id=user.id)[0]
			logging.debug("working with", user_profile)
			subfolder_id = user_profile.box_folder_id
		else:
			subfolder = client.folder('0').create_subfolder(user.last_name + ', ' + user.first_name + " - Applications")
			subfolder_id = subfolder.id
			new_user_profile = UserProfile(user=user, box_folder_id=subfolder.id)
			new_user_profile.save()

		#Begin file upload into folder. 
		new_file = client.folder(subfolder_id).upload_stream(f, file_name)
		logging.debug('File "{0}" uploaded to Box with file ID {1}'.format(new_file.name, new_file.id))
		new_loan = LoanApplication.objects.create(applicant=user, application_file_id=new_file.id)
		logging.debug('Application created with file id {0} and record {1}'.format(new_file.id, new_loan))
		new_loan.save()
		file = client.file(file_id=new_file.id)
		create_and_assign_task("Begin review of new application", new_file.id)
		#Create the webhook with File.Previewed and Task_Assignment.Updated triggers. The handler will be /callback.
		webhook = client.create_webhook(file, ['FILE.PREVIEWED', 'TASK_ASSIGNMENT.UPDATED'], 'https://boa-loan-portal.herokuapp.com/callback/' )
		print('Webhook ID is {0} and the address is {1}'.format(webhook.id, webhook.address))


def create_and_assign_task(message, file):
		
		#Create the task on the file.
		due_at_raw = datetime.now() + timedelta(days=5)
		due_at = due_at_raw.strftime('%Y-%m-%dT%H:00:00+00:00')
		action = "complete"
		task = client.file(file_id=file).create_task(message, due_at)
		print('Task {2} message is {0} and it is due at {1}'.format(task.message, task.due_at, task.id))

		#Assign the task
		user = '10240911034'
		user_object = client.user(user_id=user)
		assignment = client.task(task_id=task.id).assign(user_object)



