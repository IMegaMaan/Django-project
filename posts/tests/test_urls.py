from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from posts.models import Group, Post

User = get_user_model()


class TaskStaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')

        cls.post = Post.objects.create(
            text='Test post one',
            author=TaskStaticURLTests.author,
        )
        # group create
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        author_username = TaskStaticURLTests.author.username
        post_id = TaskStaticURLTests.post.pk
        group_slug = TaskStaticURLTests.group.slug
        cls.urls_params = {
            # 'url': ('template name', 'guest status',
            # 'authorized status', 'author_post_status')
            '/': ('index.html', 200, 200,),
            '/new/': ('post_new.html', 302, 200,),
            f'/group/{group_slug}/': ('group.html', 200, 200,),
            f'/{author_username}/': ('profile.html', 200, 200, 200,),
            f'/{author_username}/{post_id}/': ('post.html', 200, 200, 200,),
            f'/{author_username}/{post_id}/edit/':
                ('post_new.html', 302, 302, 200,),
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

        self.user = User.objects.create_user(username='authorized_not_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author = Client()
        cache.clear()

    def tearDown(self):
        self.user.delete()

    def test_urls_uses_correct_template(self):
        """
        Проверка, вызываются ли ожидаемые шаблоны
        (для авторизованного пользователя)
        """
        # full access only for logged author of posts
        self.authorized_client.force_login(TaskStaticURLTests.author)

        for url, template_and_stats in TaskStaticURLTests.urls_params.items():
            with self.subTest():
                template = template_and_stats[0]

                response = self.authorized_client.get(url, follow=True)
                self.assertTemplateUsed(
                    response, template,
                    f'По url {url} вызывется некорректный шаблон {template}'
                )

    def test_guest_user_rights(self):
        """
        Проверка доступа к шаблонам гостевого пользователя
        """
        for url, template_and_stats in TaskStaticURLTests.urls_params.items():
            with self.subTest():
                response_status = template_and_stats[1]

                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code, response_status,
                    'У гостевого пользователя неверный доступ '
                    f'к шаблону {template_and_stats[0]}'
                )

    def test_authorised_user_rights(self):
        """
        Проверка доступа к шаблонам авторизованного пользователя
        """
        for url, template_and_stats in TaskStaticURLTests.urls_params.items():
            with self.subTest():
                response_status = template_and_stats[2]

                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code, response_status,
                    'У авторизованного пользователя неверный доступ к '
                    f'шаблону {template_and_stats[0]}'
                )

    def test_author_post_rights(self):
        """
        Проверка доступа к шаблонам автора постов
        """
        self.author.force_login(TaskStaticURLTests.author)
        for url, template_and_stats in TaskStaticURLTests.urls_params.items():
            with self.subTest():
                if len(template_and_stats) < 4:
                    continue
                response_status = template_and_stats[3]
                response = self.author.get(url)
                self.assertEqual(
                    response.status_code, response_status,
                    'У автора поста неверный доступ к шаблону '
                    f'{template_and_stats[0]}'
                )

    def test_cache_index_page(self):
        """Проверка кешированиия страинцы index.html"""
        response_1 = self.authorized_client.get('/')
        task_post_text = 'Тестовый пост с одним и тем же текстом'
        for post in range(5):
            Post.objects.create(
                text=task_post_text,
                author=self.user,
            )
        response_2 = self.authorized_client.get('/')
        self.assertEqual(response_1.content, response_2.content,
                         'Некорректное сохранение кеша на главной странице')
        cache.clear()
        response_aft_cache_clear = self.authorized_client.get('/')
        self.assertNotEqual(
            response_aft_cache_clear.content, response_1.content,
            'Кеш не очищается'
        )

        Post.objects.filter(text=task_post_text).all().delete()


@override_settings(DEBUG=False)
class TaskTestErrorPages(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.urls_params = {
            # 'url': ('template name', 'guest status',
            # 'authorized status',)
            '404-error/': ('misc/404.html', 404, 404,),
            '/500/': ('misc/500.html', 500, 500,),
        }

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='authorized_not_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.authorized_user = Client()

    def tearDown(self):
        self.user.delete()

    def test_guest_error_404_500(self):
        """
        Доступ к страницам 404 и 500 гостевого пользователя
        """
        for url, template_and_stats in TaskTestErrorPages.urls_params.items():
            with self.subTest():
                response_status = template_and_stats[1]

                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code, response_status,
                    'У гостевого пользователя неверный доступ к '
                    f'шаблону {template_and_stats[0]}'
                )

    def test_auth_user_error_404_500(self):
        """
        Доступ к страницам 404 и 500 авторизованного пользователя
        """
        for url, template_and_stats in TaskTestErrorPages.urls_params.items():
            with self.subTest():
                response_status = template_and_stats[2]

                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code, response_status,
                    'У авторизованного пользователя неверный доступ к '
                    f'шаблону {template_and_stats[0]}'
                )

    def test_templates_error_404_500(self):
        """
        Проверка возвращаемых шаблонов страниц 404 и 500
        """
        for url, template_and_stats in TaskTestErrorPages.urls_params.items():
            with self.subTest():
                template = template_and_stats[0]

                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'По пути {url} вызывается некорректный шаблон. '
                    f'Должен быть {template}'
                )
