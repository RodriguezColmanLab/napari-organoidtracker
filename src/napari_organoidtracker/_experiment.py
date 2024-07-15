from typing import List, Tuple, Dict

import numpy

from napari_organoidtracker._links import Links


class Experiment:
    links: Links

    def __init__(self):
        self.links = Links()


def experiment_to_napari(experiment: Experiment) -> List[Tuple[numpy.ndarray, Dict, str]]:
    """Convert an Experiment object to the Napari format.

    The track layer format of Napari is documented at https://napari.org/stable/howtos/layers/tracks.html .
    """

    links = experiment.links
    positions_table = []  # Each row is [track_id, t, z, y, z], ordered by track_id and then t
    linking_graph = {}
    for track_id, track in links.find_all_tracks_and_ids():
        for position in track.positions():
            positions_table.append(
                [
                    track_id,
                    position.time_point_number(),
                    position.z,
                    position.y,
                    position.x,
                ]
            )

        previous_track_ids = [
            links.get_track_id(previous_track)
            for previous_track in track.get_previous_tracks()
        ]
        linking_graph[track_id] = previous_track_ids

    # Move all time points so that we start at time point 0 (OrganoidTracker can start at any time point number, but
    # Napari always starts at 0)
    positions_table = numpy.array(positions_table, dtype=numpy.float32)
    positions_table[:, 1] -= positions_table[:, 1].min()

    return [(positions_table, {"graph": linking_graph}, "tracks")]
