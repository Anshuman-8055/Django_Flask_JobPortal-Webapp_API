from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from MainApp.models import Job, SavedJobs, JobApplication
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'users/profile.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Username Entered: {username}")
        print(f"Password Entered: {password}")

        user = authenticate(request, username=username, password=password)
        print(f"Authenticated User: {user}")

        if user is not None:
            login(request, user)
            messages.success(request, "Login Successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html')

@login_required
def dashboard(request):
    recipes = Recipe.objects.all()
    return render(request, 'users/dashboard.html', {'recipes': recipes})

def user_logout(request):
    logout(request)
    return redirect('home')