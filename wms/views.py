from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from .models import Server

class ServerView(DetailView):
    model = Server

class ServerList(ListView):
    model = Server
