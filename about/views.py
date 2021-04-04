from django.views.generic.base import TemplateView


class AboutTechView(TemplateView):
    template_name = 'tech.html'


class AboutAuthorView(TemplateView):
    template_name = 'author.html'
