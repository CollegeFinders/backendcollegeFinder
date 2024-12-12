from django.contrib import admin
from .models import *

admin.site.register(CustomUser)
admin.site.register(Student)
admin.site.register(Location)
admin.site.register(Course)
admin.site.register(College)
admin.site.register(AppliedStudents)
