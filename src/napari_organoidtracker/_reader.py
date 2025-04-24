"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""

import json
from typing import Any, Dict, List

from napari_organoidtracker import _experiment
from napari_organoidtracker._basics import TimePoint
from napari_organoidtracker._experiment import Experiment
from napari_organoidtracker._links import Links, LinkingTrack
from napari_organoidtracker._position import Position
from napari_organoidtracker._position_data import PositionData


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
        return_list += _experiment._experiment_to_napari(experiment)
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

    version = data.get("version", "v1")
    if version == "v1":
        if "shapes" in data:
            # Deprecated, nowadays stored in "positions"
            _parse_simple_position_format(experiment, data["shapes"])
        elif "positions" in data:
            _parse_simple_position_format(experiment, data["positions"])

        if "links" in data:
            _parse_d3_links_format(experiment, data["links"])
        elif "links_scratch" in data:  # Deprecated, was used back when experiments could hold multiple linking sets
            _parse_d3_links_format(experiment, data["links_scratch"])
        elif "links_baseline" in data:  # Deprecated, was used back when experiments could hold multiple linking sets
            _parse_d3_links_format(experiment, data["links_baseline"])
    elif version == "v2":
        if "positions" in data:
            _parse_positions_and_meta_format(experiment, data["positions"])
        _parse_tracks_and_meta_format(experiment, data["tracks"])
    else:
        raise ValueError(
            "Unknown data version",
            "This plugin is not able to load data of version " + str(data["version"]) + ".",
        )

    return experiment


def _parse_d3_links_format(experiment: Experiment, links_json: Dict[str, Any]):
    """Parses a node_link_graph and adds all links and positions to the experiment."""
    links = Links()
    position_data = PositionData()
    _add_d3_data(position_data, links, links_json)
    links.sort_tracks_by_x()
    experiment.position_data = position_data
    experiment.links = links


def _add_d3_data(position_data: PositionData, links: Links, links_json: Dict):
    """Adds data in the D3.js node-link format. Used for deserialization."""

    # Add position data
    for node in links_json["nodes"]:
        if len(node.keys()) == 1:
            # No extra data found
            continue
        position = _parse_position(node["id"])
        for data_key, data_value in node.items():
            if data_key == "id":
                continue
            position_data.set_position_data(position, data_key, data_value)

    # Add links
    for link in links_json["links"]:
        source = _parse_position(link["source"])
        target = _parse_position(link["target"])
        links.add_link(source, target)

        # Now that we have a link, we can add link and lineage data
        for data_key, data_value in link.items():
            if data_key.startswith("__lineage_"):
                # Lineage metadata, store it
                links.set_lineage_data(links.get_track(source), data_key[len("__lineage_"):], data_value)


def _parse_position(json_structure: Dict[str, Any]) -> Position:
    if "_time_point_number" in json_structure:
        return Position(
            json_structure["x"],
            json_structure["y"],
            json_structure["z"],
            time_point_number=json_structure["_time_point_number"],
        )
    return Position(json_structure["x"], json_structure["y"], json_structure["z"])


def _parse_simple_position_format(experiment: Experiment, json_structure: Dict[str, List]):
    positions = experiment.positions

    for time_point_number, raw_positions in json_structure.items():
        time_point_number = int(time_point_number)  # str -> int

        for raw_position in raw_positions:
            position = Position(*raw_position[0:3], time_point_number=time_point_number)
            positions.add(position)


def _parse_positions_and_meta_format(experiment: Experiment, positions_json: List[Dict]):
    positions = experiment.positions

    for time_point_json in positions_json:
        time_point_number = time_point_json["time_point"]

        has_meta = "position_meta" in time_point_json
        positions_of_time_point = list() if has_meta else None
        for raw_position in time_point_json["coords_xyz_px"]:
            position = Position(*raw_position, time_point_number=time_point_number)
            positions.add(position)
            if positions_of_time_point is not None:
                positions_of_time_point.append(position)

        if has_meta:
            experiment.position_data.add_data_from_time_point_dict(TimePoint(time_point_number), positions_of_time_point,
                                                                   time_point_json["position_meta"])


def _parse_tracks_and_meta_format(experiment: Experiment, tracks_json: List[Dict]):
    links = experiment.links

    # Iterate a first time to add the tracks
    for track_json in tracks_json:
        time_point_number_start = track_json["time_point_start"]
        time_point_number_end = time_point_number_start + len(track_json["coords_xyz_px"]) - 1

        coords_xyz_px = track_json["coords_xyz_px"]
        positions_of_track = list()
        min_index = 0
        max_index = len(coords_xyz_px) - 1
        for i in range(min_index, max_index + 1):
            position = Position(*coords_xyz_px[i], time_point_number=time_point_number_start + i)
            positions_of_track.append(position)
        track = LinkingTrack(positions_of_track)
        links.add_track(track)

        # Handle lineage metadata
        if "lineage_meta" in track_json:
            for metadata_key, metadata_value in track_json["lineage_meta"].items():
                links.set_lineage_data(track, metadata_key, metadata_value)

    # Iterate again to add connections to previous tracks
    for track_json in tracks_json:
        if "coords_xyz_px_before" not in track_json:
            continue
        time_point_number_start = track_json["time_point_start"]

        position_first = Position(*track_json["coords_xyz_px"][0], time_point_number=time_point_number_start)
        for i, raw_position in enumerate(track_json["coords_xyz_px_before"]):
            # Connect the tracks
            position_previous_track = Position(*raw_position, time_point_number=time_point_number_start - 1)
            previous_track = links.get_track(position_previous_track)
            current_track = links.get_track(position_first)
            links.connect_tracks(previous=previous_track, next=current_track)

