from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()  # This will return your CustomUser model
        try:
            # Attempt to get the user by email
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            return None
        
        # Check if the password matches
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
