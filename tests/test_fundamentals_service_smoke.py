from quant.data.provider_bootstrap import build_fundamentals_service


def test_service_resolves_provider_without_location_in_api():
    service = build_fundamentals_service()

    # US -> SEC provider (because mapping exists)
    resolved_us = service.resolver.resolve("AAPL")
    assert resolved_us.provider.name == "sec"

    # non-mapped -> global fallback
    resolved_other = service.resolver.resolve("NESN.SW")
    assert resolved_other.provider.name == "global_openbb"