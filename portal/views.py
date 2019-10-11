from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from portal.forms import UploadFileForm
from portal.models import LoanApplication, UserProfile
from boxsdk import OAuth2, Client, JWTAuth
from django.views.decorators.csrf import csrf_exempt
import logging, json
import random
from django.contrib import messages
import portal.creds as c
from django.utils import timezone

# Create your views here.
def index(request):
	return render(request, 'index.html')

@login_required
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
	update_loan_application_status(file_id)

	return HttpResponse(status=200)

def update_loan_application_status(file):
	record = LoanApplication.objects.filter(application_file_id=file)[0]
	#Update Submitted to Pending once a Loan Officer begins review. 
	if record.status == "SUB":
		record.status == "PEND"
		record.save()
	#Update Pending Applications to Approved. More detail can be added here once task notifications work.
	#Approve/Reject allows for another step, but not available with FILE.PREVIEW. 
	elif record.status == "PEND":
		record.status == "APP"
		record.save()
	#Update Approved Records to Completed
	elif record.status == "APP":
		record.status == "COMP"
		record.save()
	#Exhaustive IF/ELSE to avoid writing to objects when reviewing completed applications. 
	else:
		return



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
				logging.debug("This is good", form)
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
		form = UploadFileForm()
		#self.create_box_app_user(request.user)
		applications = LoanApplication.objects.filter(applicant_id=request.user).order_by('-updated_at')[:10]
		logging.debug("Here are the apps", applications)
		args = {'form': form, 'applications': applications}
		return render(request, self.template_name, args)


	#Upload the file to Box and create the Loan Application object. 
	def handle_uploaded_file(self, f, user):

		auth = OAuth2(
		    client_id='ruaf123v1puenhi42ey8qmfyqwd3r7w4',
		    client_secret='Xc4EMVxss7DStL7CHqO74zKcYgJkfB84',
		    access_token='IuRR76pEg4BkhjBH19YMa175YSMBd7gv',
		)
		client = Client(auth)
		stream = f
		user_id_number = user.id

		file_name = user.last_name + ", " + user.first_name + " - " + str(timezone.now()) + " - Loan Application.pdf"

		logging.debug("the user is ", user.id, user_id_number )

		if UserProfile.objects.filter(user_id=user.id).count() != 0:
			user_profile = UserProfile.objects.filter(user_id=user.id)[0]
			logging.debug("working with", user_profile)
			subfolder_id = user_profile.box_folder_id
		else:
			subfolder = client.folder('0').create_subfolder('My Stuff' + str(random.randint(1,100001)))
			subfolder_id = subfolder.id
			new_user_profile = UserProfile(user=user, box_folder_id=subfolder.id)
			new_user_profile.save()

		
		new_file = client.folder(subfolder_id).upload_stream(f, file_name)
		logging.debug('File "{0}" uploaded to Box with file ID {1}'.format(new_file.name, new_file.id))
		new_loan = LoanApplication(applicant=user, application_file_id = new_file.id)
		new_loan.save()
		file = client.file(file_id=new_file.id)
		#https://enk477phc85mn.x.pipedream.net
		#https://boa-loan-portal.herokuapp.com/callback/'
		webhook = client.create_webhook(file, ['FILE.PREVIEWED', 'TASK_ASSIGNMENT.UPDATED'], 'https://boa-loan-portal.herokuapp.com/callback/' )
		print('Webhook ID is {0} and the address is {1}'.format(webhook.id, webhook.address))

	# def create_box_app_user(self, user):
	# 	sdk = JWTAuth(client_id=c.clientID,
	# 	    client_secret=c.clientSecret,
	# 	    enterprise_id=c.enterpriseID,
	# 	    jwt_key_id=c.jwtKeyID,
	# 	    rsa_private_key_file_sys_path='private.pem',
	# 	    rsa_private_key_passphrase=c.rsaPrivateKeyPassphrase)
	# 	#access_token = auth.authenticate_instance()
	# 	client = Client(sdk)
	# 	new_user = client.create_user(user.first_name + " " + user.last_name)
	# 	logging.debug("New user created: ", new_user, type(new_user))


	# def get_loan_applications(self, **kwargs):
	# 	form = UploadFileForm()
	# 	applications = LoanApplications.objects.all()
	# 	logging.debug(applications)
	# 	return render(request, 'home.html', {'form': form})


