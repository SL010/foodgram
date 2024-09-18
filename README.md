Foodgram

### Описание проекта:
О возможностях проекта
«Фудграм» — сайт, на котором пользователи могут публиковать рецепты, добавлять рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Проект доступен по адресу: https://foodgramsl.hopto.org

### Технологии, использованные при разработке:
Python, Django REST Framework, PostgreSQL, 
Nginx, gunicorn, Docker, Docker-compose, GitHub Actions,

### Запуск проекта в контейнерах:
-Перейди в директорию с файлом docker-compose.yml и выполни команду:
$docker compose up

-Выполни миграции:
$docker compose exec backend python manage.py migrate

-Выполнить сбор статики бэкенда:
$docker compose exec backend python manage.py collectstatic --no-input

-Копирование статики в папку подключенную к volumn:
$docker compose exec backend cp -r /app/collected_static/. /backend_static/static/

-Загрузка ингридиентов и тегов в базу данных:
$docker compose exec backend python manage.py load_ingredients
$docker compose exec backend python manage.py load_tags

-Создание суперпользователя:
$docker compose -f docker-compose.production.yml exec backend \
  env DJANGO_SUPERUSER_USERNAME=admin \
      DJANGO_SUPERUSER_EMAIL=admin@example.com \
      DJANGO_SUPERUSER_PASSWORD=changeme \
      DJANGO_SUPERUSER_FIRST_NAME=sss \
      DJANGO_SUPERUSER_LAST_NAME=bb \
  python manage.py createsuperuser --noinput


### Автор проекта:

Автор: [Борисов Вячеслав]
(https://github.com/SL010)
Почта: borisov.slava@yandex.ru

