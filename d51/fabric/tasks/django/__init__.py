import pkg_resources
pkg_resources.declare_namespace(__name__)

FABRIC_TASK_MODULE=True

__all__ = ['init', ]

from fabric.api import local
from fabric.colors import *
from fabric.utils import fastprint, indent
import os
import random


REQUIREMENTS_FILE = 'requirements.txt'
REQUIREMENTS_TEMPLATE = """
Django
south
psycopg2
""".strip()

def init():
    local('virtualenv .')
    create_file_if_needed(REQUIREMENTS_FILE, REQUIREMENTS_TEMPLATE)
    local('pip install -E . -r requirements.txt')
    init_django()

# TODO: make database configurable, allow replacing
SETTINGS_TEMPLATE = """
import os

_CONFIG_PATH = os.path.dirname(__file__)
_BASE_PATH = os.path.join(_CONFIG_PATH, "..")

ADMINS = (
    ('%(username)s', '%(username)s@%(hostname)s'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'var/project.db'
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(_BASE_PATH, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Don't share this with anybody.
SECRET_KEY = '%(secret)s'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'config.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(_BASE_PATH, "templates"),
)

if os.path.exists(os.path.join(_CONFIG_PATH, "local_settings.py")):
    from .local_settings import *
""".strip()

DEVELOPMENT_TEMPLATE = """
from config.settings import *

DEBUG=True
TEMPLATE_DEBUG=DEBUG

apps = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'apps', '*'))
for app in apps:
    app_path = os.path.realpath(app)
    app_name = os.path.basename(app)
    if app_path not in sys.path:
        sys.path[0:0] = [app_path,]
    if app_name not in INSTALLED_APPS:
        INSTALLED_APPS = INSTALLED_APPS + (app_name,)

if os.path.exists(os.path.join(os.path.dirname(__file__), "local_development.py")):
    from .local_development import *
""".strip()

PRODUCTION_TEMPLATE = """
from config.settings import *

if os.path.exists(os.path.join(os.path.dirname(__file__), "local_production{{{.py")):
    from .local_production import *
""".strip()

URLS_TEMPLATE = """
from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', 
         {'document_root': settings.MEDIA_ROOT}),
    )
""".strip()

DJANGO_EXECUTABLE = """
#!/usr/bin/env python
import django.core.management
import optparse
import os
import sys

def main():
    sys.path[0:0] = [
        os.path.join(os.path.dirname(__file__), ".."),
    ]
    parser = optparse.OptionParser()
    parser.add_option(
        '-s', '--settings',
        dest='settings',
        help='settings file to execute using',
        default='development'
    )

    (options, args) = parser.parse_args()

    # TODO: handle ImportError
    # Ruthlessly borrowed from the buildout djangorecipe
    settings_file = 'config.%s' % options.settings
    settings = __import__(settings_file)
    for comp in settings_file.split('.')[1:]:
        settings = getattr(settings, comp)

    django.core.management.execute_manager(settings)

if __name__ == '__main__':
    main()
""".strip()

def if_not_exists(func):
    def run_if_not_exists(*args, **kwargs):
        if os.path.exists(args[0]):
            return
        return func(*args, **kwargs)
    return run_if_not_exists

# TODO: Move into fabric.contrib.files
@if_not_exists
def mkdir(directory, include_in_git=False):
    local("mkdir %s" % directory)

    if include_in_git:
        local("touch %s" % os.path.join(directory, '.include_in_git'))

@if_not_exists
def create_file_if_needed(file, contents):
    f = open(file, "w")
    f.write(contents)
    f.close()

def django_print(msg, indention=1):
    fastprint(indent(green(msg), spaces=4*indention))

def init_django():
    print green("Initializing Django...")
    def executable(force=False):
        django_print("Creating executable...")
        mkdir('bin')
        create_file_if_needed('bin/django', DJANGO_EXECUTABLE)
        os.chmod('bin/django', 0755)
        django_print("DONE!\n", indention=0)

    def settings():
        django_print("Creating initial settings...")
        # borrowed from djangorecipe
        def generate_secret():
            chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            return ''.join([random.choice(chars) for i in range(50)])

        mkdir('config')
        create_file_if_needed('config/__init__.py', '')
        # TODO: support configuring this
        create_file_if_needed('config/settings.py',
            SETTINGS_TEMPLATE % {
                "secret": generate_secret(),
                "username": os.environ['USER'],
                "hostname": os.uname()[1],
            })
        create_file_if_needed('config/development.py', DEVELOPMENT_TEMPLATE)
        create_file_if_needed('config/production.py', PRODUCTION_TEMPLATE)
        print green("DONE!")


    def urls():
        django_print("Creating base urls.py...")
        create_file_if_needed('config/urls.py', URLS_TEMPLATE)
        print green("DONE!")

    def create_directory_skeleton():
        django_print("Creating directory skeleton...")
        dirs_to_create = ['apps', 'media', 'resources', 'templates', 'var',]
        [mkdir(dir, include_in_git=True) for dir in dirs_to_create]
        print green("DONE!")

    executable()
    settings()
    urls()
    create_directory_skeleton()
    print green("Django successfully initialized!")

