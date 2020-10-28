import os
import setuptools

# Read long description
readme_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(readme_dir, 'README.md')) as readme:
    long_description = readme.read()

setuptools.setup(name='py2dm',
                 version='0.1.1',
                 description='Read and write 2DM mesh files',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://github.com/leonhard-s/Py2DM',
                 author='Leonhard S.',
                 classifiers=['Development Status :: 3 - Alpha',
                              'Intended Audience :: Developers',
                              'License :: OSI Approved :: MIT License',
                              'Programming Language :: Python :: 3',
                              'Programming Language :: Python :: 3.7',
                              'Programming Language :: Python :: 3 :: Only'],
                 packages=['py2dm'],
                 package_data={'py2dm': ['py.typed']},
                 keywords='mesh 2dm')
