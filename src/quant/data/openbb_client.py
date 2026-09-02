from openbb import obb
from openbb_core.app.model.abstract.error import OpenBBError
import requests

from ..validation.concept_map import OPENBB_FIELDS
from .models import FinancialValue
from .request_utils import retry_call
from .request_utils import OPENBB_RETRY_EXCEPTIONS



class OpenBBClient:

    def __init__(self):
        self.provider = "sec"
        self._statement_cache = {}

    def get_statement(
        self,
        symbol: str,
        statement: str,
        limit: int = 10,
    ):

        symbol = symbol.upper()

        cache_key = (
            symbol,
            statement,
            limit,
        )

        # ---------------------------------------------------------------
        # Cache
        # ---------------------------------------------------------------

        if cache_key in self._statement_cache:

            return self._statement_cache[
                cache_key
            ].copy()

        # ---------------------------------------------------------------
        # OpenBB request
        # ---------------------------------------------------------------

        if statement == "income":

            def fetch():
                result = obb.equity.fundamental.income(
                    symbol=symbol,
                    provider=self.provider,
                    period="annual",
                    limit=limit,
                    pit_mode=True,
                )

                return result.to_df()

        elif statement == "balance":

            def fetch():
                result = obb.equity.fundamental.balance(
                    symbol=symbol,
                    provider=self.provider,
                    period="annual",
                    limit=limit,
                    pit_mode=True,
                )

                return result.to_df()

        elif statement == "cash":

            def fetch():
                result = obb.equity.fundamental.cash(
                    symbol=symbol,
                    provider=self.provider,
                    period="annual",
                    limit=limit,
                    pit_mode=True,
                )

                return result.to_df()

        else:

            raise ValueError(
                f"Unknown statement type: {statement}"
            )

        dataframe = retry_call(
            fetch,
            attempts=4,
            initial_delay=1.0,
            exceptions=OPENBB_RETRY_EXCEPTIONS,
        )
        # ---------------------------------------------------------------
        # Cache successful result only
        # ---------------------------------------------------------------

        self._statement_cache[
            cache_key
        ] = dataframe.copy()

        return dataframe

    def get_field(
        self,
        dataframe,
        field: str,
    ):
        """
        Find the OpenBB column corresponding to our
        standardized financial field.
        """

        possible_columns = OPENBB_FIELDS.get(field)

        if not possible_columns:
            raise ValueError(
                f"No OpenBB field mapping exists for '{field}'."
            )

        for column in possible_columns:

            if column in dataframe.columns:
                return dataframe[column]

        raise KeyError(
            f"None of the mapped OpenBB columns "
            f"{possible_columns} exist.\n"
            f"Available columns:\n"
            f"{list(dataframe.columns)}"
        )

    def get_financial_value(
        self,
        dataframe,
        symbol: str,
        field: str,
        fiscal_year: int,
    ):

        rows = dataframe[
            dataframe["fiscal_year"] == fiscal_year
        ]

        if rows.empty:
            raise ValueError(
                f"No OpenBB data found for "
                f"{symbol} FY{fiscal_year}."
            )

        row = rows.iloc[0]

        value_series = self.get_field(
            dataframe,
            field,
        )

        value = float(
            value_series.loc[row.name]
        )

        return FinancialValue(
            symbol=symbol,
            field=field,
            value=value,
            currency=row.get("reported_currency"),
            period_end=row["period_ending"],
            fiscal_year=row.get("fiscal_year"),
            fiscal_period=row.get("fiscal_period"),
            filing_date=row.get("filing_date"),
            accepted_date=row.get("accepted_date"),
            provider=self.provider,
        )