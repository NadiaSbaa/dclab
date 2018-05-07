#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
from os.path import join
import shutil
import tempfile

import numpy as np
import pytest

import dclab
from dclab import dfn, new_dataset

from helper_methods import example_data_dict, retrieve_data, \
    example_data_sets, cleanup


@pytest.mark.filterwarnings('ignore::UserWarning')
def test_avi_export():
    ds = new_dataset(retrieve_data(example_data_sets[1]))
    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.avi")
    ds.export.avi(path=f1)
    assert os.stat(
        f1)[6] > 1e4, "Resulting file to small, Something went wrong!"
    shutil.rmtree(edest, ignore_errors=True)
    cleanup()


def test_avi_override():
    ds = new_dataset(retrieve_data(example_data_sets[1]))

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.avi")
    ds.export.avi(f1, override=True)
    try:
        ds.export.avi(f1[:-4], override=False)
    except OSError:
        pass
    else:
        raise ValueError("Should append .avi and not override!")

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)
    cleanup()


def test_avi_no_images():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=127, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.avi")
    try:
        ds.export.avi(f1)
    except OSError:
        pass
    else:
        raise ValueError("There should be no image data to write!")
    shutil.rmtree(edest, ignore_errors=True)


def test_fcs_export():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=222, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.fcs")
    f2 = join(edest, "test_unicode.fcs")

    ds.export.fcs(f1, keys, override=True)
    ds.export.fcs(f2, [u"area_um", u"deform", u"time",
                       u"frame", u"fl3_width"], override=True)

    with io.open(f1, mode="rb") as fd:
        a1 = fd.read()

    with io.open(f2, mode="rb") as fd:
        a2 = fd.read()

    assert a1 == a2
    assert len(a1) != 0

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_fcs_override():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=212, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.fcs")
    ds.export.fcs(f1, keys, override=True)
    try:
        ds.export.fcs(f1[:-4], keys, override=False)
    except OSError:
        pass
    else:
        raise ValueError("Should append .fcs and not override!")

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_fcs_not_filtered():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=127, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.tsv")
    ds.export.fcs(f1, keys, filtered=False)

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_hdf5():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=127, keys=keys)
    ds1 = dclab.new_dataset(ddict)
    ds1.config["experiment"]["sample"] = "test"

    edest = tempfile.mkdtemp()
    f1 = join(edest, "dclab_test_export_hdf5.rtdc")
    ds1.export.hdf5(f1, keys)

    ds2 = dclab.new_dataset(f1)
    assert ds1 != ds2
    assert np.allclose(ds2["area_um"], ds1["area_um"])
    assert np.allclose(ds2["deform"], ds1["deform"])
    assert np.allclose(ds2["time"], ds1["time"])
    assert np.allclose(ds2["frame"], ds1["frame"])
    assert np.allclose(ds2["fl3_width"], ds1["fl3_width"])

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_hdf5_filtered():
    N = 10
    keys = ["area_um", "image"]
    ddict = example_data_dict(size=N, keys=keys)
    ddict["image"][3] = np.arange(10 * 20, dtype=np.uint8).reshape(10, 20) + 22

    ds1 = dclab.new_dataset(ddict)
    ds1.config["experiment"]["sample"] = "test"
    ds1.filter.manual[2] = False
    ds1.apply_filter()
    fta = ds1.filter.manual.copy()

    edest = tempfile.mkdtemp()
    f1 = join(edest, "dclab_test_export_hdf5_filtered.rtdc")
    ds1.export.hdf5(f1, keys)

    ds2 = dclab.new_dataset(f1)

    assert ds1 != ds2
    assert np.allclose(ds2["area_um"], ds1["area_um"][fta])
    assert np.allclose(ds2["image"][2], ds1["image"][3])
    assert np.all(ds2["image"][2] != ds1["image"][2])

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_hdf5_contour_image_trace():
    N = 65
    keys = ["contour", "image", "trace"]
    ddict = example_data_dict(size=N, keys=keys)

    ds1 = dclab.new_dataset(ddict)
    ds1.config["experiment"]["sample"] = "test"

    edest = tempfile.mkdtemp()
    f1 = join(edest, "dclab_test_export_hdf5_image.rtdc")
    ds1.export.hdf5(f1, keys, filtered=False)
    ds2 = dclab.new_dataset(f1)

    for ii in range(N):
        assert np.all(ds1["image"][ii] == ds2["image"][ii])
        assert np.all(ds1["contour"][ii] == ds2["contour"][ii])

    for key in dfn.FLUOR_TRACES:
        assert np.all(ds1["trace"][key] == ds2["trace"][key])

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_hdf5_override():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=212, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.rtdc")
    ds.export.hdf5(f1, keys, override=True)
    try:
        ds.export.hdf5(f1[:-5], keys, override=False)
    except OSError:
        pass
    else:
        raise ValueError("Should append .rtdc and not override!")

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_tsv_export():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=222, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.tsv")
    f2 = join(edest, "test_unicode.tsv")

    ds.export.tsv(f1, keys, override=True)
    ds.export.tsv(f2, [u"area_um", u"deform", u"time",
                       u"frame", u"fl3_width"], override=True)

    with io.open(f1) as fd:
        a1 = fd.read()

    with io.open(f2) as fd:
        a2 = fd.read()

    assert a1 == a2
    assert len(a1) != 0

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_tsv_override():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=212, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.tsv")
    ds.export.tsv(f1, keys, override=True)
    try:
        ds.export.tsv(f1[:-4], keys, override=False)
    except OSError:
        pass
    else:
        raise ValueError("Should append .tsv and not override!")

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


def test_tsv_not_filtered():
    keys = ["area_um", "deform", "time", "frame", "fl3_width"]
    ddict = example_data_dict(size=127, keys=keys)
    ds = dclab.new_dataset(ddict)

    edest = tempfile.mkdtemp()
    f1 = join(edest, "test.tsv")
    ds.export.tsv(f1, keys, filtered=False)

    # cleanup
    shutil.rmtree(edest, ignore_errors=True)


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
