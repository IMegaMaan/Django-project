import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, Follow, Comment

User = get_user_model()


class TaskViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='test_author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Test post one',
            author=TaskViewsTests.author,
        )
        cls.urls_params = {
            # 'view_name': 'template name'
            'index': 'index.html',
            'new_post': 'post_new.html',
            'group_posts': 'group.html',
            'profile': 'profile.html',
            'post': 'post.html',
            'post_edit': 'post_new.html',
        }
        author_username = TaskViewsTests.author.username
        post_id = TaskViewsTests.post.pk
        cls.args = {
            # 'view_name': [args]
            'group_posts': [TaskViewsTests.group.slug],
            'profile': [author_username],
            'post': [author_username, post_id],
            'post_edit': [author_username, post_id],
        }

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskViewsTests.author)

    def tearDown(self):
        self.user.delete()

    def test_view_according_template(self):
        """
        Проверка содержания вызова корректных шаблонов
        """

        for view, template in TaskViewsTests.urls_params.items():
            with self.subTest():
                args = TaskViewsTests.args.get(view)

                response = self.authorized_client.get(reverse(view, args=args))
                self.assertTemplateUsed(
                    response, template,
                    f'Во view "{view}" вызывется некорректный шаблон. '
                    f'Должен быть {template}'
                )

    def test_main_page_context_and_len_paginator(self):
        """
        Проверка context шаблона index.html
        """
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        response = self.authorized_client.get(reverse('index'))
        context_page = response.context['page'][0]

        self.assertEqual(
            context_page, self.post,
            'На страничку index.html не передается созданный пост'
        )

        self.post.delete()

    def test_group_page_context(self):
        """
        Проверка context шаблона group.html
        """
        self.post_without_group = Post.objects.create(
            text='Тестовый пост без группы',
            author=self.user,
        )
        self.post_with_group = Post.objects.create(
            text='Тестовый пост с группой',
            author=self.user,
            group=TaskViewsTests.group,

        )
        args = TaskViewsTests.args['group_posts']
        response = self.authorized_client.get(
            reverse('group_posts', args=args)
        )
        context_post = response.context['page'][0]
        context_group = response.context['group']
        group_template = self.urls_params['group_posts']

        self.assertEqual(context_group, self.group,
                         'Происходит привязка к некорректной группе')

        self.assertEqual(
            context_post, self.post_with_group,
            f'Некорректная выборка постов на страничке {group_template}, '
            f'группы {context_group}')

        self.post_without_group.delete()
        self.post_with_group.delete()

    def test_new_page_context(self):
        """
        Проверка context шаблона new.html (создание поста)
        """
        draft_words = 'В контексте шаблона new.html передается некорректн'
        self.task_form_type = type(PostForm())
        response = self.authorized_client.get(reverse('new_post'))
        context_form = response.context['form']
        context_is_edit = response.context['is_edit']
        self.assertIsInstance(
            context_form, self.task_form_type,
            f'{draft_words}ая форма.'
        )
        self.assertEqual(
            context_is_edit, False,
            f'{draft_words}ое значение is_edit.'
        )

    def test_post_with_group(self):
        """
        Проверка создания поста с группой
        """
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=TaskViewsTests.group,

        )

        response = self.authorized_client.get(reverse('index'))
        context_post = response.context['page'][0]
        self.assertEqual(context_post, self.post,
                         'Пост не отображается на главной страничке')

        args = TaskViewsTests.args.get('group_posts')

        response = self.authorized_client.get(
            reverse('group_posts', args=args)
        )
        context_post = response.context['page'][0]
        self.assertEqual(context_post, self.post,
                         'Пост не отображается на страничке группы')

        self.post.delete()

    def test_profile_view_context(self):
        """
        Проверка содержимого context view profile
        context = {
            "page": page,
            "count_posts": posts.count(),
            "author": author
        }
        """

        draft_words = 'В контексте view "profile" некорректное'
        # another author post
        self.post_another_author = Post.objects.create(
            text='Тестовый пост другого автора',
            author=self.user
        )
        args = TaskViewsTests.args['profile']
        response = self.authorized_client.get(reverse('profile', args=args))

        context_page = response.context['page'][0]
        context_count_posts = response.context['count_posts']
        context_author = response.context['author']

        self.assertEqual(context_page, TaskViewsTests.post,
                         f'{draft_words} содержание')
        self.assertEqual(context_count_posts, 1,
                         f'{draft_words} количество постов автора')
        self.assertEqual(context_author, TaskViewsTests.author,
                         f'{draft_words} имя автор поста')

        self.post_another_author.delete()

    def test_post_view_context(self):
        """Проверка содержимого context 'view' post
        context = {
            'post': post,
            'count_posts': count_posts,
            'author': author,
        }
        """
        self.task_first_post = Post.objects.create(
            text='Тестовый первый пост',
            author=self.author
        )
        self.task_second_post = Post.objects.create(
            text='Тестовый второй пост',
            author=self.author,
            group=TaskViewsTests.group
        )
        task_context = {
            'post': self.task_first_post,
            'count_posts': self.author.posts.count(),
            'author': self.author,
        }
        draft_words = 'В контексте view "post" некорректн'
        args = [self.author.username, self.task_first_post.pk]

        response = self.authorized_client.get(reverse('post', args=args))

        context_post = response.context['post']
        context_count_posts = response.context['count_posts']
        context_author = response.context['author']

        self.assertEqual(context_post, task_context['post'],
                         f'{draft_words}ый пост')
        self.assertEqual(context_count_posts, task_context['count_posts'],
                         f'{draft_words}ое количество постов автора')
        self.assertEqual(context_author, task_context['author'],
                         f'{draft_words}ое имя автор поста')

        self.task_first_post.delete()
        self.task_second_post.delete()

    def test_post_edit_view_context(self):
        """
        Проверка содержимого context 'view' post_edit
        context = {
        'form': form,
        'is_edit': True,
        'current_post': current_post
        }
        """
        task_form = PostForm(instance=TaskViewsTests.post)
        draft_words = 'В контексте view "post_edit" некорректн'
        args = [self.author.username, TaskViewsTests.post.pk]
        response = self.authorized_client.get(reverse('post_edit', args=args))

        context_form = response.context['form']
        context_is_edit = response.context['is_edit']
        context_current_post = response.context['current_post']
        context_form_post = context_form.instance

        self.assertIsInstance(
            context_form, type(task_form),
            f'{draft_words}ая форма.'
        )
        self.assertEqual(
            context_is_edit, True,
            f'{draft_words}ое значение is_edit.'
        )
        self.assertEqual(
            context_current_post, TaskViewsTests.post,
            f'{draft_words}ый пост.'
        )
        self.assertEqual(
            context_form_post, TaskViewsTests.post,
            f'{draft_words}ый пост в форме.'
        )

    def test_paginator_len(self):
        """
        Проверка, что в словарь context главной страницы
        передаётся не более установленного количества постов.
        """
        task_post_text = 'Тестовый пост с одним и тем же текстом'
        for post in range(20):
            Post.objects.create(
                text=task_post_text,
                author=self.author,
            )
        response = self.authorized_client.get(reverse('index'))
        context_cnt_psts = len(response.context['page'])
        self.assertEqual(
            context_cnt_psts, 10,
            'Передается неверное кличетво постов на одну страничку view index')
        Post.objects.filter(text=task_post_text).all().delete()

    def test_context_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан """
        task_post_text = 'Тестовый пост с одним и тем же текстом'
        self.not_follower = User.objects.create(
            username='test_not_follower_657'
        )
        self.follower = User.objects.create(username='test_follower_333')
        author = TaskViewsTests.author

        for post in range(3):
            Post.objects.create(
                text=task_post_text,
                author=author,
            )
        Follow.objects.create(
            user=self.follower,
            author=author,
        )

        posts = Post.objects.filter(
            author=author
        ).all()

        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

        response = self.follower_client.get(reverse('follow_index'))
        context_page = response.context['page']

        self.assertEqual(len(context_page), len(posts),
                         "У подписчика передается некорректное количество "
                         "постов в follow_index")
        for post in posts:
            with self.subTest():
                self.assertTrue(post in context_page,
                                f"Созданного поста {post} нет в страничке "
                                "подписчика")
        self.assertTemplateUsed(response, "follow.html",
                                "Используется некорректный шаблон")

        Post.objects.filter(text=task_post_text,
                            author=author).delete()
        self.not_follower.delete()
        self.follower.delete()

    def test_context_not_follow_index(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто не подписан на него."""
        task_post_text = 'Тестовый пост с одним и тем же текстом'
        self.not_follower = User.objects.create(
            username='test_not_follower_657'
        )
        self.follower = User.objects.create(username='test_follower_333')
        author = TaskViewsTests.author

        for post in range(3):
            Post.objects.create(
                text=task_post_text,
                author=author,
            )
        Follow.objects.create(
            user=self.follower,
            author=author,
        )

        Post.objects.filter(
            author=author
        ).all()

        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)

        response = self.not_follower_client.get(reverse('follow_index'))
        context_page = response.context['page']

        self.assertEqual(
            len(context_page), 0,
            "Неподписанный ни на кого пользователь видит чьи-то посты"
        )

        self.assertTemplateUsed(
            response, "follow.html",
            "Используется некорректный шаблон."
        )

        Post.objects.filter(text=task_post_text,
                            author=author).delete()
        self.not_follower.delete()
        self.follower.delete()


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(
        dir=settings.BASE_DIR, prefix='test_forms'))
