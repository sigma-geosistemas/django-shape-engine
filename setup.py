from setuptools import setup, find_packages
from distutils.core import setup

setup(
    name='django-shape_engine',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/sigma-consultoria/django-shape_engine.git',
    license='',
    author='George Silva',
    author_email='george@consultoriasigma.com.br',
    description='Export Django querysets to shapefiles',
    install_requires=["django", "fiona"],
    classifiers=[
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Natural Language :: Portuguese (Brazilian)'
    ],
)
