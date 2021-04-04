from django.test import TestCase, Client
from django.urls import reverse


class TaskAboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.about_views = {
            'about:author': 'author.html',
            'about:tech': 'tech.html',
        }

    def test_about_pages_avialable_to_guest(self):
        """Страницы приложения about доступны гостевому пользователю"""
        for view in TaskAboutViewsTests.about_views.keys():
            with self.subTest():
                response = self.guest_client.get(reverse(view))
                status = response.status_code
                self.assertEqual(
                    status, 200,
                    f'Страничка view "{view}" приложения about недоступна '
                    'гостевому пользователю'
                )

    def test_about_views_according_templates(self):
        """Проверка вызова корректных шаблонов во view приложения about"""
        for view, template in TaskAboutViewsTests.about_views.items():
            with self.subTest():
                response = self.guest_client.get(reverse(view))
                self.assertTemplateUsed(
                    response, template,
                    f'Во view "{view}" вызывется некорректный шаблон'
                )
