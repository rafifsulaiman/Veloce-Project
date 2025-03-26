from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def katalog(request):
    return render(request, 'katalog.html')