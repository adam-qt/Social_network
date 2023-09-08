from django.contrib import admin
from .models import (User, Comment, Post, Reaction)
from django.contrib.auth.models import Group
from rangefilter.filters import DateRangeFilter
from .filters import AuthorFilter, PostFilter
from django_admin_listfilter_dropdown.filters import DropdownFilter,\
    RelatedDropdownFilter, ChoiceDropdownFilter
admin.site.unregister(Group)


class CommentInLine(admin.TabularInline):
    model = Comment


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_active',
        'is_superuser',

    ]
    ordering = ['username']
    readonly_fields = ('date_joined', 'last_login')
    search_fields = ('id', 'username', 'email')
    fieldsets = (
        (
            "Личные данные", {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )}
        ),
        (
            "Учетные данные", {
                "fields": (
                    "username",
                    "password",
                )
            }
        ),
        (
            "Статусы", {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "is_active",
                )
            }
        ),
        (
            None, {
                "fields": (
                    "friends",
                )
            }
        ),
        (
            "Даты", {
                "fields": (
                    "date_joined",
                    "last_login",
                )
            }
        )
    )
    list_filter = (
            ('date_joined', DateRangeFilter),
    )


@admin.register(Comment)
class CommentModelAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'body',
                    'author',
                    )
    list_filter = (AuthorFilter, PostFilter)


@admin.register(Post)
class PostModelAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'get_body',
        'author',
        'get_comments_count']
    readonly_fields = ('created_at',)
    inlines = [CommentInLine]
    list_display_links = ('title', 'get_body', 'get_comments_count')
    fieldsets = (
        ('Post', {'fields':
                  ('author', 'body')
                  }),
        ('created', {'fields':
                         ('created_at',)})
    )
    search_fields = ('title',)

    def get_body(self, obj):
        max_length = 50
        if len(obj.body) > max_length:
            return obj.body[:max_length - 3] + '...'
        return obj.body

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("comments")

    get_body.short_description = 'body'
    get_comments_count.short_description = 'comments'
    list_filter = (('created_at', DateRangeFilter), AuthorFilter
                   )


@admin.register(Reaction)
class ReactionModelAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'value',
                    'author')
    readonly_fields = ('created_at',)
    list_filter = (AuthorFilter,
                   PostFilter,
                   ('value', ChoiceDropdownFilter))
    autocomplete_fields = (
        "author",
        "post",
    )
