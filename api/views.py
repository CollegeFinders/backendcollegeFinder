from rest_framework.views import APIView
from .serilazers import *
from .models import *
from rest_framework import status
from rest_framework.response import Response
import random, string
from datetime import timedelta
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.utils import timezone
from .permissions import IsAdminUser, IsStudentUser, IsCollegeUser
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser


# from .tasks import send_otp
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
import threading

# from rest_framework.parsers import MultiPartParser, FormParser


class StudentRegView(APIView):

    @swagger_auto_schema(request_body=CustomUserAndStudentSerializer)
    def post(self, request):

        try:
            with transaction.atomic():
                custom_user_data = {
                    "email": request.data.get("email"),
                    "password": request.data.get("password"),
                    "is_active":True,
                    "is_college":False
                }

                serializer_one = CustomUserSerializer(data=custom_user_data)
                serializer_one.is_valid(raise_exception=True)

                student_data = {
                    "student_name": request.data.get("student_name"),
                    "gender": request.data.get("gender"),
                    "student_pincode": request.data.get("student_pincode"),
                }

                serializer_two = StudentRegSerializer(data=student_data)
                serializer_two.is_valid(raise_exception=True)

                user = serializer_one.save()

                student = serializer_two.save()

                student.user = user
                otp = "".join(random.choices(string.digits, k=6))
                student.otp = otp
                student.otp_expiry = timezone.now() + timedelta(minutes=5)

                student.save()

                try:
                    # send_otp.delay(otp, student.user.email)

                    def send_otp(otp, student_email):
                        send_mail(
                            "Your OTP Code",
                            f"Your OTP code is {otp}",
                            settings.EMAIL_HOST_USER,
                            [student_email],
                            fail_silently=False,
                        )

                    thread = threading.Thread(
                        target=send_otp, args=(otp, student.user.email)
                    )
                    thread.start()

                    return Response(
                        {"detail": "OTP sent to the registered email."},
                        status=status.HTTP_201_CREATED,
                    )

                except BadHeaderError:
                    return Response(
                        {"error": "Invalid header found."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            return Response(
                {"detail": f"somthing went wrong,{str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyOtpView(APIView):

    @swagger_auto_schema(request_body=OtpVerificationSerializer)
    def post(self, request):
        data = request.data
        serializer = OtpVerificationSerializer(data=data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response(
                    {"detail": "User with this email does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                student = Student.objects.get(user=user)
            except Student.DoesNotExist:
                return Response(
                    {"detail": "Student data not found for this user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if student and student.otp == otp and student.otp_expiry > timezone.now():
                student.otp = None
                student.otp_expiry = None
                user.is_active = True
                user.is_student = True
                user.save()
                student.save()
                return Response(
                    {"detail": "Account verified successfully."},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"detail": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class CollegeRegView(APIView):
#     parser_classes = [MultiPartParser, FormParser]

#     @swagger_auto_schema(request_body=CustomUserAndCollegeSerializer)
#     def post(self, request):
#         print("Incoming Data (Raw):", request.data)
#         try:
#             with transaction.atomic():
#                 custom_user_data = {
#                     "email": request.data.get("email"),
#                     "password": request.data.get("password"),
#                 }
#                 print("Custom User Data:", custom_user_data)
#                 serializer_one = CustomUserSerializer(data=custom_user_data)
#                 serializer_one.is_valid(raise_exception=True)

#                 college_data = {
#                     "logo": request.data.get("collegeLogo"),
#                     "image": request.data.get("collegeImageCover"),
#                     "college_name": request.data.get("collegeName"),
#                     "college_pincode": request.data.get("postalCode"),
#                     "college_details": request.data.get("collegeDetails"),
#                     "college_courses": request.data.get("courseTags"),
#                 }
#                 print("College Data:", college_data)
#                 serializer_two = CollegeRegSerializer(data=college_data)
#                 serializer_two.is_valid(raise_exception=True)

#                 user = serializer_one.save()

#                 college = serializer_two.save()
#                 college.user = user
#                 college.save()

#                 return Response(
#                     {
#                         "detail": "College registered successfully. Wait for approval from admin"
#                     },
#                     status=status.HTTP_201_CREATED,
#                 )
#         except Exception as e:
#             print("Error:", e)
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CollegeRegView(APIView):

    # @swagger_auto_schema(request_body=CustomUserAndCollegeSerializer)
    def post(self, request):
        print("Incoming Data (Raw):", request.data)
        try:
            with transaction.atomic():
                custom_user_data = {
                    "email": request.data.get("email"),
                    "password": request.data.get("password"),
                    "is_college":True,
                    "is_active":True
                }
                print("Custom User Data:", custom_user_data)
                serializer_one = CustomUserSerializer(data=custom_user_data)
                print("serializer",serializer_one)
                serializer_one.is_valid(raise_exception=True)

                # Handling courseTags
                course_tags_raw = request.data.getlist('courseTags[]')
                if course_tags_raw:
                    course_tags = list(map(int, course_tags_raw[0].split(',')))  # Convert to list of integers
                else:
                    course_tags = []

                # Handling collegeDetails
                college_details = request.data.get("collegeDetails")
                if not college_details:
                    college_details = "Default Value or Null"  # Adjust based on your model's needs

                college_data = {
                    "logo": request.data.get("collegeLogo"),
                    "image": request.data.get("collegeImageCover"),
                    "college_name": request.data.get("collegeName"),
                    "college_pincode": request.data.get("postalCode"),
                    "college_details": college_details,
                    "college_courses": course_tags,  # Array of integers
                    
                }
                print("College Data:", college_data)
                serializer_two = CollegeRegSerializer(data=college_data)
                serializer_two.is_valid(raise_exception=True)

                user = serializer_one.save()
                college = serializer_two.save()
                college.user = user
                college.save()

                return Response(
                    {
                        "detail": "College registered successfully. Wait for approval from admin"
                    },
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            print("Error:", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminRegView(APIView):
    def post(self, request):
        data = request.data
        serializer = AdminRegSerializer(data=data)
        try:
            if serializer.is_valid():
                CustomUser.objects.create_superuser(**serializer.validated_data)
                return Response(
                    {"detail": "Admin registered successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RefreshTokenView(APIView):
    """
    API view to refresh the access token using a valid refresh token.
    """

    def post(self, request):
        refresh_token = request.data.get("refreshToken")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)

            # Create the new access token
            access_token = str(refresh.access_token)

            return Response(
                {
                    "accessToken": access_token,
                    "refreshToken": str(
                        refresh
                    ),  # Optionally return the same refresh token
                },
                status=status.HTTP_200_OK,
            )

        except TokenError as e:
            return Response(
                {"detail": f"Invalid refresh token: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        data = request.data
        serializer = LoginSerializer(data=data)

        try:
            if serializer.is_valid():
                user = serializer.validated_data["user"]

                # Generate the refresh and access tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Determine the role and collect ids
                if user.is_student:
                    role = "student"
                    student_id = user.student.id if user.student else None  # Assuming user has a related student model
                    college_id = None  # Students don't have a college id directly in this case
                elif user.is_college:
                    role = "college"
                    student_id = None  # Colleges don't have a student id
                    college_id = user.college.id if user.college else None  # Assuming user has a related college model
                elif not user.is_college and not user.is_student and user.is_admin:
                    role = "admin"
                    student_id = None  # Admins don't have a student id
                    college_id = None  # Admins don't have a college id

                # Return the response with the access token, refresh token, role, ids
                return Response(
                    {
                        "accessToken": access_token,
                        "refreshToken": refresh_token,
                        "role": role,
                        "id": user.id,  # Include user id in the response
                        "studentId": student_id,  # Include student id if applicable
                        "collegeId": college_id,  # Include college id if applicable
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LocationRegView(APIView):
    permission_classes = [IsAdminUser]
    @swagger_auto_schema(
        request_body=LocationRegSerializer,
    )
    def post(self, request):
        data = request.data
        serializer = LocationRegSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"detail": "Location registered successfully"},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CourseRegView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(request_body=CourseRegSerializer)
    def post(self, request):
        data = request.data
        serializer = CourseRegSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"detail": "Course registered successfully"},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# class AdminCollegeApprovalView(APIView):
#     permission_classes = [IsAdminUser]

#     def get(self, request):
#         try:
#             colleges = College.objects.filter(
#                 is_approved=False, approval_request_sent=True
#             )
#             serializer = CollegeDetailsSerializer(colleges, many=True)

#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response(
#                 {"detail": f"An error occurred: {str(e)}"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#     @swagger_auto_schema(
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             properties={
#                 "college_id": openapi.Schema(type=openapi.TYPE_INTEGER),
#                 "action": openapi.Schema(type=openapi.TYPE_STRING),
#             },
#         )
#     )
#     def post(self, request):
#         college_id = request.data.get("college_id")
#         action = request.data.get("action")

#         if not college_id or action not in ["approve", "reject"]:
#             return Response(
#                 {"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             college = College.objects.get(id=college_id)
#             user = college.user

#             if action == "approve":
#                 college.is_approved = True
#                 college.approval_request_sent = False
#                 user.is_active = True
#                 user.is_college = True
#                 college.save()
#                 user.save()
#                 return Response(
#                     {"detail": "College approved successfully."},
#                     status=status.HTTP_200_OK,
#                 )

#             elif action == "reject":
#                 college.approval_request_sent = False
#                 college.save()
#                 return Response(
#                     {"detail": "College registration rejected."},
#                     status=status.HTTP_200_OK,
#                 )

#         except College.DoesNotExist:
#             return Response(
#                 {"detail": "College not found."}, status=status.HTTP_404_NOT_FOUND

#             )
        

class AdminCollegeApprovalView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            colleges = College.objects.filter(approval_request_sent=True)
            serializer = CollegeDetailsSerializer(colleges, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "college_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "action": openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    def post(self, request):
        college_id = request.data.get("college_id")
        action = request.data.get("action")

        if not college_id or action not in ["approve", "disapprove"]:
            return Response(
                {"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            college = College.objects.get(id=college_id)
            user = college.user

            if action == "approve":
                college.is_approved = True
                college.approval_request_sent = False
                user.is_active = True
                user.is_college = True
                college.save()
                user.save()
                return Response(
                    {"detail": "College approved successfully."},
                    status=status.HTTP_200_OK,
                )

            elif action == "disapprove":
                college.is_approved = False
                college.save()
                return Response(
                    {"detail": "College disapproved."},
                    status=status.HTTP_200_OK,
                )

        except College.DoesNotExist:
            return Response(
                {"detail": "College not found."}, status=status.HTTP_404_NOT_FOUND
            )


class CollegeListView(APIView):
    def get(self, request):
        try:
            colleges = College.objects.all()
            serializer = CollegeDetailsSerializer(colleges, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"not result found {e}" }, status=status.HTTP_404_NOT_FOUND
            )


class LocationListView(APIView):
    def get(self, request):

        try:
            location = Location.objects.all()
            serializer = LocationDetailsSerializer(location, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CourseListView(APIView):
    def get(self, request):
        try:
            courses = Course.objects.all()
            serializer = CourseDetailsSerializer(courses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LocationBasedCollegeListView(APIView):
    def get(self, request, location_id):

        try:
            college = College.objects.filter(location=location_id)

            if not college.exists():
                return Response(
                    {"detail": "No Colleges found in the location"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = CollegeDetailsSerializer(college, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# class StudentProfileUpdateView(APIView):
#     permission_classes = [IsStudentUser]

#     @swagger_auto_schema(request_body=StudentProfileSerializer)
#     def put(self, request):

#         data = request.data
#         user = request.data.get("user")
#         student = Student.objects.get(user=user)
#         serializer = StudentProfileSerializer(student, data=data, partial=True)

#         try:
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(
#                     {
#                         "detail": "Student updated successfully",
#                         "profile": serializer.data,
#                     },
#                     status=status.HTTP_200_OK,
#                 )

#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response(
#                 {"detail": f"An error occurred: {str(e)}"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

class StudentProfileUpdateView(APIView):
    permission_classes = [IsStudentUser]

    @swagger_auto_schema(request_body=StudentProfileSerializer)
    def put(self, request):
        try:
            student = Student.objects.get(user=request.user)  # Fetch student by authenticated user
        except Student.DoesNotExist:
            return Response(
                {"detail": "Student profile not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentProfileSerializer(student, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # No need to pass user explicitly
            return Response(
                {
                    "detail": "Student updated successfully",
                    "profile": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CollegeProfileUpdateView(APIView):
    permission_classes = [IsCollegeUser]  # Ensure this permission allows the college user to update the profile

    @swagger_auto_schema(request_body=CollegeProfileSerializer)
    def put(self, request):
        user = request.user  # Use request.user to get the authenticated user
        try:
            college = College.objects.get(user=user)  # Assuming the College model has a relation to the User model
        except College.DoesNotExist:
            return Response({"detail": "College not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # The incoming data should be handled with the serializer
        serializer = CollegeProfileSerializer(college, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # Save the updated data
            return Response(
                {"detail": "College updated successfully", "profile": serializer.data},
                status=status.HTTP_200_OK,
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CollegeDetailsView(APIView):
    def get(self, request, college_id):

        try:
            college = College.objects.get(id=college_id)
            serializer = CollegeDetailsSerializer(college)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SearchView(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("query", openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request):
        query = request.query_params.get("query", None)

        if not query:
            return Response(
                {"detail": "Query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course_results = []
            college_results = []

            if Course.objects.exists():
                course_q = Q(course_name__icontains=query)
                courses = Course.objects.filter(course_q)
                course_results = CourseDetailsSerializer(courses, many=True).data

            if College.objects.exists():
                college_q = (
                    Q(college_name__icontains=query)
                    | Q(location__location_name__icontains=query)
                    | Q(courses__course_name__icontains=query)
                )
                colleges = (
                    College.objects.filter(college_q)
                    .select_related("location")
                    .prefetch_related("courses")
                    .distinct()
                )
                college_results = CollegeDetailsSerializer(colleges, many=True).data

            result = {
                "courses": course_results,
                "colleges": college_results,
            }

            return Response(result, status=status.HTTP_200_OK)

        except ObjectDoesNotExist as e:
            return Response(
                {"detail": "not found.", "details": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                {"detail": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplyToCollegeView(APIView):

    @swagger_auto_schema(request_body=AppliedStudentsSerializer)
    def post(self, request):
        data = {
            "student_id": request.data.get("student_id"),
            "college_id": request.data.get("college_id"),
        }

        serializer = AppliedStudentsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

        else:
            print("Serializer one errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Applied Successfully"}, status=status.HTTP_200_OK)


class AppliedStudentsView(APIView):
    def get(self, request, college_id):
        applied_students = AppliedStudents.objects.filter(
            college_id=college_id
        ).values_list("student_id", flat=True)
        students = Student.objects.filter(id__in=applied_students)
        serializer = StudentDetailsSerializer(students, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            students = Student.objects.all()
            serializer = StudentDetailsSerializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(
                {"detail": "no result found"}, status=status.HTTP_404_NOT_FOUND
            )


class StudentDetailsView(APIView):
    permission_classes = [IsStudentUser]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            serializer = StudentDetailsSerializer(student)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AppliedCollegeView(APIView):
    permission_classes = [IsStudentUser]

    def get(self, request, student_id):
        applied_colleges = AppliedStudents.objects.filter(
            student_id=student_id
        ).values_list("college_id", flat=True)
        colleges = College.objects.filter(id__in=applied_colleges)
        serializer = CollegeDetailsSerializer(colleges, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class RecentlyAddedColleges(APIView):
    def get(self, request):
        try:
            recent_colleges = College.objects.order_by("-created_at").filter(
                is_approved=True
            )[:10]
            serializer = CollegeDetailsSerializer(recent_colleges, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": "no result found"}, status=status.HTTP_404_NOT_FOUND
            )


"""class UserDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user = request.user
        
        try:
            if user.is_student:
                # student = Student.objects.get(user=user)
                user_data = {
                    # "name": student.student_name,
                    # "gender": student.gender,
                    # "location": student.student_pincode.region,
                    "role":"student"
                }

            elif user.is_college:
                # college = College.objects.get(user=user)
                # courses = CourseDetailsSerializer(college.college_courses.all(), many=True).data
                user_data = {
                    # "college_name": college.college_name,
                    # "courses": courses,
                    # "location": college.college_pincode.region,
                    "role":"college"
                }

            elif not user.is_college and not user.is_student and user.is_admin:
                user_data = {"role":"admin"}

        except Student.DoesNotExist:
            user_data = None

        return Response(user_data, status=status.HTTP_200_OK)"""
