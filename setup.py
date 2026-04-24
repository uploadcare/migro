""""
    Migro
    =====

    Migro - Uploadcare migration tool.

"""
import re

from setuptools import find_packages, setup

with open('migro/__init__.py', 'r') as fd:
    version = re.search(r"^__version__\s*=\s*['\']([^'\']*)['\']",
                        fd.read(), re.MULTILINE).group(1)

long_description = open('README.rst', encoding='utf-8').read()


setup(
    name='uploadcare-migro',
    version=version,
    description='Uploadcare migration tool',
    long_description=long_description,
    url='https://github.com/uploadcare/migro',
    license='MIT',
    author='Uploadcare team',
    author_email='hello@uploadcare.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'migro = migro.cli:cli',
        ]
    },
    zip_safe=False,
    install_requires=[
        'aiohttp==3.13.3',
        'click==8.3.1',
        'python-dateutil==2.9.0.post0',
        'tqdm==4.67.3',
        'colorama==0.4.6',
        'boto3==1.42.58',
        'botocore==1.42.95',
        'python-dotenv==1.2.1'
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ]
)
