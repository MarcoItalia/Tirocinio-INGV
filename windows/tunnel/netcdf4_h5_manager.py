from netCDF4 import Dataset  # pylint: disable=no-name-in-module
import numpy as np
import config_manager


# ── Standalone read helpers ──────────────────────────────

def read_first_variable(group) -> Dataset:
    """Recursively walk HDF5 groups until the first variable is found."""
    if group.variables:
        return next(iter(group.variables.values()))
    for grp in group.groups.values():
        result = read_first_variable(grp)
        if result is not None:
            return result
    return None


def read_attribute(path_netcdf, attr: str = "dt"):
    """Read a named attribute from the first group of an HDF5 file."""
    def _search(ds):
        for group in ds.groups.values():
            try:
                return group.getncattr(attr)
            except AttributeError:
                pass
        return None

    if isinstance(path_netcdf, str):
        with Dataset(path_netcdf, "r") as file_read:
            return _search(file_read)
    elif isinstance(path_netcdf, Dataset):
        return _search(path_netcdf)
    return None


# ── Stitcher ────────────────────────────────────────────────────────────────────

class H5Stitcher:
    """
    Incrementally stitches multiple single-second HDF5 acquisitions into a
    single output file.

    Usage
    -----
    >>> with Dataset("download_incomplete.tmp", "w") as file_write:
    ...     stitcher = H5Stitcher(file_write)
    ...     for file_path in chunk_paths:
    ...         with Dataset(file_path, "r") as file_read:
    ...             stitcher.append(file_read, timestamp, dt)
    """

    def __init__(self, file_write: Dataset):
        """
        Parameters
        ----------
        file_write : netCDF4.Dataset
            An already-open, writable Dataset (e.g. opened with mode 'w').
            If it already contains a "dataset" group (e.g. resuming a
            partially-written file), the stitcher appends to it instead
            of re-initialising.
        """
        self.file_write = file_write

        config = config_manager.yaml_read("config.yaml")
        data_window = config.data_window

        self.leave_untouched = data_window.leave_file_untouched
        if self.leave_untouched:
            self.overlap = 0
        else:
            self.overlap = data_window.overlap
            # NOTE: these are ABSOLUTE channel numbers, referring to the
            # original (uncutted) acquisition — e.g. 150-300. They are
            # converted to local array indices in _initialize, once we know
            # the source chunk's own Channel_start (src_channel_start).
            self.config_channel_start = data_window.channels_start
            self.config_channel_end = data_window.channels_end + 1  # exclusive

        # local slicing indices (into the array as received) — resolved on
        # the first append, for both fresh and resumed files
        self.channel_start = None
        self.channel_end = None
        self._channel_range_resolved = False

        self.location = data_window.location

        self.group = None
        self.variable = None
        self.position = 0
        self.initialized = "dataset" in file_write.groups

        if self.initialized:
            self.group = file_write.groups["dataset"]
            self.variable = self.group.variables["StrainRate"]
            self.position = self.variable.shape[0]

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, file_read: Dataset, timestamp, dt) -> None:
        """
        Read the first variable from `file_read` and append it to the
        output file at the next available time position.

        Parameters
        ----------
        file_read : netCDF4.Dataset
            An open, readable Dataset for a single-second chunk.
        timestamp : float
            Acquisition start time (Unix seconds) — written once on
            initialisation.
        dt : numeric
            Time step in milliseconds for this chunk — accumulated into
            "dt_millisec" on every append after the first.
        """
        dataset = read_first_variable(file_read)

        if not self._channel_range_resolved:
            src_channel_start = read_attribute(file_read, "Channel_start")
            self._resolve_channel_range(dataset, src_channel_start)
            self._channel_range_resolved = True
        else:
            src_channel_start = None  # not needed again

        if not self.initialized:
            self._initialize(dataset, timestamp, dt, src_channel_start)

        self._assign(dataset)
        # self.position += dataset.shape[0]
        self.position += 1

    # ── Internals ─────────────────────────────────────────────────────────────

    def _resolve_channel_range(self, dataset, src_channel_start) -> None:
        """
        Resolve local slicing indices (into the array as received).

        - leave_file_untouched: take the whole channel range of the dataset.
        - otherwise: config.channels_start/end are ABSOLUTE channel numbers
          (referring to the original acquisition). Convert them to local
          indices by subtracting the source chunk's own Channel_start, then
          clip to the dataset's actual size as a safety net.
        """
        if self.leave_untouched:
            self.channel_start = 0
            self.channel_end = dataset.shape[-1]
            return

        src_start = int(
            src_channel_start) if src_channel_start is not None else 0

        local_start = self.config_channel_start - src_start
        local_end = self.config_channel_end - src_start

        n_channels = dataset.shape[-1]
        local_start = max(0, min(local_start, n_channels))
        local_end = max(local_start, min(local_end, n_channels))

        if local_end == local_start:
            raise ValueError(
                f"Configured channel range [{self.config_channel_start}, "
                f"{self.config_channel_end - 1}] does not overlap with the "
                f"source chunk's channel range [{src_start}, "
                f"{src_start + n_channels - 1}]"
            )

        self.channel_start = local_start
        self.channel_end = local_end

    def _initialize(self, dataset, timestamp, dt, src_channel_start) -> None:
        # translate local slicing indices back into absolute channel numbers
        # using the source chunk's own Channel_start attribute
        src_start = int(
            src_channel_start) if src_channel_start is not None else 0
        abs_channel_start = src_start + self.channel_start
        abs_channel_end = src_start + self.channel_end - 1

        self.group = self.file_write.createGroup("dataset")
        self.group.setncattr("Timestamp", timestamp)
        self.group.setncattr("Channel_start", np.short(abs_channel_start))
        self.group.setncattr("Channel_end", np.short(abs_channel_end))
        self.group.setncattr("Location", self.location)
        self.group.setncattr("dt_millisec", np.short(dt))

        if dataset.ndim == 2:
            n_freq = dataset.shape[0] - self.overlap
        else:
            n_freq = dataset.shape[1] - self.overlap

        # if check_for_dim == 2:
        #   no time
        #   freq_dim = self.group.createDimension("Frequences", None)
        time_dim = self.group.createDimension("Time", None)
        freq_dim = self.group.createDimension("Frequences", n_freq)
        chan_dim = self.group.createDimension(
            "Channels", self.channel_end - self.channel_start
        )
        # if check_for_dim ==2:
        # self.variable = self.group.createVariable(
        #    "StrainRate",
        #    datatype="float32",
        #    dimensions=(freq_dim, chan_dim),
        # )
        self.variable = self.group.createVariable(
            "StrainRate",
            datatype="float32",
            dimensions=(time_dim, freq_dim, chan_dim),
        )

        self.initialized = True

    # def _accumulate_dt(self, dt) -> None:
    #    current = np.short(self.group.getncattr("dt_millisec"))
    #    self.group.setncattr("dt_millisec", current + np.short(dt))

    def _assign(self, dataset) -> None:
        ch = slice(self.channel_start, self.channel_end)

        if dataset.ndim == 2:
            data = dataset[:-self.overlap,
                           ch] if self.overlap > 0 else dataset[:, ch]
        else:
            data = dataset[0, :-self.overlap,
                           ch] if self.overlap > 0 else dataset[0, :, ch]

        # self.variable[self.position:, : ] = data
        self.variable[self.position, :, :] = data
