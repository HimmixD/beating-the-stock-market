from openbb import obb

from ..validation.concept_map import OPENBB_FIELDS
from .models import FinancialValue


class OpenBBClient:

    def __init__(self):
        self.provider = "sec"

    def get_statement(
        self,
        symbol: str,
        statement: str,
        limit: int = 10,
    ):

        if statement == "income":

            result = obb.equity.fundamental.income(
                symbol=symbol,
                provider=self.provider,
                period="annual",
                limit=limit,
                pit_mode=True,
            )

        elif statement == "balance":

            result = obb.equity.fundamental.balance(
                symbol=symbol,
                provider=self.provider,
                period="annual",
                limit=limit,
                pit_mode=True,
            )

        elif statement == "cash":

            result = obb.equity.fundamental.cash(
                symbol=symbol,
                provider=self.provider,
                period="annual",
                limit=limit,
                pit_mode=True,
            )

        else:
            raise ValueError(
                f"Unknown statement type: {statement}"
            )

        return result.to_df()

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