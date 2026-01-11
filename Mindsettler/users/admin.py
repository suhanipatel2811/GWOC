from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(DefaultUserAdmin):
    inlines = (ProfileInline,)
    # show phone column in the user changelist
    list_display = DefaultUserAdmin.list_display + ('phone_number',)

    def phone_number(self, obj):
        try:
            return obj.profile.phone
        except Exception:
            return ''
    phone_number.short_description = 'Phone'


# Re-register User admin to include Profile inline
try:
    admin.site.unregister(User)
except Exception:
    pass

admin.site.register(User, UserAdmin)
