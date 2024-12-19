from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password


class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()  # This will return your CustomUser model
        try:
            # Attempt to get the user by email
            user = UserModel.objects.get(email=email, is_active=True)
        except UserModel.DoesNotExist:
            return None

        # Check if the password matches
        if user.check_password(password):
            return user
        return None
