"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""

import json
from typing import Any, Dict, List, Tuple

from napari_organoidtracker import _experiment
from napari_organoidtracker._experiment import Experiment
from napari_organoidtracker._links import Links
from napari_organoidtracker._position import Position


def napari_get_reader(path):
    """A basic implementation of a Reader contribution.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]

    # if we know we cannot read the file, we immediately return None.
    if not path.endswith(".aut"):
        return None

    # otherwise we return the *function* that can read ``path``.
    return reader_function


def reader_function(input_path):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    input_path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer. Both "meta", and "layer_type" are optional. napari will
        default to layer_type=="image" if not provided
    """
    # handle both a string and a list of strings
    paths = [input_path] if isinstance(input_path, str) else input_path

    return_list = []
    for path in paths:
        experiment = _read_organoidtracker_file(path)
        return_list += _experiment.experiment_to_napari(experiment)
    return return_list


def _read_organoidtracker_file(filepath) -> Experiment:
    """Read a .aut file and return the data as a parsed Experiment object.
    """
    experiment = Experiment()

    with open(filepath) as handle:
        data = json.load(handle)

    if "version" not in data and "family_scores" not in data:
        # We don't have a general data file, but a specialized one
        raise ValueError(
            "Unknown file format",
            "This plugin is not able to load this AUT file: it is missing the version tag.",
        )

    if data.get("version", "v1") != "v1":
        raise ValueError(
            "Unknown data version",
            "This plugin is not able to load data of version " + str(data["version"]) + ".",
        )

    # if "shapes" in data:
    # Deprecated, nowadays stored in "positions"
    # _parse_position_format(experiment, data["shapes"], min_time_point, max_time_point)
    # elif "positions" in data:
    # _parse_position_format(experiment, data["positions"], min_time_point, max_time_point)

    if "links" in data:
        _parse_links_format(experiment, data["links"])
    elif "links_scratch" in data:  # Deprecated, was used back when experiments could hold multiple linking sets
        _parse_links_format(experiment, data["links_scratch"])
    elif "links_baseline" in data:  # Deprecated, was used back when experiments could hold multiple linking sets
        _parse_links_format(experiment, data["links_baseline"])

    return experiment


def _parse_links_format(experiment: Experiment, links_json: Dict[str, Any]):
    """Parses a node_link_graph and adds all links and positions to the experiment."""
    links = Links()
    _add_d3_data(links, links_json)
    links.sort_tracks_by_x()
    experiment.links = links


def _add_d3_data(links: Links, links_json: Dict):
    """Adds data in the D3.js node-link format. Used for deserialization."""

    # Add links
    for link in links_json["links"]:
        source = _parse_position(link["source"])
        target = _parse_position(link["target"])
        links.add_link(source, target)

        # Now that we have a link, we can add link and lineage data
        for data_key, data_value in link.items():
            if data_key.startswith("__lineage_"):
                # Lineage metadata, store it
                links.set_lineage_data(
                    links.get_track(source),
                    data_key[len("__lineage_"):],
                    data_value,
                )


def _parse_position(json_structure: Dict[str, Any]) -> Position:
    if "_time_point_number" in json_structure:
        return Position(
            json_structure["x"],
            json_structure["y"],
            json_structure["z"],
            time_point_number=json_structure["_time_point_number"],
        )
    return Position(json_structure["x"], json_structure["y"], json_structure["z"])
