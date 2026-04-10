from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile
from django.utils.html import format_html


class AccountAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active','first_name', 'last_name','date_joined', 'last_login')
    list_display_links = ('email','first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class UserProfileAdmin(admin.ModelAdmin):

    def thumbnail(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="30" style="border-radius:50%;">',
                obj.profile_picture.url
            )
        return "-"

    thumbnail.short_description = 'Profile Picture'

    list_display = ('thumbnail','user', 'address_line_1', 'address_line_2', 'city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)