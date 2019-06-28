from setuptools import setup

setup(name='funniest',
      version='0.1',
      description='converter from and to standoff',
      url='https://github.com/millawell/standoffconverter',
      author='David Lassner',
      author_email='lassner@tu-berlin.de',
      license='MIT',
      packages=['standoffconverter'],
      install_requires=[
          'lxml',
      ],
      zip_safe=False)
