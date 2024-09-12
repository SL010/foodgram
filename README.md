Foodgram

О возможностях проекта
«Фудграм» — сайт, на котором пользователи могут публиковать рецепты, добавлять рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

О проекте
Проект доступен по адресу: https://foodgramsl.hopto.org

Технологии, использованные при разработке
Python, Django REST Framework, PostgreSQL, Nginx, gunicorn, Docker, Docker-compose, GitHub Actions,

создание суперпользователя (в директории с файлом docker-compose.yml)
docker compose exec backend \
  env DJANGO_SUPERUSER_USERNAME=admin \
      DJANGO_SUPERUSER_EMAIL=admin@example.com \
      DJANGO_SUPERUSER_PASSWORD=changeme \
  python manage.py createsuperuser --noinput
