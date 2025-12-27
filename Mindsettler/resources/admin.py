from django.contrib import admin
from .models import Article, Video

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ('title', 'created_at')
    search_fields = ('title',)