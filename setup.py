from setuptools import setup, find_packages

setup(
    name='mgx-libs',
    version='0.1.0',
    description='Library package for migrx plugins',
    url='https://github.com/migrx-io/mgx-libs',
    author='Anatolii Makarov',
    author_email='anatolii.makaroff@gmail.com',
    packages=find_packages(),
    install_requires=[
        "gevent==22.10.2", "requests==2.28.2", "eventlet==0.30.2",
        "PyYAML==5.4.1", "lxml==4.9.2",
        "click==7.1.2", "Flask==2.0.3",
        "Flask-JWT-Extended==4.4.4","Jinja2==3.1.2",
        "psutil==5.9.4", "uWSGI==2.0.21", "websocket-client==1.4.2",
        "Werkzeug==2.2.2", "cassandra-driver==3.24.0",
        "simplejson==3.18.1", "confget==4.1.1",
        "croniter==1.3.8", "scrypt==0.8.20",
        "python-ldap==3.4.3", "PyQRCode==1.2.1", "pypng==0.20220715.0",
        "pyotp==2.8.0", "flasgger==0.9.5", "pytest==7.2.1", "pylint==2.10.2",
        "allure-pytest==2.12.0", "cassandra-migrate==0.3.4", "yapf==0.32.0",
        "transitions==0.9.0", "python-gnupg==0.5.0", "dnspython==1.16.0",
        "pbr==5.10.0", "tzlocal==4.3"
    ],
    classifiers=[
        'Intended Audience :: Migrx/Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3'
    ],
)
