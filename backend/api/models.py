from django.db import models

class MarketSubscriber(models.Model):
    REPORT_CHOICES = [
        ('weekly', 'Weekly Market Intelligence (Masabata Onse)'),
        ('monthly', 'Monthly Strategic Bulletin (Mwezi Uliwonse)'),
        ('both', 'Both Weekly & Monthly Reports (Masabata ndi Miyezi)'),
    ]

    ORG_CHOICES = [
        ('farmer', 'Farmer (Mlimi)'),
        ('trader', 'Trader (Wamalonda / Wogulitsa)'),
    ]

    full_name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    pin = models.CharField(max_length=128, default='1234')
    reset_code = models.CharField(max_length=10, blank=True, null=True)
    reset_code_expires = models.DateTimeField(blank=True, null=True)
    district = models.CharField(max_length=100, default='Lilongwe')
    organization_type = models.CharField(max_length=50, choices=ORG_CHOICES, default='farmer')
    report_frequency = models.CharField(max_length=50, choices=REPORT_CHOICES, default='weekly')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_report_sent = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.district} [{self.report_frequency}]"
