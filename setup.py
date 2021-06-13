import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()
# 'pyramid_debugtoolbar', # enabled only for dev/testing
# 'mysqlclient', # mysql language
    
requires = [
    'pyramid==1.10',  # framework
    'SQLAlchemy==1.3.24',  # DB access
    'pytest',  # gunicorn
    'webtest',  # gunicorn
    'PyMySQL==1.0.2',  # gunicorn
    'pyramid_tm',  # transaction manager
    'transaction',
    'zope.sqlalchemy',  # zope session manager
    'gunicorn==20.0.4',  # gunicorn
    'webtest',  # gunicorn
    'urllib3==1.26.4',  # gunicorn
    'get-docker-secret',
    'pyramid_jwt',  # auth. by jwt token
    'cornice==5.1.0',  # Rest - API (Custom adapters (arrow) not working on 5.0.3 yet.)
    'cryptography',  # for mysql 8.0
    'sqlalchemy_filters',
    'colander',  # JSON handling (required by cornice) TODO?
    'jsonschema',  # json data validation
    'python-dateutil',  # for formatting iso-formats to datetime (only necessary for python <3.7)
    'sqlalchemy-utils==0.36.8',
    'arrow==1.0.3'
    ]
# apt-get install build-essential libssl-dev libffi-dev python-dev
tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
    ]

setup(name='fabrikApi',
    version='1.0',
    description='demokratiefabrik/fabrikApi',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Application",
    ],
    author='Dominik Wyss',
    author_email='demokratiefabrik.ipw@unibe.ch',
    url='',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={'testing': tests_require, },
    install_requires=requires,
    python_requires='>=3.5',
    entry_points={
        'paste.app_factory': [
            'main = fabrikApi:main',
        ],
        'console_scripts': [
            # NOTE: run pip install -e
            # 'initialize_fabrikApi_db = fabrikApi.scripts.initializedb:main',
            'check_peerreview = fabrikApi.scripts.check_peerreview:main',
        ],
    },
)
