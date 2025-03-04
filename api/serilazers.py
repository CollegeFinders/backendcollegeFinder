from rest_framework import serializers
from .models import *
from django.contrib.auth import authenticate,login
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.contrib.auth.hashers import check_password
from cloudinary.models import CloudinaryField


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["email", "password","is_active","is_college"]




class StudentRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["student_name", "gender", "student_pincode"]


class StudentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "student_name", "gender", "student_pincode"]


# class CollegeRegSerializer(serializers.ModelSerializer):
#     college_courses = serializers.PrimaryKeyRelatedField(
#         queryset=Course.objects.all(), many=True
#     )
class CollegeRegSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField()
    image = serializers.ImageField()



    class Meta:
        model = College
        fields = [
            "logo",
            "image",
            "college_name",
            "college_pincode",
            "college_courses",
            "college_details",
        ]



class AdminRegSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class LocationRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        exclude = ["id", "created_at", "updated_at"]


class LocationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        exclude = ["id", "created_at", "updated_at"]


class CourseRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["course_name"]


class CourseDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "course_name"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data["user"] = user
        return data

        

        """try:

            if user.is_student:
                student = Student.objects.get(user=user)
                user_data = {
                    "name": student.student_name,
                    "gender": student.gender,
                    "location": student.location.location_name,
                    "role":"student"
                }

            elif user.is_college:
                college = College.objects.get(user=user)
                courses = CourseDetailsSerializer(college.courses.all(), many=True).data
                user_data = {
                    "college_name": college.college_name,
                    "courses": courses,
                    "location": college.location.location_name,
                    "role":"college"
                }

            elif not user.is_college and not user.is_student:
                data["user"] = user
                data["user_data"] = {"role":"admin"}
                return data

        except Student.DoesNotExist:
            user_data = None

        data["user"] = user
        data["user_data"] = user_data
        return data

    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "refreshToken": str(refresh),
            "accessToken": str(refresh.access_token),
        }"""


class OtpVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        otp = data.get("otp")
        if not email or not otp:
            raise serializers.ValidationError("Both email and OTP are required.")
        return data


class CollegeDetailsSerializer(serializers.ModelSerializer):
    location = LocationDetailsSerializer(read_only=True)
    college_courses = CourseDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = College
        fields = '__all__'






class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["user", "student_name", "gender", "student_pincode"]


class CollegeProfileSerializer(serializers.ModelSerializer):
    # courses = serializers.PrimaryKeyRelatedField(
    #     queryset=Course.objects.all(), many=True  # Linking courses with the Course model
    # )

    class Meta:
        model = College
        fields = ["user","logo","image", "college_name", "college_pincode","college_details", "college_courses"]


class CustomUserAndCollegeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    logo = serializers.ImageField()
    image = serializers.ImageField()
    college_name = serializers.CharField()
    college_details = serializers.CharField()
    college_courses = serializers.ListSerializer(child=serializers.IntegerField())
    college_pincode = serializers.IntegerField()


class CustomUserAndStudentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    student_name = serializers.CharField()
    gender = serializers.CharField()
    location = serializers.IntegerField()


class AppliedStudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppliedStudents
        fields = "__all__"
