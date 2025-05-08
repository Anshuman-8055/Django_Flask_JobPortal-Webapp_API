from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from .models import Job, SavedJobs, JobApplication
from .forms import JobForm
from users.forms import CustomUserCreationForm


# Auth: Register
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


# Auth: Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            if hasattr(user, 'user_type') and user.user_type == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


# Auth: Logout
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')




# Admin Dashboard - View All Applications
@login_required
def admin_dashboard(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'admin':
        return HttpResponseForbidden("You are not authorized to view this page.")
    orders = JobApplication.objects.all().order_by('-applied_at')
    return render(request, 'admin_dashboard.html', {'orders': orders})


def jobs_list(request):
    page = request.GET.get("page", 1)
    jobs = Job.objects.all().order_by('-pub_date')
    paginator = Paginator(jobs, 5)  # Adjust per scroll load

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        jobs_page = paginator.get_page(page)
        html = render_to_string('partials/job_cards.html', {'jobs': jobs_page}, request=request)
        return JsonResponse({'html': html})

    jobs_page = paginator.get_page(1)
    return render(request, 'job_listing.html', {'jobs': jobs_page})

# User Dashboard - List All Jobs
@login_required
def dashboard(request):
    jobs = Job.objects.all()
    categories = Job.CATEGORY_CHOICES
    return render(request, 'product.html', {'jobs': jobs, 'category_choices': categories})


# Public Job Listings (Homepage)
def shop(request):
    jobs = Job.objects.all()
    categories = Job.CATEGORY_CHOICES
    return render(request, 'shop.html', {'jobs': jobs, 'category_choices': categories})


# Job Detail Page
def jobs_detail(request, job_id):
    job = get_object_or_404(Job, job_id=job_id)
    return render(request, 'product_detail.html', {'job': job})

def load_more_jobs(request):
    page = request.GET.get("page")
    jobs = Job.objects.all()
    paginator = Paginator(jobs, 10)  # load 10 jobs at a time
    try:
        jobs_page = paginator.page(page)
    except:
        return JsonResponse({'jobs_html': '', 'has_next': False})
    
    return JsonResponse({
        'jobs_html': render_to_string('partials/job_cards.html', {'jobs': jobs_page}),
        'has_next': jobs_page.has_next()
    })

def chat_page(request):
    return render(request, 'chatbot/index.html')



# All Jobs Page
def jobs(request):
    jobs = Job.objects.all()
    return render(request, 'jobs.html', {'jobs': jobs})


# Admin View - Manage All Applications
@login_required
def manage_orders(request):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can manage applications.")
    
    orders = JobApplication.objects.all().order_by('-applied_at')
    return render(request, 'manage_orders.html', {
        'orders': orders,
        'status_choices': JobApplication.STATUS_CHOICES,
    })


# Admin: Add a New Job
@login_required
def add_job(request):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can post jobs.")
    
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Job posted successfully!")
            return redirect('dashboard')
    else:
        form = JobForm()
    return render(request, 'add_product.html', {'form': form})




# Save Job to Cart
@login_required
def add_to_cart(request, job_id):
    job = get_object_or_404(Job, job_id=job_id)
    cart, _ = SavedJobs.objects.get_or_create(user=request.user)
    cart.jobs.add(job)
    messages.success(request, f"{job.job_title} added to your saved jobs.")
    return redirect('dashboard')


# View Saved Jobs (Cart)
@login_required
def view_cart(request):
    cart, _ = SavedJobs.objects.get_or_create(user=request.user)
    print(cart.jobs.all())  # Optional: for debug
    return render(request, 'cart.html', {'cart': cart})


# Remove Job from Saved
@login_required
def remove_from_cart(request, job_id):
    cart = get_object_or_404(SavedJobs, user=request.user)
    job = get_object_or_404(Job, job_id=job_id)
    cart.jobs.remove(job)
    messages.success(request, f"{job.job_title} removed from saved jobs.")
    return redirect('view_cart')


# Apply to All Saved Jobs (Cart → Applications)
@login_required
def place_order(request):
    cart = get_object_or_404(SavedJobs, user=request.user)
    if cart.jobs.exists():
        for job in cart.jobs.all():
            JobApplication.objects.get_or_create(user=request.user, job=job)
        cart.jobs.clear()
        messages.success(request, "You have successfully applied to selected jobs!")
        return redirect('order_list')
    else:
        messages.warning(request, "You haven't saved any jobs!")
        return redirect('dashboard')


# User View - My Applications
@login_required
def order_list(request):
    orders = JobApplication.objects.filter(user=request.user).order_by('-applied_at')
    return render(request, 'order_list.html', {'orders': orders})


# Admin Action - Update Application Status
@require_POST
@login_required
def update_order_status(request, order_id):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can update job application status.")
    
    order = get_object_or_404(JobApplication, id=order_id)
    new_status = request.POST.get('status')
    if new_status in dict(JobApplication.STATUS_CHOICES):
        order.status = new_status
        order.save()
        messages.success(request, f"Application #{order.id} status updated to {new_status}.")
    else:
        messages.error(request, "Invalid status value.")
    return HttpResponseRedirect(reverse('manage_orders'))


# Filter Jobs by Category
def category_filter(request, category_slug):
    filtered_jobs = Job.objects.filter(category=category_slug)
    categories = Job.CATEGORY_CHOICES
    return render(request, 'category_jobs.html', {
        'jobs': filtered_jobs,
        'category_name': dict(Job.CATEGORY_CHOICES).get(category_slug, category_slug),
        'category_choices': categories,
    })


# List jobs for admin
@login_required
def admin_job_list(request):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can manage jobs.")
    
    jobs = Job.objects.all().order_by('-pub_date')
    return render(request, 'admin_jobs.html', {'jobs': jobs})


@login_required
def edit_job(request, job_id):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can edit jobs.")

    job = get_object_or_404(Job, job_id=job_id)

    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"{job.job_title} has been updated.")
            return redirect('admin_job_list')
    else:
        form = JobForm(instance=job)

    return render(request, 'edit_job.html', {'form': form, 'job': job})


@login_required
def delete_job(request, job_id):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can delete jobs.")

    job = get_object_or_404(Job, job_id=job_id)

    if request.method == 'POST':
        job_title = job.job_title
        job.delete()
        messages.success(request, f"{job_title} was deleted successfully.")
        return redirect('admin_job_list')

    return render(request, 'confirm_delete.html', {'job': job})


@login_required
def admin_user_list(request):
    if request.user.user_type != 'admin':
        return HttpResponseForbidden("Only admins can access this page.")
    
    User = get_user_model()
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_user_list.html', {'users': users})