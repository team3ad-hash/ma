# Copyright 2026 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Write tools for campaign bidding, location targeting type and ad schedule.

These tools register on the same ``management`` sub-server as
``campaign_management`` and follow the same propose-and-confirm workflow
(``validate_only=True`` first, then ``validate_only=False`` with the returned
``checksum`` after the user approves).

Tools:
  * update_campaign_bidding           - Maximize conversions (+ optional target CPA)
                                        or maximize conversion value (+ optional target ROAS)
  * update_campaign_location_targeting - PRESENCE vs. PRESENCE_OR_INTEREST
  * set_campaign_ad_schedule          - replace a campaign's ad schedule
"""

from enum import Enum
from typing import Any

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from ads_mcp import propose_and_confirm as pac
import ads_mcp.utils as utils
from ads_mcp.tools.campaign_management import (
    _clean_cid,
    _clean_id,
    _enum_value,
    _lookup,
    _summarize_results,
    management_mcp,
)


class BiddingStrategy(str, Enum):
    """Supported standard (non-portfolio) bidding strategies."""

    MAXIMIZE_CONVERSIONS = "MAXIMIZE_CONVERSIONS"
    MAXIMIZE_CONVERSION_VALUE = "MAXIMIZE_CONVERSION_VALUE"


class LocationTargetingType(str, Enum):
    """Who is reached by a campaign's location targets."""

    PRESENCE = "PRESENCE"  # People in or regularly in the targeted locations.
    PRESENCE_OR_INTEREST = "PRESENCE_OR_INTEREST"  # ... or interested in them.


class DayOfWeek(str, Enum):
    """Days of the week for ad schedules."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


_MINUTE_ENUM = {0: "ZERO", 15: "FIFTEEN", 30: "THIRTY", 45: "FORTY_FIVE"}
_MINUTE_FROM_ENUM = {v: k for k, v in _MINUTE_ENUM.items()}
_MAX_SCHEDULE_WINDOWS = 42  # Google Ads allows up to 6 windows per day.


class AdScheduleWindow(BaseModel):
    """One ad schedule window, in the account's time zone."""

    day_of_week: DayOfWeek = Field(description="Day, e.g. 'SUNDAY'.")
    start_hour: int = Field(ge=0, le=23, description="Start hour, 0-23.")
    start_minute: int = Field(default=0, description="0, 15, 30 or 45.")
    end_hour: int = Field(ge=0, le=24, description="End hour, 0-24 (24 = midnight).")
    end_minute: int = Field(default=0, description="0, 15, 30 or 45 (must be 0 when end_hour is 24).")
    bid_modifier: float | None = Field(
        default=None,
        description="Optional bid adjustment, e.g. 1.2 for +20% or 0.8 for -20% (0.1-10). Omit for none.",
    )


def _micros(amount: float, name: str) -> int:
    try:
        value = float(amount)
    except (TypeError, ValueError) as exc:
        raise ToolError(f"Error: '{name}' must be a number.") from exc
    if value < 0:
        raise ToolError(f"Error: '{name}' cannot be negative.")
    # Round to 0.01 currency units (multiple of 10,000 micros).
    return int(round(value * 100)) * 10_000


# --------------------------------------------------------------------------
# Bidding
# --------------------------------------------------------------------------


