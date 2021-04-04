from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect

import yatube.settings as settings
from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, settings.PAGINATE_BY)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
    }
    return render(request, 'index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:12]

    paginator = Paginator(posts, settings.PAGINATE_BY)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'page': page,
    }
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'post_new.html', context)


def profile(request, username):
    """Профиль любого автора"""
    author = get_object_or_404(User, username=username)

    posts = author.posts.all()
    paginator = Paginator(posts.all(), settings.PAGINATE_BY)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    following = (
        request.user.is_authenticated
        and Follow.objects.filter(author=author,
                                  user=request.user or None
                                  ).exists()
    )
    context = {
        'page': page,
        'count_posts': posts.count(),
        'author': author,
        'following': following,
        'followers': author.follower.count(),
        'following_to': author.following.count(),
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    context = {
        'post': post,
        'count_posts': post.author.posts.count(),
        'author': post.author,
        'comments': post.comments.all(),
        'form': CommentForm(),
        'followers': post.author.follower.count(),
        'following_to': post.author.following.count(),
    }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    current_post = get_object_or_404(
        Post, pk=post_id, author__username=username
    )

    if request.user != current_post.author:
        return redirect('index')
    form = PostForm(
        request.POST or None,
        instance=current_post,
        files=request.FILES or None
    )

    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
        'current_post': current_post
    }
    return render(request, 'post_new.html', context)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    """Создание комментария к посту"""
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    """Вывод постов, на которые подписан текущий пользователь"""
    following_post = Post.objects.filter(
        author__following__user=request.user).all()
    paginator = Paginator(following_post, settings.PAGINATE_BY)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться"""
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect('follow_index')


@login_required
def profile_unfollow(request, username):
    """Отписаться"""
    obj = get_object_or_404(
        Follow,
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    obj.delete()
    return redirect('follow_index')
