"""Write tools for Google Ads campaigns of every type, including Demand Gen.

All tools default to validate_only=true (dry run). See `mutate.py` for the
safety rules shared by every tool.
"""

import base64
import urllib.request
from typing import Any, Dict, List, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools import Tool
from mcp.types import ToolAnnotations

import ads_mcp.utils as utils
from ads_write_mcp.mutate import run_mutate, search_rows

campaigns_write_mcp = FastMCP("write")

_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)

Status = Literal["ENABLED", "PAUSED"]

BiddingStrategy = Literal[
    "MANUAL_CPC",
    "MAXIMIZE_CLICKS",
    "MAXIMIZE_CONVERSIONS",
    "MAXIMIZE_CONVERSION_VALUE",
    "TARGET_CPA",
    "TARGET_ROAS",
    "TARGET_CPC",
    "MANUAL_CPM",
    "TARGET_CPM",
    "MANUAL_CPV",
    "TARGET_CPV",
]

ChannelType = Literal[
    "SEARCH",
    "DISPLAY",
    "SHOPPING",
    "VIDEO",
    "PERFORMANCE_MAX",
    "DEMAND_GEN",
    "MULTI_CHANNEL",
    "HOTEL",
    "TRAVEL",
    "LOCAL",
    "SMART",
]

DemandGenChannel = Literal[
    "YOUTUBE_IN_STREAM",
    "YOUTUBE_IN_FEED",
    "YOUTUBE_SHORTS",
    "DISCOVER",
    "GMAIL",
    "DISPLAY",
    "MAPS",
]

_SAFETY_DOC = """
    Safety: validate_only defaults to true, so the first call only validates
    the change with Google and changes nothing. Describe the change to the
    user, and only after they confirm call again with validate_only=false.
"""


def _write_tool(fn):
    """Registers `fn` as a write tool, appending the shared safety notes."""
    fn.__doc__ = (fn.__doc__ or "") + _SAFETY_DOC
    campaigns_write_mcp.add_tool(Tool.from_function(fn, annotations=_WRITE))
    return fn


def _micros(amount: float) -> int:
    """Converts an amount in account currency to micros, rounded to cents."""
    return int(round(amount * 100)) * 10_000


def _date_time(value: str | None, end_of_day: bool = False) -> str | None:
    """Accepts YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS' and returns the latter."""
    if value is None:
        return None
    if len(value) == 10:
        return f"{value} {'23:59:59' if end_of_day else '00:00:00'}"
    return value


def _customer(customer_id: str | int) -> str:
    return f"customers/{utils.clean_customer_id(customer_id)}"


def _bidding_fields(
    strategy: str | None,
    target_cpa: float | None = None,
    target_roas: float | None = None,
    max_cpc: float | None = None,
    target_cpc: float | None = None,
) -> Dict[str, Any]:
    """Maps a friendly bidding choice to the Campaign oneof field it sets."""
    if strategy is None:
        if any(v is not None for v in (target_cpa, target_roas, max_cpc, target_cpc)):
            raise ToolError("Pass bidding_strategy together with its targets.")
        return {}

    ceiling = {"cpc_bid_ceiling_micros": _micros(max_cpc)} if max_cpc else {}
    if strategy == "MANUAL_CPC":
        return {"manual_cpc": {}}
    if strategy == "MAXIMIZE_CLICKS":
        return {"target_spend": ceiling}
    if strategy == "MAXIMIZE_CONVERSIONS":
        fields = dict(ceiling)
        if target_cpa is not None:
            fields["target_cpa_micros"] = _micros(target_cpa)
        return {"maximize_conversions": fields}
    if strategy == "MAXIMIZE_CONVERSION_VALUE":
        fields = dict(ceiling)
        if target_roas is not None:
            fields["target_roas"] = target_roas
        return {"maximize_conversion_value": fields}
    if strategy == "TARGET_CPA":
        if target_cpa is None:
            raise ToolError("TARGET_CPA needs target_cpa.")
        return {"target_cpa": {"target_cpa_micros": _micros(target_cpa), **ceiling}}
    if strategy == "TARGET_ROAS":
        if target_roas is None:
            raise ToolError("TARGET_ROAS needs target_roas.")
        return {"target_roas": {"target_roas": target_roas, **ceiling}}
    if strategy == "TARGET_CPC":
        if target_cpc is None:
            raise ToolError("TARGET_CPC needs target_cpc.")
        return {"target_cpc": {"target_cpc_micros": _micros(target_cpc)}}
    # MANUAL_CPM, TARGET_CPM, MANUAL_CPV, TARGET_CPV take no required fields.
    return {strategy.lower(): {}}