@management_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True)
)
def update_campaign_bidding(
    customer_id: str | int,
    campaign_id: str | int,
    strategy: BiddingStrategy,
    target_cpa: float | None = None,
    target_roas: float | None = None,
    login_customer_id: str | int | None = None,
    validate_only: bool = True,
    checksum: str | None = None,
) -> str:
    """Sets a campaign's standard bidding strategy and its optional target.

    - MAXIMIZE_CONVERSIONS with `target_cpa` (account currency, e.g. 120 for ₪120).
      Pass target_cpa=0 to remove the target; omit it to remove it as well.
    - MAXIMIZE_CONVERSION_VALUE with `target_roas` as a ratio (3.5 = 350%).
      Pass target_roas=0 or omit it to remove the target.

    Works for campaigns using a standard (not portfolio) strategy, including
    Search and Performance Max. Changing strategy or target restarts learning.

    Propose & Confirm Workflow (`validate_only` and `checksum`):
    1. Call with `validate_only=True` (the default) to validate and get `change_items` (with current values) and a `checksum`.
    2. Present the `change_items` to the user and wait for explicit approval.
    3. Only after approval, call again with the exact same parameters, `validate_only=False` and the `checksum`.

    Args:
        customer_id: Google Ads customer ID.
        campaign_id: ID of the campaign.
        strategy: 'MAXIMIZE_CONVERSIONS' or 'MAXIMIZE_CONVERSION_VALUE'.
        target_cpa: Target cost per conversion in account currency (only with MAXIMIZE_CONVERSIONS).
        target_roas: Target return on ad spend as a ratio, 0.01-1000 (only with MAXIMIZE_CONVERSION_VALUE).
        login_customer_id: Optional manager customer ID for the login-customer-id header.
        validate_only: If True (default), validate only and return a proposal. If False, commit; requires `checksum`.
        checksum: Checksum returned by the prior `validate_only=True` call.
    """
    cid = _clean_cid(customer_id)
    camp_id = _clean_id(campaign_id, "campaign_id")
    strategy_name = _enum_value(strategy, BiddingStrategy, "strategy")

    if strategy_name == "MAXIMIZE_CONVERSIONS" and target_roas is not None:
        raise ToolError("Error: 'target_roas' is only valid with MAXIMIZE_CONVERSION_VALUE.")
    if strategy_name == "MAXIMIZE_CONVERSION_VALUE" and target_cpa is not None:
        raise ToolError("Error: 'target_cpa' is only valid with MAXIMIZE_CONVERSIONS.")

    ga_client = utils.get_googleads_client(login_customer_id=login_customer_id)
    service = utils.get_googleads_service_from_client(ga_client, "CampaignService")

    resource_name = f"customers/{cid}/campaigns/{camp_id}"
    op = ga_client.get_type("CampaignOperation")
    campaign = op.update
    campaign.resource_name = resource_name

    target_label: str
    if strategy_name == "MAXIMIZE_CONVERSIONS":
        cpa_micros = _micros(target_cpa or 0, "target_cpa")
        bidding = ga_client.get_type("MaximizeConversions")
        bidding.target_cpa_micros = cpa_micros
        campaign.maximize_conversions = bidding
        op.update_mask.paths.append("maximize_conversions.target_cpa_micros")
        target_value: Any = cpa_micros
        target_label = f"{cpa_micros / 1_000_000:.2f}" if cpa_micros else "none"
        target_field = "Target CPA"
    else:
        roas = float(target_roas or 0)
        if roas and not (0.01 <= roas <= 1000):
            raise ToolError("Error: 'target_roas' must be between 0.01 and 1000.")
        bidding = ga_client.get_type("MaximizeConversionValue")
        bidding.target_roas = roas
        campaign.maximize_conversion_value = bidding
        op.update_mask.paths.append("maximize_conversion_value.target_roas")
        target_value = roas
        target_label = f"{roas * 100:.0f}%" if roas else "none"
        target_field = "Target ROAS"

    name, orig_strategy, orig_target = "", None, None
    rows = _lookup(
        ga_client,
        cid,
        "SELECT campaign.name, campaign.bidding_strategy_type, "
        "campaign.maximize_conversions.target_cpa_micros, "
        "campaign.maximize_conversion_value.target_roas "
        f"FROM campaign WHERE campaign.id = {camp_id}",
    )
    c = getattr(rows[0], "campaign", None) if rows else None
    if c is not None:
        name = str(getattr(c, "name", "") or "")
        orig_strategy = getattr(getattr(c, "bidding_strategy_type", None), "name", None)
        try:
            if orig_strategy == "MAXIMIZE_CONVERSIONS":
                micros = c.maximize_conversions.target_cpa_micros
                orig_target = f"{micros / 1_000_000:.2f}" if micros else "none"
            elif orig_strategy == "MAXIMIZE_CONVERSION_VALUE":
                r = c.maximize_conversion_value.target_roas
                orig_target = f"{r * 100:.0f}%" if r else "none"
        except AttributeError:
            pass

    operation_payload = {
        "tool": "update_campaign_bidding",
        "campaign_id": camp_id,
        "strategy": strategy_name,
        "target": target_value,
    }
    original_fields: dict[str, Any] = {"Bidding Strategy": orig_strategy}
    if orig_strategy == strategy_name:
        original_fields[target_field] = orig_target
    change_items = pac.build_change_items(
        operation="UPDATE",
        entity_readable="Campaign Bidding",
        primary_key_readable=f"{name} ({camp_id})" if name else resource_name,
        fields={"Bidding Strategy": strategy_name, target_field: target_label},
        original_fields=original_fields,
    )

    request = ga_client.get_type("MutateCampaignsRequest")
    request.customer_id = cid
    request.operations.append(op)

    def _validate() -> None:
        request.validate_only = True
        service.mutate_campaigns(request=request)

    def _commit() -> str:
        request.validate_only = False
        response = service.mutate_campaigns(request=request)
        return _summarize_results(response, "campaign bidding setting(s)", "updated")

    return pac.propose_and_confirm(
        customer_id=cid,
        validate_only=validate_only,
        checksum=checksum,
        operation_payload=operation_payload,
        change_items=change_items,
        validate_fn=_validate,
        commit_fn=_commit,
        error_prefix="Failed to update campaign bidding",
    )


