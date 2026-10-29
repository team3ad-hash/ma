"""Offline tests: every request is parsed into real v26 protos, no API calls."""

import asyncio
from types import SimpleNamespace

import pytest
from fastmcp.exceptions import ToolError
from google.ads.googleads.v26.services.types.google_ads_service import (
    MutateGoogleAdsResponse,
    MutateOperationResponse,
)

import ads_write_mcp.mutate as mutate_module
import ads_write_mcp.tools as tools
from ads_write_mcp.mutate import build_operations, field_mask_paths


class FakeService:
    def __init__(self):
        self.requests = []

    def mutate(self, request):
        self.requests.append(request)
        response = MutateGoogleAdsResponse()
        if not request.validate_only:
            for _ in request.mutate_operations:
                item = MutateOperationResponse()
                item.campaign_result.resource_name = "customers/1/campaigns/99"
                response.mutate_operation_responses.append(item)
        return response


@pytest.fixture
def service(monkeypatch):
    fake = FakeService()
    monkeypatch.setattr(mutate_module, "get_service", lambda *a, **k: fake)
    monkeypatch.delenv(mutate_module.WRITES_ENV, raising=False)
    return fake


def _op(service, index=0):
    return service.requests[-1].mutate_operations[index]


def test_field_mask_keeps_false_and_empty_messages():
    paths = field_mask_paths(
        {
            "resource_name": "x",
            "manual_cpc": {},
            "network_settings": {"target_content_network": False},
            "maximize_conversions": {"target_cpa_micros": 0},
        }
    )
    assert paths == [
        "manual_cpc",
        "network_settings.target_content_network",
        "maximize_conversions.target_cpa_micros",
    ]


def test_build_operations_defaults_and_normalization():
    ops, notes = build_operations(
        [
            {"campaignOperation": {"create": {"name": "x"}}},
            {
                "campaign_operation": {
                    "update": {"resource_name": "customers/1/campaigns/2", "status": "PAUSED"},
                    "update_mask": "status",
                }
            },
        ]
    )
    assert ops[0].campaign_operation.create.status.name == "PAUSED"
    assert notes == ["Operation 0: new campaign set to PAUSED."]
    assert list(ops[1].campaign_operation.update_mask.paths) == ["status"]


def test_build_operations_rejects_bad_input():
    with pytest.raises(ToolError, match="allow_remove"):
        build_operations([{"campaign_operation": {"remove": "customers/1/campaigns/2"}}])
    with pytest.raises(ToolError, match="unknown operation kind"):
        build_operations([{"campaign_op": {"create": {}}}])
    with pytest.raises(ToolError, match="invalid fields"):
        build_operations([{"campaign_operation": {"create": {"nope": 1}}}])


def test_real_writes_need_env_flag(service, monkeypatch):
    with pytest.raises(ToolError, match="Writes are disabled"):
        tools.update_campaign("1", "2", status="PAUSED", validate_only=False)
    assert service.requests == []

    monkeypatch.setenv(mutate_module.WRITES_ENV, "true")
    result = tools.update_campaign("1", "2", status="PAUSED", validate_only=False)
    assert result["status"] == "APPLIED"
    assert result["results"][0]["resource_name"] == "customers/1/campaigns/99"
    assert service.requests[-1].validate_only is False


def test_update_campaign_switches_bidding(service):
    result = tools.update_campaign(
        "123-456-7890",
        "55",
        bidding_strategy="MAXIMIZE_CONVERSIONS",
        target_cpa=42.5,
        end_date="2026-12-31",
    )
    assert result["validate_only"] is True
    request = service.requests[-1]
    assert request.customer_id == "1234567890" and request.validate_only
    op = _op(service).campaign_operation
    assert op.update.resource_name == "customers/1234567890/campaigns/55"
    assert op.update.maximize_conversions.target_cpa_micros == 42_500_000
    assert op.update.end_date_time == "2026-12-31 23:59:59"
    assert set(op.update_mask.paths) == {
        "end_date_time",
        "maximize_conversions.target_cpa_micros",
    }


def test_create_demand_gen_campaign(service):
    tools.create_campaign(
        "1",
        name="DG test",
        channel_type="DEMAND_GEN",
        daily_budget=100,
        bidding_strategy="MAXIMIZE_CONVERSIONS",
        location_ids=[2376],
        language_ids=[1027],
        extra_fields={"demand_gen_campaign_settings": {"upgraded_targeting": True}},
    )
    ops = service.requests[-1].mutate_operations
    budget = ops[0].campaign_budget_operation.create
    campaign = ops[1].campaign_operation.create
    assert budget.amount_micros == 100_000_000 and budget.explicitly_shared is False
    assert campaign.advertising_channel_type.name == "DEMAND_GEN"
    assert campaign.status.name == "PAUSED"
    assert campaign.campaign_budget == budget.resource_name
    assert campaign.demand_gen_campaign_settings.upgraded_targeting is True
    assert "network_settings" not in campaign
    assert ops[2].campaign_criterion_operation.create.location.geo_target_constant == (
        "geoTargetConstants/2376"
    )
    assert ops[3].campaign_criterion_operation.create.campaign == campaign.resource_name


