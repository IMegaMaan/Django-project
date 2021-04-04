import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group


class TaskFormTest(TestCase):
    def setUp(self):
        user = get_user_model()
        self.user = user.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        self.user.delete()

    def test_create_new_post(self):
        """Создание поста и перенаправление на главню странику"""
        form_data = {
            'text': 'Тестовый пост',
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data, follow=True
        )
        self.assertRedirects(response, reverse('index'))
        created_post = Post.objects.get(text=form_data['text'])

        self.assertEqual(created_post.text, form_data['text'],
                         'Создание поста не происходит')

        created_post.delete()

    def test_change_post(self):
        """Проверка изменения поста post_edit"""
        self.task_post = Post.objects.create(
            text='Текст поста до изменения',
            author=self.user
        )
        self.task_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
        )
        form_data = {
            'text': 'Тестовый пост после изменения',
            'group': self.task_group.pk,
        }

        args = [self.user.username, self.task_post.pk]
        self.authorized_client.post(reverse('post_edit', args=args),
                                    data=form_data, follow=True)
        post_after_change = Post.objects.get(pk=self.task_post.pk)
        text_draft = 'Во view "post_edit" не происходит изменения'
        self.assertEqual(post_after_change.text, form_data['text'],
                         f'{text_draft} текста поста')
        self.assertEqual(post_after_change.group.pk, self.task_group.pk,
                         f'{text_draft} изменения группы')

        self.assertEqual(post_after_change.pk, self.task_post.pk,
                         'Создается другой пост'
                         )

        self.task_post.delete()
        self.task_group.delete()


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(
        dir=settings.BASE_DIR, prefix='test_forms'))
class TaskImageSaveInDatabase(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskImageSaveInDatabase.user)

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
            content=TaskImageSaveInDatabase.small_gif,
            content_type='image/gif'
        )
        # crate user
        user = get_user_model()
        cls.user = user.objects.create_user(username='test')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        TaskImageSaveInDatabase.user.delete()
        super().tearDownClass()

    def test_create_post_from_form(self):
        """Пост сохраняется в БД при отправке через PostForm"""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст с картинкой',
            'image': TaskImageSaveInDatabase.uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), tasks_count + 1,
                         'Количество записей в БД не увеличивается')
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image='posts/small.gif',
                author=TaskImageSaveInDatabase.user
            ).exists()
        )
        # clear database
        Post.objects.filter(
            text='Тестовый текст',
            image='posts/small.gif',
            author=TaskImageSaveInDatabase.user
        ).delete()