# --------------------------------------------------------------------------
# Location targeting type
# --------------------------------------------------------------------------


@management_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True)
)
def update_campaign_location_targeting(
    customer_id: str | int,
    campaign_id: str | int,
    targeting_type: LocationTargetingType,
    login_customer_id: str | int | None = None,
    validate_only: bool = True,
    checksum: str | None = None,
) -> str:
    """Sets who a campaign's location targets reach.

    PRESENCE reaches only people in (or regularly in) the targeted locations.
    PRESENCE_OR_INTEREST also reaches people elsewhere who show interest in them.
    The targeted locations themselves are not changed.

    Propose & Confirm Workflow (`validate_only` and `checksum`):
    1. Call with `validate_only=True` (the default) to validate and get `change_items` and a `checksum`.
    2. Present the `change_items` to the user and wait for explicit approval.
    3. Only after approval, call again with the exact same parameters, `validate_only=False` and the `checksum`.

    Args:
        customer_id: Google Ads customer ID.
        campaign_id: ID of the campaign.
        targeting_type: 'PRESENCE' or 'PRESENCE_OR_INTEREST'.
        login_customer_id: Optional manager customer ID for the login-customer-id header.
        validate_only: If True (default), validate only and return a proposal. If False, commit; requires `checksum`.
        checksum: Checksum returned by the prior `validate_only=True` call.
    """
    cid = _clean_cid(customer_id)
    camp_id = _clean_id(campaign_id, "campaign_id")
    type_name = _enum_value(targeting_type, LocationTargetingType, "targeting_type")

    ga_client = utils.get_googleads_client(login_customer_id=login_customer_id)
    service = utils.get_googleads_service_from_client(ga_client, "CampaignService")

    resource_name = f"customers/{cid}/campaigns/{camp_id}"
    op = ga_client.get_type("CampaignOperation")
    op.update.resource_name = resource_name
    op.update.geo_target_type_setting.positive_geo_target_type = getattr(
        ga_client.get_type("PositiveGeoTargetTypeEnum").PositiveGeoTargetType,
        type_name,
    )
    op.update_mask.paths.append("geo_target_type_setting.positive_geo_target_type")

    name, original = "", None
    rows = _lookup(
        ga_client,
        cid,
        "SELECT campaign.name, campaign.geo_target_type_setting.positive_geo_target_type "
        f"FROM campaign WHERE campaign.id = {camp_id}",
    )
    c = getattr(rows[0], "campaign", None) if rows else None
    if c is not None:
        name = str(getattr(c, "name", "") or "")
        try:
            original = c.geo_target_type_setting.positive_geo_target_type.name
        except AttributeError:
            original = None

    operation_payload = {
        "tool": "update_campaign_location_targeting",
        "campaign_id": camp_id,
        "targeting_type": type_name,
    }
    change_items = pac.build_change_items(
        operation="UPDATE",
        entity_readable="Campaign Location Targeting",
        primary_key_readable=f"{name} ({camp_id})" if name else resource_name,
        fields={"Location Targeting Type": type_name},
        original_fields={"Location Targeting Type": original},
    )

    request = ga_client.get_type("MutateCampaignsRequest")
    request.customer_id = cid
    request.operations.append(op)

    def _validate() -> None:
        request.validate_only = True
        service.mutate_campaigns(request=request)

    def _commit() -> str:
        request.validate_only = False
        response = service.mutate_campaigns(request=request)
        return _summarize_results(response, "campaign location setting(s)", "updated")

    return pac.propose_and_confirm(
        customer_id=cid,
        validate_only=validate_only,
        checksum=checksum,
        operation_payload=operation_payload,
        change_items=change_items,
        validate_fn=_validate,
        commit_fn=_commit,
        error_prefix="Failed to update campaign location targeting",
    )


# --------------------------------------------------------------------------
# Ad schedule
# --------------------------------------------------------------------------


def _fmt_window(day: str, sh: int, sm: int, eh: int, em: int, mod: float | None) -> str:
    text = f"{day} {sh:02d}:{sm:02d}-{eh:02d}:{em:02d}"
    if mod:
        text += f" (bid x{mod:g})"
    return text


