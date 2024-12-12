from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed

class IsAuthenticatedWithJWT(BasePermission):
    """
    Custom permission to only allow users with a valid JWT token to access the resource.
    """

    def has_permission(self, request, view):
        # Check if the request contains an Authorization header with a token
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            raise AuthenticationFailed("Authorization header missing.")

        # Extract the token from the Authorization header
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            raise AuthenticationFailed("Invalid token header. No token provided.")

        try:
            # Validate and decode the JWT token
            access_token = AccessToken(token)
            # The user is authenticated with JWT, so we attach it to the request
            request.user = access_token.payload
        except Exception as e:
            raise AuthenticationFailed(f"Invalid token. Error: {str(e)}")
        
        return True
