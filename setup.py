from setuptools import setup

setup(
    name='mpbridge',
    version='0.0.0',
    author='Alistair Buxton',
    author_email='a.j.buxton@gmail.com',
    url='https://github.com/ali1234/32blit-mpbridge',
    packages=['mpbridge'],
    entry_points={
        'console_scripts': [
            'mpbridge = mpbridge.main:main',
        ]
    },
    install_requires=['click', 'trio', 'anyio_serial>=0.1.4'],
)
