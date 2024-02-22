from setuptools import setup, find_namespace_packages

setup(
    name='our_bot_pg15',
    version='0.2',
    url='',
    license='',
    author='',
    author_email='',
    description='',
    entry_points={'console_scripts': ['bot_pg15 = Bot.v2.main:main']},
    packages=find_namespace_packages(),
    install_requires=[
        'prompt_toolkit',
        'pygame',
    ],
)
