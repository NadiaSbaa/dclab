"""RT-DC hdf5 format"""
from __future__ import annotations

import functools
import pathlib
from typing import Any, BinaryIO, Dict
import warnings

import h5py

from ...external.packaging import parse as parse_version
from ...util import hashobj, hashfile

from ..config import Configuration
from ..core import RTDCBase

from . import basins
from . import events
from . import logs
from . import tables


class OldFormatNotSupportedError(BaseException):
    pass


class UnknownKeyWarning(UserWarning):
    pass


class RTDC_HDF5(RTDCBase):
    def __init__(self,
                 h5path: str | pathlib.Path | BinaryIO,
                 h5kwargs: Dict[str, Any] = None,
                 *args,
                 **kwargs):
        """HDF5 file format for RT-DC measurements

        Parameters
        ----------
        h5path: str or pathlib.Path or file-like object
            Path to an '.rtdc' measurement file or a file-like object
        h5kwargs: dict
            Additional keyword arguments given to :class:`h5py.File`
        *args:
            Arguments for `RTDCBase`
        **kwargs:
            Keyword arguments for `RTDCBase`

        Attributes
        ----------
        path: pathlib.Path
            Path to the experimental HDF5 (.rtdc) file
        """
        super(RTDC_HDF5, self).__init__(*args, **kwargs)

        if isinstance(h5path, (str, pathlib.Path)):
            h5path = pathlib.Path(h5path)
        else:
            h5path = h5path

        self._hash = None
        self.path = h5path

        # In dclab 0.51.0, we introduced basins, a simple way of combining
        # HDF5-based datasets (including the :class:`.HDF5_S3` format)
        # *during* initialization. The idea is to be able to store parts
        # of the dataset (e.g. images) in a separate file that could then
        # be hosted on an S3 instance.
        self.h5file, fbasin = basins.initialize_basin_flooded_h5file(
            h5path, h5kwargs)
        self._features_basin += fbasin

        self._events = events.H5Events(self.h5file)

        # Parse configuration
        self.config = RTDC_HDF5.parse_config(h5path)

        # Override logs property with HDF5 data
        self.logs = logs.H5Logs(self.h5file)

        # Override the tables property with HDF5 data
        self.tables = tables.H5Tables(self.h5file)

        # check version
        rtdc_soft = self.config["setup"]["software version"]
        if rtdc_soft.startswith("dclab "):
            rtdc_ver = parse_version(rtdc_soft.split(" ")[1])
            if rtdc_ver < parse_version(MIN_DCLAB_EXPORT_VERSION):
                msg = "The file {} was created ".format(self.path) \
                      + "with dclab {} which is ".format(rtdc_ver) \
                      + "not supported anymore! Please rerun " \
                      + "dclab-tdms2rtdc / export the data again."
                raise OldFormatNotSupportedError(msg)

        self.title = "{} - M{}".format(self.config["experiment"]["sample"],
                                       self.config["experiment"]["run index"])

        # Set up filtering
        self._init_filters()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        # close the HDF5 file
        self.h5file.close()

    @functools.lru_cache()
    def __len__(self):
        ec = self.h5file.get("experiment:event count")
        if ec is not None:
            return ec
        else:
            return super(RTDC_HDF5, self).__len__()

    @property
    def _h5(self):
        warnings.warn("Access to the underlying HDF5 file is now public. "
                      "Please use the `h5file` attribute instead of `_h5`!",
                      DeprecationWarning)
        return self.h5file

    @staticmethod
    def can_open(h5path):
        """Check whether a given file is in the .rtdc file format"""
        h5path = pathlib.Path(h5path)
        if h5path.suffix == ".rtdc":
            return True
        else:
            # we don't know the extension; check for the "events" group
            canopen = False
            try:
                # This is a workaround for Python2 where h5py cannot handle
                # unicode file names.
                with h5path.open("rb") as fd:
                    h5 = h5py.File(fd, "r")
                    if "events" in h5:
                        canopen = True
            except IOError:
                # not an HDF5 file
                pass
            return canopen

    @staticmethod
    def parse_config(h5path):
        """Parse the RT-DC configuration of an HDF5 file"""
        with h5py.File(h5path, mode="r") as fh5:
            h5attrs = dict(fh5.attrs)

        # Convert byte strings to unicode strings
        # https://github.com/h5py/h5py/issues/379
        for key in h5attrs:
            if isinstance(h5attrs[key], bytes):
                h5attrs[key] = h5attrs[key].decode("utf-8")

        config = Configuration()
        for key in h5attrs:
            section, pname = key.split(":")
            config[section][pname] = h5attrs[key]
        return config

    @property
    def hash(self):
        """Hash value based on file name and content"""
        if self._hash is None:
            tohash = [self.path.name,
                      # Hash a maximum of ~1MB of the hdf5 file
                      hashfile(self.path, blocksize=65536, count=20)]
            self._hash = hashobj(tohash)
        return self._hash


#: rtdc files exported with dclab prior to this version are not supported
MIN_DCLAB_EXPORT_VERSION = "0.3.3.dev2"
