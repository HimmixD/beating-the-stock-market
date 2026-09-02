from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import FundamentalProvider
from .sec_provider import SECFundamentalProvider
from .global_provider import GlobalOpenBBProvider


@dataclass
class ResolvedProvider:
    provider: FundamentalProvider
    reason: str


class ProviderResolver:
    def __init__(
        self,
        sec_provider: SECFundamentalProvider,
        global_provider: Optional[GlobalOpenBBProvider] = None,
    ):
        self.sec_provider = sec_provider
        self.global_provider = global_provider or GlobalOpenBBProvider()

    def resolve(self, symbol: str) -> ResolvedProvider:
        s = symbol.upper()

        if self.sec_provider.supports_symbol(s):
            return ResolvedProvider(
                provider=self.sec_provider,
                reason="CIK mapping available -> SEC provider selected",
            )

        return ResolvedProvider(
            provider=self.global_provider,
            reason="No SEC mapping -> global provider fallback selected",
        )