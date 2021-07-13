# type: ignore

import os
import setuptools

from py2dm import __version__ as version

# Read long description
readme_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(readme_dir, 'README.md')) as readme:
    long_description = readme.read()

# Create C extension
c_parser = setuptools.Extension(
    'py2dm._parser._cparser', ['src/_cparser.cpp'], optional=True)

setuptools.setup(name='py2dm',
                 version=version,
                 description='Read and write 2DM mesh files',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://github.com/leonhard-s/Py2DM',
                 author='Leonhard S.',
                 classifiers=['Development Status :: 4 - Beta',
                              'Intended Audience :: Developers',
                              'License :: OSI Approved :: MIT License',
                              'Programming Language :: Python :: 3.6',
                              'Programming Language :: Python :: 3.7',
                              'Programming Language :: Python :: 3.8',
                              'Programming Language :: Python :: 3.9',
                              'Programming Language :: Python :: 3.10',
                              'Programming Language :: Python :: 3 :: Only'],
                 packages=['py2dm', 'py2dm._parser'],
                 package_data={'py2dm': ['py.typed'],
                               'py2dm._parser': ['_cparser.pyi']},
                 keywords='mesh 2dm',
                 ext_modules=[c_parser])
