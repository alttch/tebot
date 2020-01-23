__version__ = '0.2.4'

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='tebot',
    version=__version__,
    author='Altertech',
    author_email='div@altertech.com',
    description='Telegram bot library for Python and humans',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alttch/tebot',
    packages=setuptools.find_packages(),
    license='MIT',
    install_requires=['neotasker', 'filetype'],
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries',
    ),
)