def _demand_gen_channel_controls(
    channels: List[str] | None,
    owned_and_operated_only: bool = False,
) -> Dict[str, Any]:
    if channels:
        return {
            "channel_config": "SELECTED_CHANNELS",
            "selected_channels": {
                c.lower(): (c in channels) for c in DemandGenChannel.__args__
            },
        }
    return {
        "channel_config": "CHANNEL_STRATEGY",
        "channel_strategy": (
            "ALL_OWNED_AND_OPERATED_CHANNELS"
            if owned_and_operated_only
            else "ALL_CHANNELS"
        ),
    }


@_write_tool
def mutate(
    customer_id: str | int,
    operations: List[Dict[str, Any]],
    validate_only: bool = True,
    partial_failure: bool = False,
    allow_remove: bool = False,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Runs any Google Ads write (GoogleAdsService.Mutate) for any campaign type.

    Use this for anything the dedicated tools don't cover: Performance Max
    asset groups and listing groups, Demand Gen carousel/product ads, Shopping
    and Hotel settings, keywords, audiences, sitelinks and other assets,
    campaign criteria (locations, languages, schedules), labels, experiments.

    Each item in `operations` is one MutateOperation in JSON form with proto
    field names, holding exactly one operation kind with one of
    create/update/remove. Examples:

        {"campaign_operation": {"update": {
            "resource_name": "customers/123/campaigns/456",
            "status": "PAUSED"}}}

        {"ad_group_criterion_operation": {"create": {
            "ad_group": "customers/123/adGroups/789",
            "keyword": {"text": "running shoes", "match_type": "PHRASE"},
            "cpc_bid_micros": 1500000}}}

        {"campaign_criterion_operation": {"create": {
            "campaign": "customers/123/campaigns/456",
            "location": {"geo_target_constant": "geoTargetConstants/2376"}}}}

    Updates: `update_mask` is optional; when omitted it is built from exactly
    the fields given (including false/0 values and empty messages).
    Creates in one request can reference each other with negative temporary
    IDs, e.g. create a budget "customers/123/campaignBudgets/-1" and a campaign
    whose campaign_budget is that same name. Money is always in micros
    (1 unit of currency = 1,000,000). Bytes (image data) are base64 strings.
    New campaigns, ad groups, ads and asset groups are created PAUSED unless
    a status is set. Remove operations need allow_remove=true.

    Look up resource names and field names with the read-only `search` and
    `get_resource_metadata` tools before writing; do not guess IDs.

    Args:
        customer_id: The customer to change (digits only).
        operations: The MutateOperation objects, applied in order.
        validate_only: true = dry run (default); false = apply.
        partial_failure: Apply valid operations even if others fail.
        allow_remove: Allow remove operations (irreversible).
        login_customer_id: Optional manager account ID.
    """
    return run_mutate(
        customer_id,
        operations,
        validate_only=validate_only,
        partial_failure=partial_failure,
        allow_remove=allow_remove,
        login_customer_id=login_customer_id,
    )



@_write_tool
def update_campaign(
    customer_id: str | int,
    campaign_id: str | int,
    name: str | None = None,
    status: Status | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    bidding_strategy: BiddingStrategy | None = None,
    target_cpa: float | None = None,
    target_roas: float | None = None,
    max_cpc: float | None = None,
    target_cpc: float | None = None,
    portfolio_bidding_strategy_id: str | int | None = None,
    network_settings: Dict[str, bool] | None = None,
    final_url_suffix: str | None = None,
    tracking_url_template: str | None = None,
    extra_fields: Dict[str, Any] | None = None,
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Edits a campaign of any type (Search, Display, Shopping, Video,
    Performance Max, Demand Gen, App, Hotel, ...).

    Only the arguments you pass are changed. Money arguments are in the
    account currency (e.g. 25.5), not micros.

    Args:
        customer_id: The customer ID (digits only).
        campaign_id: The campaign to edit.
        name: New campaign name.
        status: ENABLED or PAUSED (to remove, use set_status).
        start_date: YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS'.
        end_date: YYYY-MM-DD (end of that day) or 'YYYY-MM-DD HH:MM:SS'.
        bidding_strategy: Switch to this standard bidding strategy. For
            Performance Max and Demand Gen use MAXIMIZE_CONVERSIONS (with an
            optional target_cpa) or MAXIMIZE_CONVERSION_VALUE (with an
            optional target_roas). MAXIMIZE_CLICKS accepts max_cpc.
        target_cpa: Target cost per conversion, in currency.
        target_roas: Target ROAS as a ratio (3.5 = 350%).
        max_cpc: Max CPC bid ceiling, in currency.
        target_cpc: For TARGET_CPC (Demand Gen / Video).
        portfolio_bidding_strategy_id: Attach a portfolio bidding strategy
            instead of a standard one.
        network_settings: e.g. {"target_search_network": false,
            "target_content_network": false} (Search/Display).
        final_url_suffix: Tracking suffix appended to final URLs.
        tracking_url_template: Tracking template.
        extra_fields: Any other Campaign fields in proto JSON form, e.g.
            {"demand_gen_campaign_settings": {"upgraded_targeting": true}} or
            {"shopping_setting": {"feed_label": "US"}}.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    if bidding_strategy and portfolio_bidding_strategy_id:
        raise ToolError("Pass bidding_strategy or portfolio_bidding_strategy_id, not both.")

    customer = _customer(customer_id)
    update: Dict[str, Any] = {
        "resource_name": f"{customer}/campaigns/{utils.clean_customer_id(campaign_id)}"
    }
    simple = {
        "name": name,
        "status": status,
        "start_date_time": _date_time(start_date),
        "end_date_time": _date_time(end_date, end_of_day=True),
        "final_url_suffix": final_url_suffix,
        "tracking_url_template": tracking_url_template,
        "network_settings": network_settings,
    }
    update.update({k: v for k, v in simple.items() if v is not None})
    update.update(
        _bidding_fields(bidding_strategy, target_cpa, target_roas, max_cpc, target_cpc)
    )
    if portfolio_bidding_strategy_id is not None:
        update["bidding_strategy"] = (
            f"{customer}/biddingStrategies/"
            f"{utils.clean_customer_id(portfolio_bidding_strategy_id)}"
        )
    if extra_fields:
        update.update(extra_fields)
    if len(update) == 1:
        raise ToolError("Nothing to change: pass at least one field.")

    return run_mutate(
        customer_id,
        [{"campaign_operation": {"update": update}}],
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )



@_write_tool
def update_campaign_budget(
    customer_id: str | int,
    campaign_id: str | int,
    amount: float,
    allow_shared_budget: bool = False,
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Changes the budget amount of a campaign (any campaign type).

    The amount is in the account currency (e.g. 150 = 150 per day for a daily
    budget, or the total for a campaign-total budget). If the budget is shared
    with other campaigns the change affects all of them, so it is refused
    unless allow_shared_budget=true.

    Args:
        customer_id: The customer ID (digits only).
        campaign_id: The campaign whose budget to change.
        amount: New budget amount, in currency.
        allow_shared_budget: Allow changing a budget shared by several campaigns.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    rows = search_rows(
        customer_id,
        "SELECT campaign.name, campaign_budget.resource_name, "
        "campaign_budget.amount_micros, campaign_budget.total_amount_micros, "
        "campaign_budget.reference_count, campaign_budget.explicitly_shared "
        "FROM campaign WHERE campaign.id = "
        f"{utils.clean_customer_id(campaign_id)}",
        login_customer_id,
    )
    if not rows:
        raise ToolError(f"Campaign {campaign_id} not found.")
    budget = rows[0].campaign_budget
    if budget.reference_count > 1 and not allow_shared_budget:
        raise ToolError(
            f"The budget of '{rows[0].campaign.name}' is shared by "
            f"{budget.reference_count} campaigns; changing it changes all of "
            "them. Confirm with the user and pass allow_shared_budget=true."
        )

    field = "total_amount_micros" if budget.total_amount_micros else "amount_micros"
    result = run_mutate(
        customer_id,
        [
            {
                "campaign_budget_operation": {
                    "update": {
                        "resource_name": budget.resource_name,
                        field: _micros(amount),
                    }
                }
            }
        ],
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )
    previous = getattr(budget, field) / 1_000_000
    result["notes"].append(f"Budget {field[:-7]}: {previous:g} -> {amount:g}")
    return result



_STATUS_RESOURCES = {
    "campaign": ("campaign_operation", "campaigns"),
    "ad_group": ("ad_group_operation", "adGroups"),
    "ad": ("ad_group_ad_operation", "adGroupAds"),
    "asset_group": ("asset_group_operation", "assetGroups"),
    "keyword": ("ad_group_criterion_operation", "adGroupCriteria"),
}


@_write_tool
def set_status(
    customer_id: str | int,
    entity_type: Literal["campaign", "ad_group", "ad", "asset_group", "keyword"],
    ids: List[str | int],
    status: Literal["ENABLED", "PAUSED", "REMOVED"],
    validate_only: bool = True,
    allow_remove: bool = False,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Enables, pauses or removes campaigns, ad groups, ads, asset groups or keywords.

    Works for every campaign type, including Performance Max asset groups and
    Demand Gen ad groups and ads. All changes are applied atomically.

    Args:
        customer_id: The customer ID (digits only).
        entity_type: What the ids refer to.
        ids: IDs to change. Ads use "adGroupId~adId" and keywords use
            "adGroupId~criterionId".
        status: ENABLED, PAUSED, or REMOVED (irreversible, needs allow_remove).
        validate_only: true = dry run (default); false = apply.
        allow_remove: Required to remove.
        login_customer_id: Optional manager account ID.
    """
    kind, collection = _STATUS_RESOURCES[entity_type]
    customer = _customer(customer_id)
    operations = []
    for entity_id in ids:
        resource_name = f"{customer}/{collection}/{str(entity_id).strip()}"
        if status == "REMOVED":
            operations.append({kind: {"remove": resource_name}})
        else:
            operations.append(
                {kind: {"update": {"resource_name": resource_name, "status": status}}}
            )
    return run_mutate(
        customer_id,
        operations,
        validate_only=validate_only,
        allow_remove=allow_remove,
        login_customer_id=login_customer_id,
    )



@_write_tool
def create_campaign(
    customer_id: str | int,
    name: str,
    channel_type: ChannelType,
    daily_budget: float,
    bidding_strategy: BiddingStrategy,
    target_cpa: float | None = None,
    target_roas: float | None = None,
    max_cpc: float | None = None,
    target_cpc: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    location_ids: List[int] | None = None,
    language_ids: List[int] | None = None,
    network_settings: Dict[str, bool] | None = None,
    merchant_id: int | None = None,
    contains_eu_political_advertising: bool = False,
    status: Status = "PAUSED",
    extra_fields: Dict[str, Any] | None = None,
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Creates a campaign with its own daily budget, PAUSED by default.

    Supports every channel type the API can create: SEARCH, DISPLAY,
    SHOPPING, PERFORMANCE_MAX, DEMAND_GEN, VIDEO (where allowed), MULTI_CHANNEL
    (App), HOTEL, TRAVEL, ... The campaign still needs ad groups and ads
    (or asset groups for Performance Max) before it can serve. For Demand Gen,
    follow up with create_demand_gen_ad_group and create_demand_gen_ad.

    Args:
        customer_id: The customer ID (digits only).
        name: Campaign name (must be unique in the account).
        channel_type: Campaign type.
        daily_budget: Daily budget in currency.
        bidding_strategy: Standard bidding strategy (see update_campaign).
        target_cpa: Target CPA in currency.
        target_roas: Target ROAS as a ratio (3.5 = 350%).
        max_cpc: Max CPC ceiling in currency.
        target_cpc: Target CPC in currency (TARGET_CPC).
        start_date: YYYY-MM-DD.
        end_date: YYYY-MM-DD.
        location_ids: Geo target constant IDs to target (e.g. 2376 = Israel,
            2840 = United States). Find others with search on
            geo_target_constant.
        language_ids: Language constant IDs (e.g. 1027 = Hebrew, 1000 = English).
        network_settings: Search/Display networks; for SEARCH defaults to
            Google Search + search partners, no Display.
        merchant_id: Merchant Center ID (required for SHOPPING; optional for
            PERFORMANCE_MAX retail).
        contains_eu_political_advertising: Required declaration; false unless
            the campaign has EU political ads.
        status: PAUSED (default) or ENABLED.
        extra_fields: Any other Campaign fields in proto JSON form, e.g.
            {"advertising_channel_sub_type": "APP_CAMPAIGN",
             "app_campaign_setting": {...}}.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    customer = _customer(customer_id)
    budget_name = f"{customer}/campaignBudgets/-1"
    campaign_name = f"{customer}/campaigns/-2"

    budget = {
        "resource_name": budget_name,
        "name": f"{name} budget",
        "amount_micros": _micros(daily_budget),
        "delivery_method": "STANDARD",
        "explicitly_shared": False,
    }
    campaign: Dict[str, Any] = {
        "resource_name": campaign_name,
        "name": name,
        "status": status,
        "advertising_channel_type": channel_type,
        "campaign_budget": budget_name,
        "contains_eu_political_advertising": (
            "CONTAINS_EU_POLITICAL_ADVERTISING"
            if contains_eu_political_advertising
            else "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"
        ),
    }
    campaign.update(
        _bidding_fields(bidding_strategy, target_cpa, target_roas, max_cpc, target_cpc)
    )
    if start_date:
        campaign["start_date_time"] = _date_time(start_date)
    if end_date:
        campaign["end_date_time"] = _date_time(end_date, end_of_day=True)
    if network_settings is not None:
        campaign["network_settings"] = network_settings
    elif channel_type == "SEARCH":
        campaign["network_settings"] = {
            "target_google_search": True,
            "target_search_network": True,
            "target_content_network": False,
            "target_partner_search_network": False,
        }
    if merchant_id is not None:
        campaign["shopping_setting"] = {"merchant_id": merchant_id}
    elif channel_type == "SHOPPING":
        raise ToolError("SHOPPING campaigns need merchant_id.")
    if extra_fields:
        campaign.update(extra_fields)

    operations: List[Dict[str, Any]] = [
        {"campaign_budget_operation": {"create": budget}},
        {"campaign_operation": {"create": campaign}},
    ]
    for location_id in location_ids or []:
        operations.append(
            {
                "campaign_criterion_operation": {
                    "create": {
                        "campaign": campaign_name,
                        "location": {
                            "geo_target_constant": f"geoTargetConstants/{location_id}"
                        },
                    }
                }
            }
        )
    for language_id in language_ids or []:
        operations.append(
            {
                "campaign_criterion_operation": {
                    "create": {
                        "campaign": campaign_name,
                        "language": {
                            "language_constant": f"languageConstants/{language_id}"
                        },
                    }
                }
            }
        )
    return run_mutate(
        customer_id,
        operations,
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )



@_write_tool
def update_ad_group(
    customer_id: str | int,
    ad_group_id: str | int,
    name: str | None = None,
    status: Status | None = None,
    cpc_bid: float | None = None,
    cpm_bid: float | None = None,
    cpv_bid: float | None = None,
    target_cpa: float | None = None,
    target_roas: float | None = None,
    demand_gen_channels: List[DemandGenChannel] | None = None,
    demand_gen_all_channels: bool | None = None,
    extra_fields: Dict[str, Any] | None = None,
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Edits an ad group of any campaign type, including Demand Gen channel controls.

    Args:
        customer_id: The customer ID (digits only).
        ad_group_id: The ad group to edit.
        name: New name.
        status: ENABLED or PAUSED.
        cpc_bid: Max CPC bid in currency (manual CPC / ad group override).
        cpm_bid: Max CPM bid in currency.
        cpv_bid: Max CPV bid in currency (Video).
        target_cpa: Ad group target CPA override in currency.
        target_roas: Ad group target ROAS override (3.5 = 350%).
        demand_gen_channels: Demand Gen only: serve only on these channels.
        demand_gen_all_channels: Demand Gen only: true = all Google channels,
            false = Google-owned channels only (YouTube, Discover, Gmail, Maps).
        extra_fields: Any other AdGroup fields in proto JSON form.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    if demand_gen_channels and demand_gen_all_channels is not None:
        raise ToolError("Pass demand_gen_channels or demand_gen_all_channels, not both.")

    update: Dict[str, Any] = {
        "resource_name": f"{_customer(customer_id)}/adGroups/"
        f"{utils.clean_customer_id(ad_group_id)}"
    }
    money = {
        "cpc_bid_micros": cpc_bid,
        "cpm_bid_micros": cpm_bid,
        "cpv_bid_micros": cpv_bid,
        "target_cpa_micros": target_cpa,
    }
    update.update({k: _micros(v) for k, v in money.items() if v is not None})
    if name is not None:
        update["name"] = name
    if status is not None:
        update["status"] = status
    if target_roas is not None:
        update["target_roas"] = target_roas
    if demand_gen_channels or demand_gen_all_channels is not None:
        update["demand_gen_ad_group_settings"] = {
            "channel_controls": _demand_gen_channel_controls(
                demand_gen_channels,
                owned_and_operated_only=demand_gen_all_channels is False,
            )
        }
    if extra_fields:
        update.update(extra_fields)
    if len(update) == 1:
        raise ToolError("Nothing to change: pass at least one field.")

    return run_mutate(
        customer_id,
        [{"ad_group_operation": {"update": update}}],
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )



@_write_tool
def create_demand_gen_ad_group(
    customer_id: str | int,
    campaign_id: str | int,
    name: str,
    channels: List[DemandGenChannel] | None = None,
    owned_and_operated_only: bool = False,
    location_ids: List[int] | None = None,
    language_ids: List[int] | None = None,
    status: Status = "PAUSED",
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Creates an ad group in a Demand Gen campaign, PAUSED by default.

    Args:
        customer_id: The customer ID (digits only).
        campaign_id: The Demand Gen campaign.
        name: Ad group name.
        channels: Serve only on these channels; omit for all channels.
        owned_and_operated_only: With no channels: Google-owned channels only
            (no Display network).
        location_ids: Ad-group-level location targets (geo target constant IDs).
        language_ids: Ad-group-level language targets (language constant IDs).
        status: PAUSED (default) or ENABLED.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    customer = _customer(customer_id)
    ad_group_name = f"{customer}/adGroups/-1"
    operations: List[Dict[str, Any]] = [
        {
            "ad_group_operation": {
                "create": {
                    "resource_name": ad_group_name,
                    "name": name,
                    "status": status,
                    "campaign": f"{customer}/campaigns/"
                    f"{utils.clean_customer_id(campaign_id)}",
                    "demand_gen_ad_group_settings": {
                        "channel_controls": _demand_gen_channel_controls(
                            channels, owned_and_operated_only
                        )
                    },
                }
            }
        }
    ]
    for location_id in location_ids or []:
        operations.append(
            {
                "ad_group_criterion_operation": {
                    "create": {
                        "ad_group": ad_group_name,
                        "location": {
                            "geo_target_constant": f"geoTargetConstants/{location_id}"
                        },
                    }
                }
            }
        )
    for language_id in language_ids or []:
        operations.append(
            {
                "ad_group_criterion_operation": {
                    "create": {
                        "ad_group": ad_group_name,
                        "language": {
                            "language_constant": f"languageConstants/{language_id}"
                        },
                    }
                }
            }
        )
    return run_mutate(
        customer_id,
        operations,
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )



def _download(url: str, max_bytes: int = 5_120_000) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ads-write-mcp"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ToolError("Image is larger than the 5120 KB Google Ads limit.")
    return data


@_write_tool
def create_image_asset(
    customer_id: str | int,
    image_url: str,
    name: str,
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Uploads an image (from a public URL) as an image asset.

    Use the returned asset resource name in create_demand_gen_ad, Performance
    Max asset groups, responsive display ads, etc. Google checks aspect
    ratios where the asset is used: landscape 1.91:1 (e.g. 1200x628),
    square 1:1 (1200x1200), portrait 4:5 (960x1200), logo 1:1.

    Args:
        customer_id: The customer ID (digits only).
        image_url: Public http(s) URL of a JPG/PNG/GIF image.
        name: Asset name (must be unique among image assets).
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    if not image_url.startswith(("https://", "http://")):
        raise ToolError("image_url must be an http(s) URL.")
    data = _download(image_url)
    return run_mutate(
        customer_id,
        [
            {
                "asset_operation": {
                    "create": {
                        "name": name,
                        "type": "IMAGE",
                        "image_asset": {"data": base64.b64encode(data).decode()},
                    }
                }
            }
        ],
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )



@_write_tool
def create_youtube_video_asset(
    customer_id: str | int,
    youtube_video_id: str,
    name: str,
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Creates a YouTube video asset for Demand Gen, Performance Max or Video ads.

    Args:
        customer_id: The customer ID (digits only).
        youtube_video_id: The 11-character YouTube video ID (from the URL).
        name: Asset name.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    return run_mutate(
        customer_id,
        [
            {
                "asset_operation": {
                    "create": {
                        "name": name,
                        "type": "YOUTUBE_VIDEO",
                        "youtube_video_asset": {"youtube_video_id": youtube_video_id},
                    }
                }
            }
        ],
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )



def _asset_list(customer: str, ids: List[str | int] | None) -> List[Dict[str, str]]:
    """Accepts asset IDs or full resource names."""
    result = []
    for value in ids or []:
        value = str(value)
        if not value.startswith("customers/"):
            value = f"{customer}/assets/{utils.clean_customer_id(value)}"
        result.append({"asset": value})
    return result


def _texts(values: List[str] | None) -> List[Dict[str, str]]:
    return [{"text": v} for v in values or []]


@_write_tool
def create_demand_gen_ad(
    customer_id: str | int,
    ad_group_id: str | int,
    ad_format: Literal["MULTI_ASSET", "VIDEO_RESPONSIVE"],
    final_url: str,
    business_name: str,
    headlines: List[str],
    descriptions: List[str],
    logo_image_assets: List[str],
    marketing_image_assets: List[str] | None = None,
    square_marketing_image_assets: List[str] | None = None,
    portrait_marketing_image_assets: List[str] | None = None,
    video_assets: List[str] | None = None,
    long_headlines: List[str] | None = None,
    call_to_action_text: str | None = None,
    ad_name: str | None = None,
    status: Status = "PAUSED",
    validate_only: bool = True,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Creates a Demand Gen image (multi-asset) or video ad, PAUSED by default.

    Upload images with create_image_asset and videos with
    create_youtube_video_asset first, then pass their asset IDs or resource
    names. Carousel and product ads can be created with `mutate`
    (demand_gen_carousel_ad / demand_gen_product_ad).

    Args:
        customer_id: The customer ID (digits only).
        ad_group_id: A Demand Gen ad group.
        ad_format: MULTI_ASSET (image ad) or VIDEO_RESPONSIVE (video ad).
        final_url: Landing page URL.
        business_name: Advertiser/brand name (up to 25 characters).
        headlines: 1-5 headlines (up to 40 characters).
        descriptions: 1-5 descriptions (up to 90 characters).
        logo_image_assets: 1:1 logo image assets.
        marketing_image_assets: MULTI_ASSET: landscape 1.91:1 images.
        square_marketing_image_assets: MULTI_ASSET: square 1:1 images.
        portrait_marketing_image_assets: MULTI_ASSET: portrait 4:5 images.
        video_assets: VIDEO_RESPONSIVE: YouTube video assets.
        long_headlines: VIDEO_RESPONSIVE: 1-5 long headlines (up to 90 chars).
        call_to_action_text: MULTI_ASSET: e.g. "Shop now"; omit for automated.
        ad_name: Optional internal ad name.
        status: PAUSED (default) or ENABLED.
        validate_only: true = dry run (default); false = apply.
        login_customer_id: Optional manager account ID.
    """
    customer = _customer(customer_id)
    if ad_format == "MULTI_ASSET":
        if not (marketing_image_assets or square_marketing_image_assets):
            raise ToolError(
                "MULTI_ASSET ads need marketing_image_assets or "
                "square_marketing_image_assets."
            )
        info: Dict[str, Any] = {
            "marketing_images": _asset_list(customer, marketing_image_assets),
            "square_marketing_images": _asset_list(
                customer, square_marketing_image_assets
            ),
            "portrait_marketing_images": _asset_list(
                customer, portrait_marketing_image_assets
            ),
            "logo_images": _asset_list(customer, logo_image_assets),
            "headlines": _texts(headlines),
            "descriptions": _texts(descriptions),
            "business_name": business_name,
        }
        if call_to_action_text:
            info["call_to_action_text"] = call_to_action_text
        ad_field = "demand_gen_multi_asset_ad"
    else:
        if not video_assets:
            raise ToolError("VIDEO_RESPONSIVE ads need video_assets.")
        info = {
            "videos": _asset_list(customer, video_assets),
            "logo_images": _asset_list(customer, logo_image_assets),
            "headlines": _texts(headlines),
            "long_headlines": _texts(long_headlines or headlines[:1]),
            "descriptions": _texts(descriptions),
            "business_name": {"text": business_name},
        }
        ad_field = "demand_gen_video_responsive_ad"

    ad: Dict[str, Any] = {"final_urls": [final_url], ad_field: info}
    if ad_name:
        ad["name"] = ad_name
    return run_mutate(
        customer_id,
        [
            {
                "ad_group_ad_operation": {
                    "create": {
                        "ad_group": f"{customer}/adGroups/"
                        f"{utils.clean_customer_id(ad_group_id)}",
                        "status": status,
                        "ad": ad,
                    }
                }
            }
        ],
        validate_only=validate_only,
        login_customer_id=login_customer_id,
    )

