import os

from napari_organoidtracker import napari_get_reader


def test_reader():
    """An example of how you might test your plugin."""

    my_test_file = os.path.join(os.path.dirname(__file__), "nd410xy01.aut")

    # try to read it back in
    reader = napari_get_reader(my_test_file)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data_list = reader(my_test_file)
    assert isinstance(layer_data_list, list) and len(layer_data_list) > 0
    layer_data_tuple = layer_data_list[0]

    # Make sure the tracks are in
    assert len(layer_data_tuple[1]["graph"]) == 288

    assert layer_data_tuple[2] == "tracks"


def test_get_reader_pass():
    reader = napari_get_reader("fake.file")
    assert reader is None
