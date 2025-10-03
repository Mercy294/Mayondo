from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):

    # Custom auth backend to allow login with either username or email.
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        # Try to fetch by username or email
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user_obj = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        if user_obj.check_password(password) and self.user_can_authenticate(user_obj):
            return user_obj
        return None
