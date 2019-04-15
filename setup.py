try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = '0.6.6'

with open('requirements/production.txt') as requirements_file:
    requires = [item for item in requirements_file]

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='powerlibs-django-restless',
    version=version,
    description="Set of tools to build a JSON REST API for Django projects",
    long_description=readme,
    author='Cléber Zavadniak',
    author_email='cleberman@gmail.com',
    url='https://github.com/Dronemapp/powerlibs-django-restless',
    license=license,
    packages=['powerlibs.django.restless'],
    package_data={'': ['AUTHORS.md', 'README.md']},
    include_package_data=True,
    install_requires=requires,
    zip_safe=False,
    keywords='generic libraries',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ),
)
