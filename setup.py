from setuptools import setup, find_packages


setup(
    name='app',
    version='0.0.1.dev1',
    description='API',
    platforms=['POSIX'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'init_models = db.base:run_init_models',
            'init_db = db.create:run_init_db',
        ]
    }
)

