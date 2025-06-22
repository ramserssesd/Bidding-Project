from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import BidForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from .models import Bid
from django.db.models import Subquery, OuterRef

@login_required
def product_list(request):
    products = Product.objects.all()
    now = timezone.now()
    
    for product in products:
        if product.end_date < now and product.assigned_to is None:
            highest_bid = product.bids.order_by('-amount').first()
            if highest_bid:
                product.assigned_to = highest_bid.user
                product.save()
   
    max_bid_subquery = Bid.objects.filter(product=OuterRef('product')).order_by('-amount').values('amount')[:1]
    user_bids = Bid.objects.filter(user=request.user, product__assigned_to=request.user,amount=Subquery(max_bid_subquery))
    return render(request, 'auction/product_list.html', {'products': products,'user_bids':user_bids})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = BidForm()
    user_bids = product.bids.filter(user=request.user) if request.user.is_authenticated else None
    if request.method == 'POST':
        if not product.is_active():
            return render(request, 'auction/product_detail.html', {'product': product, 'form': form,'error': 'Bidding time is over!'})

        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.user = request.user
            bid.product = product
            bid.save()
            return redirect('product_detail', pk=pk)

    return render(request, 'auction/product_detail.html', {
        'product': product,
        'form': form,
        'highest_bid': product.bids.first(),
        'user_bids':user_bids,
    })

def user_login(request):
    if request.user.is_authenticated:
        return redirect('product_list')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('product_list')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'auction/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')