import os
from setuptools import find_packages, setup


README = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst')


DEPENDENCIES = [
    'django >=1.6, <2.2',
    'funcy',
]


DEPENDENCY_LINKS = [
    # Add externally hosted packages like so:
    # e.g. http://github.com/[USERNAME]/[REPO]/tarball/[BRANCH]#egg=[EGG_NAME]
]


setup(
    name='django-abnorm',
    version='0.1.0',
    description='Django automatic denormalization toolkit',
    author='trashnroll',
    author_email='trashnroll@gmail.com',
    install_requires=DEPENDENCIES,
    dependency_links=DEPENDENCY_LINKS,
    setup_requires=[],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Framework :: Django :: 1.6",
        "Framework :: Django :: 1.7",
        "Framework :: Django :: 1.8",
        "Framework :: Django :: 1.9",
        "Framework :: Django :: 1.10",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Environment :: Web Environment",
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='django denormalization',
    packages=find_packages()
)