def _validate_windows(windows: list[AdScheduleWindow]) -> list[dict[str, Any]]:
    if len(windows) > _MAX_SCHEDULE_WINDOWS:
        raise ToolError(
            f"Error: At most {_MAX_SCHEDULE_WINDOWS} windows (6 per day) are allowed."
        )
    cleaned: list[dict[str, Any]] = []
    for w in windows:
        if isinstance(w, dict):
            w = AdScheduleWindow(**w)
        day = _enum_value(w.day_of_week, DayOfWeek, "day_of_week")
        if w.start_minute not in _MINUTE_ENUM or w.end_minute not in _MINUTE_ENUM:
            raise ToolError("Error: Minutes must be 0, 15, 30 or 45.")
        if w.end_hour == 24 and w.end_minute != 0:
            raise ToolError("Error: When end_hour is 24, end_minute must be 0.")
        start = w.start_hour * 60 + w.start_minute
        end = w.end_hour * 60 + w.end_minute
        if end <= start:
            raise ToolError(
                f"Error: Window on {day} must end after it starts "
                "(windows cannot cross midnight; split them per day)."
            )
        if w.bid_modifier is not None and not (0.1 <= w.bid_modifier <= 10):
            raise ToolError("Error: 'bid_modifier' must be between 0.1 and 10.")
        cleaned.append(
            {
                "day": day,
                "start_hour": w.start_hour,
                "start_minute": w.start_minute,
                "end_hour": w.end_hour,
                "end_minute": w.end_minute,
                "bid_modifier": w.bid_modifier,
                "_start": start,
                "_end": end,
            }
        )
    by_day: dict[str, list[dict[str, Any]]] = {}
    for c in cleaned:
        by_day.setdefault(c["day"], []).append(c)
    for day, items in by_day.items():
        if len(items) > 6:
            raise ToolError(f"Error: At most 6 windows per day ({day} has {len(items)}).")
        items.sort(key=lambda x: x["_start"])
        for prev, nxt in zip(items, items[1:]):
            if nxt["_start"] < prev["_end"]:
                raise ToolError(f"Error: Overlapping windows on {day}.")
    for c in cleaned:
        c.pop("_start")
        c.pop("_end")
    return cleaned