class TaskImageSave(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskImageSave.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # image upload
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=TaskImageSave.small_gif,
            content_type='image/gif'
        )
        # crate user
        user = get_user_model()
        cls.user = user.objects.create_user(username='test')

        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post_with_image = Post.objects.create(
            text='Первый тестовый пост',
            image=TaskImageSave.uploaded,
            author=TaskImageSave.user,
            group=TaskImageSave.group,
        )
        # (view, way_to_image, template)
        cls.views = (
            ('index', 'page', 'index.html',),
            ('profile', 'page', 'profile.html',),
            ('group_posts', 'page', 'group.html',),
            ('post', 'post', 'post.html',),
        )
        # view_name: [arg_1, arg_2, ...]
        cls.args = {
            'profile': [TaskImageSave.user.username],
            'group_posts': [TaskImageSave.group.slug],
            'post': [TaskImageSave.user.username,
                     TaskImageSave.post_with_image.pk]
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        TaskImageSave.user.delete()
        TaskImageSave.post_with_image.delete()
        TaskImageSave.group.delete()
        super().tearDownClass()

    def test_image_in_context_index(self):
        """Наличие картинки в контексте"""
        for view, key, template in TaskImageSave.views:
            with self.subTest():
                args = TaskImageSave.args.get(view)
                response = self.authorized_client.get(reverse(view, args=args))
                context = response.context[key]
                content_image = (context.image if isinstance(context, Post)
                                 else context[0].image)
                self.assertEqual(
                    content_image.read(), TaskImageSave.small_gif,
                    f'На страничку {template} не передается загруженная '
                    'в пост картинка.'
                )


class TaskCommentsFollow(TestCase):
    def setUp(self):
        user = get_user_model()
        self.user = user.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def tearDown(self):
        self.user.delete()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Test post one',
            author=TaskCommentsFollow.author,
        )

    def test_follow_unfollow(self):
        """Подписка и отписка"""
        follow_counts = Follow.objects.filter(user=self.user).count()
        author = TaskCommentsFollow.author
        self.authorized_client.get(
            reverse('profile_follow', args=[author.username])
        )
        self.assertEqual(
            follow_counts + 1,
            Follow.objects.filter(user=self.user).count(),
            'Количество подписчиков не увеличивается'
        )
        new_follow = Follow.objects.get(user=self.user,
                                        author=author)
        self.assertEqual(new_follow.user, self.user,
                         'Привязка к некорректному user модели Follow')

        self.assertEqual(new_follow.author, author,
                         'Привязка к некорректному author модели Follow')

        Follow.objects.filter(user=self.user,
                              author=author).delete()

    def test_unfollow(self):
        """
        Отписка
        """
        author = TaskCommentsFollow.author
        Follow.objects.create(
            user=self.user,
            author=author,
        )

        self.authorized_client.get(
            reverse('profile_unfollow', args=[author.username])
        )
        deleted_follow = Follow.objects.filter(user=self.user,
                                               author=author).first()
        self.assertIsNone(deleted_follow, 'Удаление подписки не работает')

    def test_comment_to_post(self):
        """
        Только авторизированный пользователь может
        комментировать посты
        """
        form_data_auth = {
            'text': 'Тестовый комментарий авторизованного пользователя'
        }
        form_data_guest = {
            'text': 'Тестовый комментарий гостевого пользователя'
        }
        author_comment = self.user
        post = TaskCommentsFollow.post

        # auth user make a comment
        self.authorized_client.post(
            reverse('add_comment', args=[author_comment.username, post.pk]),
            follow=True,
            data=form_data_auth,
        )
        auth_comment = Comment.objects.filter(
            post=post,
            author=author_comment,
            text=form_data_auth['text']
        ).first()
        self.assertEqual(auth_comment.post.pk, post.pk,
                         "Комментарий привязывется не к тому посту")
        self.assertEqual(auth_comment.author.pk, author_comment.pk,
                         "Комментарий привязывется не к тому автору")
        self.assertEqual(auth_comment.text, form_data_auth['text'],
                         "Некорректный текст в комментарии")
        # guest try make a comment
        self.guest_client.post(
            reverse('add_comment', args=[author_comment.username, post.pk]),
            follow=True,
            data=form_data_guest,
        )
        guest_comment = Comment.objects.filter(
            post=post,
            author=author_comment,
            text=form_data_guest['text']
        ).first()

        self.assertIsNone(
            guest_comment,
            "Происходит создание комментария неавторизованным пользователем"
        )
        self.assertEqual(Comment.objects.all().count(), 1,
                         'Комментариев создано больше ,чем 1')

        auth_comment.delete()
