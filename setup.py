from setuptools import setup, find_packages


setup(
    name='rush_notificator_sdk',
    description='rush_notificator_sdk based on aiohttp',
    version='0.0.0',
    license='MIT',
    author="Alexey Dergunov",
    author_email='dergunovalexey2000@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/thealexeydergunov/rush_notificator_sdk.git',
    keywords='rush_notificator_sdk based on aiohttp',
    install_requires=[
        'aiohttp',
    ],
)
