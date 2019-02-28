import os, sys
 
sys.path.append('/home/ujcb52/web/manage')
sys.path.append('/home/ujcb52/venv_python36/lib/python3.6/site-packages/')
 
from django.core.wsgi import get_wsgi_application
 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manage.settings")
 
application = get_wsgi_application()
