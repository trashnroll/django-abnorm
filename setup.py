import os
from setuptools import find_packages, setup


README = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst')


DEPENDENCIES = [
    'django >=2.2, <4.1',
]


DEPENDENCY_LINKS = [
    # Add externally hosted packages like so:
    # e.g. http://github.com/[USERNAME]/[REPO]/tarball/[BRANCH]#egg=[EGG_NAME]
]


setup(
    name='django-abnorm',
    version='1.2.0',
    description='Django automatic denormalization toolkit',
    author='trashnroll',
    author_email='trashnroll@gmail.com',
    install_requires=DEPENDENCIES,
    dependency_links=DEPENDENCY_LINKS,
    setup_requires=[],
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='django denormalization',
    packages=find_packages()
)
