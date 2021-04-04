from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group


class PostModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test')
        self.post_task = Post.objects.create(
            text='Тестовый текст. А это уже не должно быть в представлении',
            author=self.user,
        )

    def tearDown(self):
        self.user.delete()
        self.post_task.delete()

    def test_post_str_method(self):
        """__str__ совпадает с ожидаемым"""
        post_str = self.post_task.__str__()
        self.assertEqual(post_str, 'Тестовый текст.',
                         'Ошибка в строковом представлении модели Post')

    def test_help_text(self):
        """Проверка help_text"""
        self.assertEqual(self.post_task._meta.get_field('group').help_text,
                         'Любая группа из уже существующих, либо ничего',
                         'Ошибка в поле group help_text')
        self.assertEqual(self.post_task._meta.get_field('text').help_text,
                         'Заполнение данного поля является обязательным',
                         'Ошибка в поле text help_text')

    def test_verbose_name(self):
        """Проверка verbose_name"""
        self.assertEqual(
            self.post_task._meta.get_field('group').verbose_name, 'Группа',
            'Ошибка в поле group verbose_name'
        )
        self.assertEqual(
            self.post_task._meta.get_field('text').verbose_name, 'Текст поста',
            'Ошибка в поле get_field verbose_name'
        )


class TaskGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_task = Group.objects.create(
            title='Тестовый заголовок',
            slug='test',
            description='Описание тестовой группы',
        )

    def test_group_str_method(self):
        """Проверка корректности метода __str__ модели Group"""
        group_task_str = TaskGroupModelTest.group_task.__str__()
        self.assertEqual(group_task_str, 'Тестовый заголовок',
                         'Ошибка в строковом представлении модели Group')
