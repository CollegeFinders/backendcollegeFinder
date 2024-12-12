from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_otp(otp, student_email):
    send_mail(
        "Your OTP Code",
        f"Your OTP code is {otp}",
        settings.EMAIL_HOST_USER,
        [student_email],
        fail_silently=False,
    )
