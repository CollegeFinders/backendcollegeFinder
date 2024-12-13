from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('refresh/',TokenRefreshView.as_view()),
    path("student_reg/", StudentRegView.as_view()),
    path("college_reg/", CollegeRegView.as_view()),
    path("login/", LoginView.as_view()),
    path("verify_otp/", VerifyOtpView.as_view()),
    path("admin_reg/", AdminRegView.as_view()),
    path("location_reg/", LocationRegView.as_view()),
    path("course_reg/", CourseRegView.as_view()),
    path("admin_approval/", AdminCollegeApprovalView.as_view()),
    path("colleges_list/", CollegeListView.as_view()),
    path("courses_list/", CourseListView.as_view()),
    path("student_update/", StudentProfileUpdateView.as_view()),
    path("college_update/", CollegeProfileUpdateView.as_view()),
    path("college_details/<int:college_id>/", CollegeDetailsView.as_view()),
    path("search/", SearchView.as_view()),
    path("location_list/", LocationListView.as_view()),
    path(
        "location_based_college_list/<int:location_id>/",
        LocationBasedCollegeListView.as_view(),
    ),
    path("apply/", ApplyToCollegeView.as_view()),
    path("applied_students/<int:college_id>", AppliedStudentsView.as_view()),
    path("students_details/<int:student_id>", StudentDetailsView.as_view()),
    path("students_list/", StudentListView.as_view()),
    path("applied_colleges/<int:student_id>", AppliedCollegeView.as_view()),
    path("recent_colleges/", RecentlyAddedColleges.as_view()),
]
