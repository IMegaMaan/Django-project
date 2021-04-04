from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, null=False, unique=True)
    description = models.TextField()

    def __str__(self):
        return str(self.title)


class Post(models.Model):
    text = models.TextField(
        help_text="Заполнение данного поля является обязательным",
        verbose_name="Текст поста",
    )
    pub_date = models.DateTimeField(
        "date published",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts"
    )
    group = models.ForeignKey(
        Group, blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        help_text="Любая группа из уже существующих, либо ничего",
        verbose_name="Группа",
    )
    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True,
        verbose_name="Картинка для поста",
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ["-pub_date"]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(
        help_text="Напишите все, что думаете об этом",
        verbose_name="Текст комментария",
    )
    created = models.DateTimeField(
        "date published",
        auto_now_add=True,
    )


class Follow(models.Model):
    # ссылка на объект пользователя, который подписывается
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower"
    )
    # ссылка на объект пользователя, на которого подписываются,
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
