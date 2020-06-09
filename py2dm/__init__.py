"""The Py2DM module provides read and write support for 2DM mesh files.

Visit the project repository at https://github.com/leonhard-s/Py2DM for
detailed usage instructions and to provide feedback.

For additional information on the 2DM format, refer to the 2DM file
format specification at
https://www.xmswiki.com/wiki/SMS:2D_Mesh_Files_*.2dm.
"""

from . import errors
from .read import Reader
from .write import Writer

__version__ = '0.1.0a'
