"""LoanPortal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from portal import views as portal_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', include('portal.urls')),
    #path('accounts/', include('django_registration.backends.one_step.urls')),
    path('', include('django.contrib.auth.urls')),
    path('accounts/home/', portal_views.HomeView.as_view(), name='post'),
    path('success/', portal_views.success),
    path('callback/', portal_views.handle_webhook),

    # path('accounts/home/', portal_views.upload_file, name='upload_file')
    #path('login/$','django.contrib.auth.views.login', {'template_name': '/index.html'}),
    # path('accounts/register/',
    #     RegistrationView.as_view(success_url='home/'),
    #     name='django_registration_register'),
    #path('accounts/', include('registration.backends.simple.urls')),

]

# urlpatterns = patterns('',
# 	url(r'^$', 'portals.views.index', name='home'),
# 	url(r'^admin', include(admin.site.urls)),
# )

