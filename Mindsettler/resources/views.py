from django.shortcuts import render, get_object_or_404
from .models import Article, Video
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse

def blog_list(request):
    query = request.GET.get('q')

    articles = Article.objects.all().order_by('-created_at')
    videos = Video.objects.all().order_by('-created_at')

    if query:
        articles = articles.filter(title__icontains=query)
        videos = videos.filter(title__icontains=query)

    paginator = Paginator(articles, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'resources/blog_list.html', {
        'articles': page_obj,
        'videos': videos,
        'query': query
    })


def blog_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    article.views += 1
    article.save(update_fields=['views'])
    
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action=f'Read article: {article.title}'
        )

    return render(request, 'resources/blog_detail.html', {
        'article': article
    })

def like_article(request, slug):
    article = get_object_or_404(Article, slug=slug)
    article.likes += 1
    article.save(update_fields=['likes'])
    
    # Track as module completion for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action=f'Completed module: {article.title}'
        )
    
    return HttpResponseRedirect(
        reverse('resources:blog_detail', args=[slug])
    )