def test_create_search_campaign_defaults(service):
    tools.create_campaign(
        "1", name="S", channel_type="SEARCH", daily_budget=50, bidding_strategy="MANUAL_CPC"
    )
    campaign = _op(service, 1).campaign_operation.create
    assert "manual_cpc" in campaign
    assert campaign.network_settings.target_google_search is True
    assert campaign.network_settings.target_content_network is False
    with pytest.raises(ToolError, match="merchant_id"):
        tools.create_campaign(
            "1", name="S", channel_type="SHOPPING", daily_budget=5, bidding_strategy="MANUAL_CPC"
        )


def test_demand_gen_ad_group_and_channels(service):
    tools.create_demand_gen_ad_group(
        "1", "7", "AG", channels=["YOUTUBE_SHORTS", "DISCOVER"], location_ids=[2840]
    )
    ad_group = _op(service).ad_group_operation.create
    controls = ad_group.demand_gen_ad_group_settings.channel_controls
    assert controls.channel_config.name == "SELECTED_CHANNELS"
    assert controls.selected_channels.youtube_shorts is True
    assert controls.selected_channels.gmail is False
    assert ad_group.status.name == "PAUSED"
    assert _op(service, 1).ad_group_criterion_operation.create.ad_group == ad_group.resource_name

    tools.update_ad_group("1", "8", demand_gen_all_channels=False, cpc_bid=1.2)
    op = _op(service).ad_group_operation
    assert op.update.cpc_bid_micros == 1_200_000
    assert (
        op.update.demand_gen_ad_group_settings.channel_controls.channel_strategy.name
        == "ALL_OWNED_AND_OPERATED_CHANNELS"
    )
    assert "demand_gen_ad_group_settings.channel_controls.channel_strategy" in (
        op.update_mask.paths
    )


def test_demand_gen_ads(service):
    tools.create_demand_gen_ad(
        "1",
        "8",
        ad_format="MULTI_ASSET",
        final_url="https://example.com",
        business_name="Example",
        headlines=["H1", "H2"],
        descriptions=["D1"],
        logo_image_assets=["11"],
        marketing_image_assets=["customers/1/assets/12"],
        call_to_action_text="Shop now",
    )
    ad = _op(service).ad_group_ad_operation.create.ad
    info = ad.demand_gen_multi_asset_ad
    assert info.logo_images[0].asset == "customers/1/assets/11"
    assert info.marketing_images[0].asset == "customers/1/assets/12"
    assert [h.text for h in info.headlines] == ["H1", "H2"]
    assert ad.final_urls == ["https://example.com"]

    tools.create_demand_gen_ad(
        "1",
        "8",
        ad_format="VIDEO_RESPONSIVE",
        final_url="https://example.com",
        business_name="Example",
        headlines=["H1"],
        descriptions=["D1"],
        logo_image_assets=["11"],
        video_assets=["13"],
    )
    info = _op(service).ad_group_ad_operation.create.ad.demand_gen_video_responsive_ad
    assert info.business_name.text == "Example"
    assert info.long_headlines[0].text == "H1"
    assert info.videos[0].asset == "customers/1/assets/13"


def test_set_status(service):
    tools.set_status("1", "ad", ["5~6", "5~7"], "PAUSED")
    assert _op(service, 1).ad_group_ad_operation.update.resource_name == (
        "customers/1/adGroupAds/5~7"
    )
    with pytest.raises(ToolError, match="allow_remove"):
        tools.set_status("1", "campaign", ["2"], "REMOVED")
    tools.set_status("1", "asset_group", ["9"], "REMOVED", allow_remove=True)
    assert _op(service).asset_group_operation.remove == "customers/1/assetGroups/9"


def test_budget_update_refuses_shared_budget(service, monkeypatch):
    def rows(reference_count, total=0):
        budget = SimpleNamespace(
            resource_name="customers/1/campaignBudgets/3",
            amount_micros=50_000_000,
            total_amount_micros=total,
            reference_count=reference_count,
        )
        return [SimpleNamespace(campaign=SimpleNamespace(name="C"), campaign_budget=budget)]

    monkeypatch.setattr(tools, "search_rows", lambda *a: rows(3))
    with pytest.raises(ToolError, match="shared by 3"):
        tools.update_campaign_budget("1", "2", 80)

    monkeypatch.setattr(tools, "search_rows", lambda *a: rows(1))
    result = tools.update_campaign_budget("1", "2", 80)
    assert _op(service).campaign_budget_operation.update.amount_micros == 80_000_000
    assert result["notes"][-1] == "Budget amount: 50 -> 80"


def test_server_exposes_read_and_write_tools():
    from ads_write_mcp.server import mcp

    names = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert {"search_search", "write_mutate", "write_create_demand_gen_ad"} <= names
    write_tools = {n for n in names if n.startswith("write_")}
    assert len(write_tools) == 10
