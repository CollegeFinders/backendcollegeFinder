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
from .permissions import IsAuthenticatedWithJWT
from rest_framework.permissions import IsAdminUser
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .tasks import send_otp
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


class StudentRegView(APIView):
    """
    API view to register student.
    """

    @swagger_auto_schema(request_body=CustomUserAndStudentSerializer)
    def post(self, request):

        try:
            with transaction.atomic():
                custom_user_data = {
                    "email": request.data.get("email"),
                    "password": request.data.get("password"),
                }

                serializer_one = CustomUserSerializer(data=custom_user_data)
                serializer_one.is_valid(raise_exception=True)

                student_data = {
                    "student_name": request.data.get("student_name"),
                    "gender": request.data.get("gender"),
                    "location": request.data.get("location"),
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
                    send_otp.delay(otp, student.user.email)

                    return Response(
                        {"message": "OTP sent to the registered email."},
                        status=status.HTTP_201_CREATED,
                    )

                except BadHeaderError:
                    return Response(
                        {"error": "Invalid header found."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            return Response(
                {"message": "somthing went wrong,{e}"},
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
                    {"message": "User with this email does not exist."},
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
                    {"message": "Account verified successfully."},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"message": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CollegeRegView(APIView):

    @swagger_auto_schema(request_body=CustomUserAndCollegeSerializer)
    def post(self, request):

        try:
            with transaction.atomic():
                custom_user_data = {
                    "email": request.data.get("email"),
                    "password": request.data.get("password"),
                }
                serializer_one = CustomUserSerializer(data=custom_user_data)
                serializer_one.is_valid(raise_exception=True)

                college_data = {
                    "college_name": request.data.get("college_name"),
                    "courses": request.data.get("courses"),
                    "location": request.data.get("location"),
                }
                serializer_two = CollegeRegSerializer(data=college_data)
                serializer_two.is_valid(raise_exception=True)

                user = serializer_one.save()

                college = serializer_two.save()
                college.user = user
                college.save()

                return Response(
                    {
                        "message": "College registered successfully. Wait for approval from admin"
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"message": f"somthing went wrong,{e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AdminRegView(APIView):
    def post(self, request):
        data = request.data
        serializer = AdminRegSerializer(data=data)
        try:
            if serializer.is_valid():
                CustomUser.objects.create_superuser(**serializer.validated_data)
                return Response(
                    {"message": "Admin registered successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RefreshTokenView(APIView):
    """
    API view to refresh the access token using a valid refresh token.
    """

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create the RefreshToken instance using the provided refresh token
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
                {"message": f"Invalid refresh token: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(APIView):

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        data = request.data
        serializer = LoginSerializer(data=data)

        try:
            if serializer.is_valid():
                user = serializer.validated_data["user"]

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                return Response(
                    {"accessToken": access_token, "refreshToken": refresh_token},
                    status=status.HTTP_200_OK,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
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
                    {"message": "Location registered successfully"},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
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
                    {"message": "Course registered successfully"},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AdminCollegeApprovalView(APIView):
    def get(self, request):
        permission_classes = [IsAdminUser]

        try:
            colleges = College.objects.filter(
                is_approved=False, approval_request_sent=True
            )
            serializer = CollegeDetailsSerializer(colleges, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
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
        permission_classes = [IsAdminUser]

        college_id = request.data.get("college_id")
        action = request.data.get("action")

        if not college_id or action not in ["approve", "reject"]:
            return Response(
                {"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST
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
                    {"message": "College approved successfully."},
                    status=status.HTTP_200_OK,
                )

            elif action == "reject":
                college.approval_request_sent = False
                college.save()
                return Response(
                    {"message": "College registration rejected."},
                    status=status.HTTP_200_OK,
                )

        except College.DoesNotExist:
            return Response(
                {"message": "College not found."}, status=status.HTTP_404_NOT_FOUND
            )


class CollegeListView(APIView):
    def get(self, request):
        permission_classes = [IsAuthenticatedWithJWT]

        try:
            colleges = College.objects.all()
            serializer = CollegeDetailsSerializer(colleges, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(
                {"message": "not result found"}, status=status.HTTP_404_NOT_FOUND
            )


class LocationListView(APIView):
    def get(self, request):
        permission_classes = [IsAuthenticatedWithJWT]

        try:
            location = Location.objects.all()
            serializer = LocationDetailsSerializer(location, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CourseListView(APIView):
    def get(self, request):
        permission_classes = [IsAuthenticatedWithJWT]

        try:
            courses = Course.objects.all()
            serializer = CourseDetailsSerializer(courses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LocationBasedCollegeListView(APIView):
    def get(self, request, location_id):

        try:
            college = College.objects.filter(location=location_id)

            if not college.exists():
                return Response(
                    {"message": "No Colleges found in the location"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = CollegeDetailsSerializer(college, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class StudentProfileUpdateView(APIView):

    @swagger_auto_schema(request_body=StudentProfileSerializer)
    def put(self, request):
        permission_classes = [IsAuthenticatedWithJWT]

        data = request.data
        user = request.data.get("user")
        student = Student.objects.get(user=user)
        serializer = StudentProfileSerializer(student, data=data, partial=True)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Student updated successfully",
                        "profile": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CollegeProfileUpdateView(APIView):

    @swagger_auto_schema(request_body=CollegeProfileSerializer)
    def put(self, request):
        permission_classes = [IsAuthenticatedWithJWT]

        data = request.data
        user = request.data.get("user")
        college = College.objects.get(user=user)
        serializer = CollegeProfileSerializer(college, data=data, partial=True)

        try:
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "College updated successfully",
                        "profile": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CollegeDetailsView(APIView):
    def get(self, request, college_id):
        permission_classes = [IsAuthenticatedWithJWT]

        try:
            college = College.objects.get(id=college_id)
            serializer = CollegeDetailsSerializer(college)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SearchView(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("query", openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request):
        permission_classes = [IsAuthenticatedWithJWT]

        query = request.query_params.get("query", None)

        if not query:
            return Response(
                {"message": "Query parameter is required."},
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
                {"message": "not found.", "details": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                {"message": "An unexpected error occurred.", "details": str(e)},
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

        return Response({"message": "Applied Successfully"}, status=status.HTTP_200_OK)


class AppliedStudentsView(APIView):
    def get(self, request, college_id):
        applied_students = AppliedStudents.objects.filter(
            college_id=college_id
        ).values_list("student_id", flat=True)
        students = Student.objects.filter(id__in=applied_students)
        serializer = StudentDetailsSerializer(students, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentListView(APIView):
    def get(self, request):
        permission_classes = [IsAdminUser]

        try:
            students = Student.objects.all()
            serializer = StudentDetailsSerializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(
                {"message": "no result found"}, status=status.HTTP_404_NOT_FOUND
            )


class StudentDetailsView(APIView):
    def get(self, request, student_id):
        permission_classes = [IsAdminUser]

        try:
            student = Student.objects.get(id=student_id)
            serializer = StudentDetailsSerializer(student)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AppliedCollegeView(APIView):
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
                {"message": "no result found"}, status=status.HTTP_404_NOT_FOUND
            )
