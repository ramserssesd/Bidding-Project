from django.core.management.base import BaseCommand
from django.utils import timezone
from auction.models import Product

class Command(BaseCommand):
    help = "Assign winners to products after auction ends"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        products = Product.objects.filter(end_date__lte=now, assigned_to__isnull=True)
        for product in products:
            highest_bid = product.bids.order_by('-amount').first()
            if highest_bid:
                product.assigned_to = highest_bid.user
                product.save()
                self.stdout.write(f"Assigned {product.name} to {highest_bid.user.username}")
            else:
                self.stdout.write(f"No bids for {product.name}")
