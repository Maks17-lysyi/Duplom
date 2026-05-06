release: python manage.py migrate
web: python manage.py collectstatic --noinput && gunicorn squadup.wsgi:application