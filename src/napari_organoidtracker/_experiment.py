from random import random
from typing import List, Tuple, Dict, Iterable

import numpy

from napari_organoidtracker._links import Links
from napari_organoidtracker._position_collection import PositionCollection
from napari_organoidtracker._position_data import PositionData


class Experiment:
    links: Links
    positions: PositionCollection
    position_data: PositionData

    def __init__(self):
        self.links = Links()
        self.positions = PositionCollection()
        self.position_data = PositionData()


def _get_str_float_bool_metadata_keys(position_data: PositionData) -> Iterable[str]:
    """Get the metadata keys of values that are floats or booleans."""
    for metadata_key, metadata_type in position_data.get_data_names_and_types().items():
        if metadata_type == bool or metadata_type == float or metadata_type == int or metadata_type == str:
            yield metadata_key


def _experiment_to_napari(experiment: Experiment) -> List[Tuple[numpy.ndarray, Dict, str]]:
    """Convert an Experiment object to the Napari format.

    The track layer format of Napari is documented at https://napari.org/stable/howtos/layers/tracks.html .
    """

    links = experiment.links
    positions_table = []  # Each row is [track_id, t, z, y, x], ordered by track_id and then t
    metadata = dict()
    for metadata_key in _get_str_float_bool_metadata_keys(experiment.position_data):
        metadata[metadata_key] = []

    linking_graph = {}
    for track_id, track in links.find_all_tracks_and_ids():
        for position in track.positions():
            # Build positions table
            positions_table.append(
                [
                    track_id,
                    position.time_point_number(),
                    position.z,
                    position.y,
                    position.x,
                ]
            )

            # Build metadata dictionary
            for metadata_key, metadata_values in metadata.items():
                metadata_value = experiment.position_data.get_position_data(position, metadata_key)
                if isinstance(metadata_value, str):
                    metadata_value = abs(hash(metadata_value)) % 1000
                if metadata_value is None or not isinstance(metadata_value, (bool, float, int)):
                    metadata_values.append(0)
                else:
                    metadata_values.append(metadata_value)

        previous_track_ids = [
            links.get_track_id(previous_track)
            for previous_track in track.get_previous_tracks()
        ]
        linking_graph[track_id] = previous_track_ids

    output_array = []

    if experiment.links.has_links():
        positions_table = numpy.array(positions_table, dtype=numpy.float32)

        # Move all time points so that we start at time point 0 (OrganoidTracker can start at any time point number, but
        # Napari always starts at 0)
        positions_table[:, 1] -= positions_table[:, 1].min()

        # Remove the Z column if all values are 0 (then we have 2D tracking data)
        if numpy.all(positions_table[:, 2] == 0):
            positions_table = numpy.delete(positions_table, 2, axis=1)
            print("Removed Z column from tracking data because all values were 0.")
        else:
            print("Z column was not removed from tracking data because not all values were 0.")

        output_array.append((positions_table, {"graph": linking_graph, "features": metadata}, "tracks"))

    return output_array