@management_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True)
)
def set_campaign_ad_schedule(
    customer_id: str | int,
    campaign_id: str | int,
    windows: list[AdScheduleWindow],
    login_customer_id: str | int | None = None,
    validate_only: bool = True,
    checksum: str | None = None,
) -> str:
    """Replaces a campaign's whole ad schedule with the given windows.

    All existing ad schedule windows of the campaign are removed and the given
    ones are created, in one atomic request. Times are in the account's time
    zone. Ads run only inside the windows; days without a window get no ads.
    Pass an empty list to remove the schedule entirely (ads run all the time).
    If the existing schedule changes between proposal and commit, the commit
    is rejected and a new proposal is needed.

    Example (Sunday-Thursday 08:00-20:00, Friday 08:00-14:00):
      windows=[{"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 20}, ...,
               {"day_of_week": "FRIDAY", "start_hour": 8, "end_hour": 14}]

    Propose & Confirm Workflow (`validate_only` and `checksum`):
    1. Call with `validate_only=True` (the default) to validate and get `change_items` (removed and added windows) and a `checksum`.
    2. Present the `change_items` to the user and wait for explicit approval.
    3. Only after approval, call again with the exact same parameters, `validate_only=False` and the `checksum`.

    Args:
        customer_id: Google Ads customer ID.
        campaign_id: ID of the campaign.
        windows: The complete new schedule (max 6 windows per day).
        login_customer_id: Optional manager customer ID for the login-customer-id header.
        validate_only: If True (default), validate only and return a proposal. If False, commit; requires `checksum`.
        checksum: Checksum returned by the prior `validate_only=True` call.
    """
    cid = _clean_cid(customer_id)
    camp_id = _clean_id(campaign_id, "campaign_id")
    new_windows = _validate_windows(list(windows or []))

    ga_client = utils.get_googleads_client(login_customer_id=login_customer_id)
    service = utils.get_googleads_service_from_client(
        ga_client, "CampaignCriterionService"
    )

    # The existing schedule decides which removals are sent, so a failed lookup
    # must stop the tool instead of silently leaving old windows in place.
    ga_service = utils.get_googleads_service_from_client(ga_client, "GoogleAdsService")
    query = (
        "SELECT campaign_criterion.criterion_id, "
        "campaign_criterion.ad_schedule.day_of_week, "
        "campaign_criterion.ad_schedule.start_hour, "
        "campaign_criterion.ad_schedule.start_minute, "
        "campaign_criterion.ad_schedule.end_hour, "
        "campaign_criterion.ad_schedule.end_minute, "
        "campaign_criterion.bid_modifier "
        "FROM campaign_criterion "
        f"WHERE campaign.id = {camp_id} "
        "AND campaign_criterion.type = 'AD_SCHEDULE' "
        "AND campaign_criterion.status != 'REMOVED'"
    )
    try:
        existing_rows = list(ga_service.search(customer_id=cid, query=query))
    except GoogleAdsException as exc:
        raise ToolError(
            "Failed to read the current ad schedule:\n"
            + utils.format_google_ads_error(exc)
        ) from exc

    existing: list[dict[str, Any]] = []
    for row in existing_rows:
        crit = row.campaign_criterion
        sched = crit.ad_schedule
        existing.append(
            {
                "criterion_id": str(crit.criterion_id),
                "label": _fmt_window(
                    getattr(sched.day_of_week, "name", str(sched.day_of_week)),
                    int(sched.start_hour),
                    _MINUTE_FROM_ENUM.get(getattr(sched.start_minute, "name", ""), 0),
                    int(sched.end_hour),
                    _MINUTE_FROM_ENUM.get(getattr(sched.end_minute, "name", ""), 0),
                    float(crit.bid_modifier) if crit.bid_modifier else None,
                ),
            }
        )
    existing.sort(key=lambda e: e["criterion_id"])

    if not existing and not new_windows:
        raise ToolError("Error: The campaign has no ad schedule and none was given.")

    request = ga_client.get_type("MutateCampaignCriteriaRequest")
    request.customer_id = cid
    campaign_rn = f"customers/{cid}/campaigns/{camp_id}"

    for e in existing:
        op = ga_client.get_type("CampaignCriterionOperation")
        op.remove = f"customers/{cid}/campaignCriteria/{camp_id}~{e['criterion_id']}"
        request.operations.append(op)

    day_enum = ga_client.get_type("DayOfWeekEnum").DayOfWeek
    minute_enum = ga_client.get_type("MinuteOfHourEnum").MinuteOfHour
    for w in new_windows:
        op = ga_client.get_type("CampaignCriterionOperation")
        crit = op.create
        crit.campaign = campaign_rn
        crit.ad_schedule.day_of_week = getattr(day_enum, w["day"])
        crit.ad_schedule.start_hour = w["start_hour"]
        crit.ad_schedule.start_minute = getattr(minute_enum, _MINUTE_ENUM[w["start_minute"]])
        crit.ad_schedule.end_hour = w["end_hour"]
        crit.ad_schedule.end_minute = getattr(minute_enum, _MINUTE_ENUM[w["end_minute"]])
        if w["bid_modifier"] is not None:
            crit.bid_modifier = float(w["bid_modifier"])
        request.operations.append(op)

    name = ""
    rows = _lookup(
        ga_client, cid, f"SELECT campaign.name FROM campaign WHERE campaign.id = {camp_id}"
    )
    if rows:
        name = str(getattr(getattr(rows[0], "campaign", None), "name", "") or "")
    target = f"{name} ({camp_id})" if name else campaign_rn

    operation_payload = {
        "tool": "set_campaign_ad_schedule",
        "campaign_id": camp_id,
        "remove_criterion_ids": [e["criterion_id"] for e in existing],
        "windows": new_windows,
    }
    change_items = [
        pac.ChangeItem(
            operation="REMOVE",
            entity_readable="Ad Schedule Window",
            primary_key_readable=target,
            field_readable="Window",
            value_readable=e["label"],
        )
        for e in existing
    ] + [
        pac.ChangeItem(
            operation="CREATE",
            entity_readable="Ad Schedule Window",
            primary_key_readable=target,
            field_readable="Window",
            value_readable=_fmt_window(
                w["day"], w["start_hour"], w["start_minute"],
                w["end_hour"], w["end_minute"], w["bid_modifier"],
            ),
        )
        for w in new_windows
    ]

    def _validate() -> None:
        request.validate_only = True
        service.mutate_campaign_criteria(request=request)

    def _commit() -> str:
        request.validate_only = False
        service.mutate_campaign_criteria(request=request)
        return (
            f"Successfully replaced the ad schedule of campaign {target}: "
            f"removed {len(existing)} window(s), added {len(new_windows)}."
        )

    return pac.propose_and_confirm(
        customer_id=cid,
        validate_only=validate_only,
        checksum=checksum,
        operation_payload=operation_payload,
        change_items=change_items,
        validate_fn=_validate,
        commit_fn=_commit,
        error_prefix="Failed to set campaign ad schedule",
    )
