from django.db import models
from .manager import UserManager
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.hashers import make_password



class Location(models.Model):
    location_name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.location_name


class CustomUser(AbstractBaseUser):

    email = models.EmailField(unique=True)

    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_college = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    def save(self, *args, **kwargs):

        # Hash the password before saving
        if self.password and not self.password.startswith(
            ("pbkdf2_sha256$", "bcrypt", "sha1", "md5")
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    objects = UserManager()

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def __str__(self):
        return self.email


class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    student_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, null=True)
    otp_expiry = models.DateTimeField(null=True)

    def __str__(self):
        return self.student_name


class Course(models.Model):
    course_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.course_name


class College(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    college_name = models.CharField(max_length=200)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name="courses")
    is_approved = models.BooleanField(default=False)
    approval_request_sent = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.college_name
    

class AppliedStudents(models.Model):
    student_id = models.ForeignKey(Student,on_delete=models.CASCADE)
    college_id = models.ForeignKey(College,on_delete=models.CASCADE)



