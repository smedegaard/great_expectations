from __future__ import annotations

import logging
import warnings
from typing import Callable, Iterator, Sequence

import pandas as pd

from great_expectations.compatibility import sqlalchemy

logger = logging.getLogger(__name__)


def read_sql_table_as_df(
    table_name,
    con,
    schema=None,
    index_col: str | Sequence[str] | None = None,
    coerce_float: bool = True,
    parse_dates=None,
    columns=None,
    chunksize: int | None = None,
) -> pd.DataFrame | Iterator[pd.DataFrame]:
    """Read SQL table as DataFrame.

    Wrapper for `read_sql_table()` method in Pandas. Created as part of the effort to allow GX to be compatible
    with SqlAlchemy 2, and is used to suppress warnings that arise from implicit auto-commits.

    Args:
        table_name (str): name of SQL Table.
        con (sqlalchemy engine or connection): sqlalchemy.engine or sqlite3.Connection
        schema (str | None): Specify the schema (if database flavor supports this). If None, use
            default schema. Defaults to None.
        index_col (str | Sequence[str] | None): Column(s) to set as index(MultiIndex).
        coerce_float (bool): If True, method to convert values of non-string, non-numeric objects (like
            decimal.Decimal) to floating point. Can result in loss of Precision.
        parse_dates (List or Dict): list or dict, default None
            - List of column names to parse as dates.
            - Dict of ``{column_name: format string}`` where format string is
                strftime compatible in case of parsing string times or is one of
                (D, s, ns, ms, us) in case of parsing integer timestamps.
            - Dict of ``{column_name: arg dict}``, where the arg dict corresponds
                to the keyword arguments of :func:`pandas.to_datetime`
                Especially useful with databases without native Datetime support,
                such as SQLite.
        columns: List of column names to select from SQL table.
        chunksize: If specified, returns an iterator where `chunksize` is the number of
            rows to include in each chunk.
    """
    if sqlalchemy.Engine and isinstance(con, sqlalchemy.Engine):
        con = con.connect()
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", category=DeprecationWarning)
        return pd.read_sql_table(
            table_name=table_name,
            con=con,
            schema=schema,
            index_col=index_col,
            coerce_float=coerce_float,
            parse_dates=parse_dates,
            columns=columns,
            chunksize=chunksize,
        )


def add_dataframe_to_db(
    df: pd.DataFrame,
    name: str,
    con,
    schema=None,
    if_exists: str = "fail",
    index: bool = True,
    index_label: str | None = None,
    chunksize: int | None = None,
    dtype: dict | None = None,
    method: str | Callable | None = None,
) -> None:
    """Write records stored in a DataFrame to a SQL database.

    Wrapper for `to_sql()` method in Pandas. Created as part of the effort to allow GX to be compatible
    with SqlAlchemy 2, and is used to suppress warnings that arise from implicit auto-commits.

    The need for this function will eventually go away once we migrate to Pandas 1.4.0.

    Args:
        df (pd.DataFrame): DataFrame to load into the SQL Table.
        name (str): name of SQL Table.
        con (sqlalchemy engine or connection): sqlalchemy.engine or sqlite3.Connection
        schema (str | None): Specify the schema (if database flavor supports this). If None, use
            default schema. Defaults to None.
        if_exists (str | None): Can be either 'fail', 'replace', or 'append'. Defaults to `fail`.
            * fail: Raise a ValueError.
            * replace: Drop the table before inserting new values.
            * append: Insert new values to the existing table.
        index (bool): Write DataFrame index as a column. Uses `index_label` as the column
            name in the table. Defaults to True.
        index_label (str | None):
            Column label for index column(s). If None is given (default) and
            `index` is True, then the index names are used.
        chunksize (int | None):
            Specify the number of rows in each batch to be written at a time.
            By default, all rows will be written at once.
        dtype (dict | int | float | bool | None):
            Specifying the datatype for columns. If a dictionary is used, the
            keys should be the column names and the values should be the
            SQLAlchemy types or strings for the sqlite3 legacy mode. If a
            scalar is provided, it will be applied to all columns.
        method (str | Callable | None):
            Controls the SQL insertion clause used:
                * None : Uses standard SQL ``INSERT`` clause (one per row).
                * 'multi': Pass multiple values in a single ``INSERT`` clause.
                * callable with signature ``(pd_table, conn, keys, data_iter)``.
    """
    with warnings.catch_warnings():
        # Note that RemovedIn20Warning is the warning class that we see from sqlalchemy
        # but using the base class here since sqlalchemy is an optional dependency and this
        # warning type only exists in sqlalchemy < 2.0.
        warnings.filterwarnings(action="ignore", category=DeprecationWarning)
        df.to_sql(
            name=name,
            con=con,
            schema=schema,
            if_exists=if_exists,
            index=index,
            index_label=index_label,
            chunksize=chunksize,
            dtype=dtype,
            method=method,
        )
