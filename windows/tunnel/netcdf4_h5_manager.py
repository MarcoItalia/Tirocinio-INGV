from os import replace
from netCDF4 import Dataset  # pylint: disable=no-name-in-module
from yaml_manager import yaml_read
import numpy as np


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
                attr_value = group.getncattr(attr)
                if attr_value is not None:
                    return attr_value
            except AttributeError:
                pass
            attr_value = _search(group)
            if attr_value is not None:
                return attr_value
        return None

    if isinstance(path_netcdf, str):
        with Dataset(path_netcdf, "r") as file_read:
            return _search(file_read)
    elif isinstance(path_netcdf, Dataset):
        return _search(path_netcdf)
    return None


# ── Function to optimize ──────────────────────────────


def _minimize_int_type(value) -> type:
    """
    Return the smallest numpy integer type that can represent the value.
    Order: int8 → int16 → int32 → int64
    """
    for dtype in [np.int8, np.int16, np.int32, np.int64]:
        info = np.iinfo(dtype)
        if info.min <= value <= info.max:
            return dtype
    return np.int64  # fallback


def optimize_memory(value):
    """
    Reduce the memory footprint of a value by casting it to the smallest
    compatible type.
    Supports scalar integers (int, np.integer) and lists.
    Floats and other types are returned unchanged.
    Parameters
    ----------
    value : int | np.integer | list | any
        The value to optimize.

    Returns
    -------
    new_type : type
        The type of the optimized value (e.g. np.int16, list).
        For unchanged types, returns the original type of value.
    value : int | np.integer | list | any
        The value cast to the smallest compatible type.
        For lists, each integer element is individually optimized.
        Non-integer values are returned unchanged.
    """
    new_type = type(value)
    if isinstance(value, int) or isinstance(value, np.integer):
        new_type = _minimize_int_type(value)
    elif isinstance(value, list):
        new_list = []
        for item in value:
            if isinstance(item, int) or isinstance(item, np.integer):
                new_type = _minimize_int_type(item)
                new_list.append(new_type(item))
            else:
                new_list.append(item)
        value = new_list
        new_type = list
    return new_type, value


# ── Stitcher ────────────────────────────────────────────────────────────────────


class H5Stitcher:
    """
    Incrementally stitches multiple single-second HDF5 acquisitions into a
    single output file.

    Usage
    -----
    >>> with Dataset("download_incomplete.tmp", "w") as file_write:
    ...     stitcher = H5Stitcher(file_write, True)
    ...     for file_path in list_file_dir:
    ...         with Dataset(file_path, "r") as file_read:
    ...             stitcher.append(file_read, timestamp, dt)
    """

    def __init__(self, file_write: Dataset, add_info: bool = False):
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
        self.add_info = {}
        config = yaml_read("config.yaml")
        if add_info:
            try:
                self.add_info = yaml_read(
                    f"{config["paths"]["info_dir"]}/_add_info.yaml")
            except (FileNotFoundError, IOError):
                pass
        data_window = config["data_window"]

        self.leave_untouched = data_window["leave_file_untouched"]
        if self.leave_untouched:
            self.overlap = 0
        else:
            self.overlap = data_window["overlap"]
            # NOTE: these are ABSOLUTE channel numbers, referring to the
            # original (uncutted) acquisition — e.g. 150-300. They are
            # converted to local array indices in _initialize, once we know
            # the source chunk's own Channel_start (src_channel_start).
            self.config_channel_start = data_window["channels_start"]
            # exclusive
            self.config_channel_end = data_window["channels_end"] + 1

        # local slicing indices (into the array as received) — resolved on
        # the first append, for both fresh and resumed files
        self.channel_start = None
        self.channel_end = None
        self._channel_range_resolved = False

        self.location = data_window["location"]

        self.group = None
        self.variable = None
        self.position = 0
        self.initialized = "dataset" in file_write.groups

        if self.initialized:
            self.group = file_write.groups["dataset"]
            self.variable = self.group.variables["StrainRate"]
            self.position = self.variable.shape[0]

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, file_read, timestamp, dt) -> None:
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
        if isinstance(file_read, Dataset):
            dataset = read_first_variable(file_read)
        elif isinstance(file_read, np.ndarray):
            dataset = file_read
        elif isinstance(file_read, list):
            dataset = file_read
        else:
            return None

        if not self._channel_range_resolved:
            src_channel_start = read_attribute(file_read, "Channel_start")
            self._resolve_channel_range(dataset, src_channel_start)
            self._channel_range_resolved = True
        else:
            src_channel_start = None  # not needed again

        if not self.initialized:
            self._initialize(timestamp, dt, src_channel_start)

        written_lines = self._assign(dataset)
        self.position += written_lines

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

    def _initialize(self, timestamp, dt, src_channel_start) -> None:
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
        if self.add_info:
            for key, value in self.add_info.items():
                new_type, value = optimize_memory(value)
                self.group.setncattr(key, new_type(value))

        time_dim = self.group.createDimension("Time", None)
        chan_dim = self.group.createDimension(
            "Channels", self.channel_end - self.channel_start
        )

        self.variable = self.group.createVariable(
            "StrainRate",
            datatype="float32",
            dimensions=(time_dim, chan_dim),
        )
        self.initialized = True

    def _assign(self, dataset) -> None:
        ch = slice(self.channel_start, self.channel_end)

        if dataset.ndim == 2:
            data = dataset[:-self.overlap,
                           ch] if self.overlap > 0 else dataset[:, ch]
        else:
            data = dataset[0, :-self.overlap,
                           ch] if self.overlap > 0 else dataset[0, :, ch]

        self.variable[self.position: self.position +
                      data.shape[0], :] = data
        return data.shape[0]

# ── Compatibility Wrapper ────────────────────────────────────────────────────────────────────


def h5_file_write(path_netcdf, file_read, timestamp, dt):
    """
    Backward-compatible single-shot writer.
    """
    if isinstance(path_netcdf, str):
        pos_ext = path_netcdf.find(".h5")
        if pos_ext == -1:
            raise ValueError
        file_write = Dataset("temp_file.tmp", "w")
    elif isinstance(path_netcdf, Dataset):
        file_write = path_netcdf
    else:
        raise ValueError

    stitcher = H5Stitcher(file_write)
    stitcher.append(file_read, timestamp, dt)

    if isinstance(path_netcdf, str):
        file_write.close()
        replace("temp_file.tmp", path_netcdf)
