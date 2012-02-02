from distutils.core import setup

import github3

setup(

    name='py_github3',

    version=github3.__version__,
    description=github3.__doc__,
    long_description=open('README.txt').read(),
    author=github3.__author__,
    author_email=github3.__contact__,
    url=github3.__homepage__,
    packages=['github3'],
    license='LICENSE.txt',
    install_requires=[
        "requests == 0.8.5",
    ],
)
