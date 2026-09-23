"""The two kinds of failure a run itself can raise. Imports nothing."""


class ReadinessError(Exception):
    """Something the run needed was missing, found before the model answered."""


class RuntimeFailure(Exception):
    """The run reached the model, and its answer could not be used."""
