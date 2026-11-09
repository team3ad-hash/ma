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

"""General-purpose write tools.

* ``mutate`` - any of the 62 operation types supported by
  ``GoogleAdsService.Mutate`` (campaigns, ad groups, ads, assets, budgets,
  criteria, bidding strategies, conversion actions, audiences, experiments,
  labels, shared sets, ...), in one atomic request. Billing, account access
  and account linking are not part of that API and are therefore not
  reachable.
* ``create_search_campaign`` - a complete Search campaign (budget, campaign,
  locations, languages, ad group, keywords, responsive search ad) in one
  atomic request. The campaign is always created PAUSED.
* ``upload_click_conversions`` - offline conversion import by GCLID.

All three follow the propose-and-confirm workflow (``validate_only=True``
first, then ``validate_only=False`` with the returned ``checksum``).
"""

import json
from typing import Any

from fastmcp.exceptions import ToolError
from google.protobuf import json_format
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from ads_mcp import propose_and_confirm as pac
import ads_mcp.utils as utils
from ads_mcp.tools.campaign_management import (
    _clean_cid,
    _clean_id,
    _clean_keywords,
    _enum_value,
    MatchType,
    management_mcp,
)

_MAX_OPERATIONS = 1000
_MAX_CONVERSIONS = 2000
_PREVIEW_CHARS = 600


# --------------------------------------------------------------------------
# Shared engine
# --------------------------------------------------------------------------


def _pb(message: Any) -> Any:
    """Returns the raw protobuf of a proto-plus message (or the message itself)."""
    try:
        return type(message).pb(message)
    except (AttributeError, TypeError):
        return message


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_strings(v)


def _check_customer_scope(cid: str, value: Any) -> None:
    """Rejects resource names that point at a different customer account."""
    prefix = f"customers/{cid}/"
    for text in _walk_strings(value):
        if text.startswith("customers/") and not (
            text.startswith(prefix) or text == f"customers/{cid}"
        ):
            raise ToolError(
                f"Error: Resource name '{text}' belongs to a different account "
                f"than customer_id {cid}."
            )


def _parse_operations(ga_client: Any, cid: str, operations: list[dict]) -> tuple[list[Any], list[dict]]:
    """Parses JSON operations into MutateOperation messages.

    Returns the messages and their canonical (snake_case) dict form, which is
    used for the checksum and the change summary.
    """
    if not operations:
        raise ToolError("Error: 'operations' must contain at least one operation.")
    if len(operations) > _MAX_OPERATIONS:
        raise ToolError(
            f"Error: At most {_MAX_OPERATIONS} operations per call (got {len(operations)})."
        )
    messages: list[Any] = []
    canonical: list[dict] = []
    for index, raw in enumerate(operations):
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ToolError(f"Error: Operation #{index} is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict) or len(raw) != 1:
            raise ToolError(
                f"Error: Operation #{index} must be an object with exactly one key, "
                "e.g. {\"campaign_operation\": {\"update\": {...}, \"update_mask\": \"status\"}}."
            )
        op = ga_client.get_type("MutateOperation")
        try:
            json_format.ParseDict(raw, _pb(op))
        except json_format.ParseError as exc:
            raise ToolError(f"Error: Operation #{index} is invalid: {exc}") from exc
        as_dict = json_format.MessageToDict(_pb(op), preserving_proto_field_name=True)
        if len(as_dict) != 1:
            raise ToolError(f"Error: Operation #{index} is empty.")
        inner = next(iter(as_dict.values()))
        if not any(k in inner for k in ("create", "update", "remove")):
            raise ToolError(
                f"Error: Operation #{index} needs one of 'create', 'update' or 'remove'."
            )
        if "update" in inner and not inner.get("update_mask"):
            raise ToolError(
                f"Error: Operation #{index} is an update without 'update_mask' "
                "(comma-separated field paths, e.g. \"status,name\")."
            )
        _check_customer_scope(cid, as_dict)
        messages.append(op)
        canonical.append(as_dict)
    return messages, canonical


def _summarize_operation(op_dict: dict) -> pac.ChangeItem:
    key, inner = next(iter(op_dict.items()))
    entity = key.removesuffix("_operation")
    if "remove" in inner:
        return pac.ChangeItem(
            operation="REMOVE",
            entity_readable=entity,
            primary_key_readable=inner["remove"],
            field_readable="(irreversible)",
            value_readable="remove",
        )
    action = "CREATE" if "create" in inner else "UPDATE"
    body = inner.get("create") or inner.get("update") or {}
    preview = json.dumps(body, ensure_ascii=False, sort_keys=True)
    if len(preview) > _PREVIEW_CHARS:
        preview = preview[:_PREVIEW_CHARS] + " ..."
    return pac.ChangeItem(
        operation=action,
        entity_readable=entity,
        primary_key_readable=str(body.get("resource_name", "")),
        field_readable=(
            f"fields: {inner.get('update_mask')}" if action == "UPDATE" else "new resource"
        ),
        value_readable=preview,
    )


def _result_names(response: Any) -> list[str]:
    names: list[str] = []
    for item in getattr(response, "mutate_operation_responses", []) or []:
        try:
            d = json_format.MessageToDict(_pb(item), preserving_proto_field_name=True)
            result = next(iter(d.values()), {})
            names.append(str(result.get("resource_name", "")))
        except Exception:  # pylint: disable=broad-except
            names.append("")
    return names


def _run_mutate(
    *,
    tool: str,
    cid: str,
    login_customer_id: str | int | None,
    operations: list[dict],
    validate_only: bool,
    checksum: str | None,
    extra_change_items: list[pac.ChangeItem] | None = None,
) -> str:
    ga_client = utils.get_googleads_client(login_customer_id=login_customer_id)
    messages, canonical = _parse_operations(ga_client, cid, operations)
    service = utils.get_googleads_service_from_client(ga_client, "GoogleAdsService")

    request = ga_client.get_type("MutateGoogleAdsRequest")
    request.customer_id = cid
    for message in messages:
        request.mutate_operations.append(message)

    change_items = list(extra_change_items or []) + [
        _summarize_operation(d) for d in canonical
    ]
    operation_payload = {"tool": tool, "operations": canonical}

    def _validate() -> None:
        request.validate_only = True
        service.mutate(request=request)

    def _commit() -> str:
        request.validate_only = False
        response = service.mutate(request=request)
        names = [n for n in _result_names(response) if n]
        lines = [f"Successfully applied {len(messages)} operation(s)."]
        lines += [f"- {n}" for n in names[:50]]
        if len(names) > 50:
            lines.append(f"... and {len(names) - 50} more")
        return "\n".join(lines)

    return pac.propose_and_confirm(
        customer_id=cid,
        validate_only=validate_only,
        checksum=checksum,
        operation_payload=operation_payload,
        change_items=change_items,
        validate_fn=_validate,
        commit_fn=_commit,
        error_prefix="Failed to apply operations",
    )


# --------------------------------------------------------------------------
# Generic mutate
# --------------------------------------------------------------------------


@management_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True)
)
def mutate(
    customer_id: str | int,
    operations: list[dict],
    login_customer_id: str | int | None = None,
    validate_only: bool = True,
    checksum: str | None = None,
) -> str:
    """Applies any Google Ads changes through GoogleAdsService.Mutate, atomically.

    Use this for anything the dedicated tools do not cover: creating or
    editing campaigns, ad groups, ads (responsive search ads, etc.), assets and
    asset links (sitelinks, callouts, calls), Performance Max asset groups and
    signals, bid modifiers, audiences and user lists, conversion actions and
    value rules, bidding strategies, labels, shared sets, experiments, account
    settings (customer_operation) and more. Prefer the dedicated tools when
    one fits. All operations succeed or fail together.

    Each item of `operations` is one MutateOperation in Google Ads API JSON
    form, with exactly one key. Field names may be snake_case or camelCase and
    enum values are strings. Examples:
      {"campaign_operation": {"update": {"resource_name": "customers/123/campaigns/456", "status": "PAUSED"}, "update_mask": "status"}}
      {"ad_group_ad_operation": {"update": {"resource_name": "customers/123/adGroupAds/789~111", "status": "PAUSED"}, "update_mask": "status"}}
      {"campaign_criterion_operation": {"remove": "customers/123/campaignCriteria/456~222"}}
      {"campaign_budget_operation": {"create": {"resource_name": "customers/123/campaignBudgets/-1", "name": "B", "amount_micros": "100000000", "delivery_method": "STANDARD", "explicitly_shared": false}}}
    Updates require `update_mask` (comma-separated field paths). New resources
    can reference each other in the same call through temporary negative IDs
    (e.g. campaignBudgets/-1 used by a campaign created in the same call).
    Every resource name must belong to `customer_id`. Up to 1000 operations.
    Look up valid fields with the metadata tool first; do not guess them.

    Propose & Confirm Workflow (`validate_only` and `checksum`):
    1. Call with `validate_only=True` (the default). Google Ads validates every operation without committing, and the tool returns `change_items` and a `checksum`.
    2. Present the `change_items` to the user and wait for explicit approval. Point out any REMOVE operations: they cannot be undone.
    3. Only after approval, call again with the exact same `operations`, `validate_only=False` and the `checksum`.

    Args:
        customer_id: Google Ads customer ID.
        operations: List of MutateOperation objects (JSON), max 1000.
        login_customer_id: Optional manager customer ID for the login-customer-id header.
        validate_only: If True (default), validate only and return a proposal. If False, commit; requires `checksum`.
        checksum: Checksum returned by the prior `validate_only=True` call.
    """
    cid = _clean_cid(customer_id)
    return _run_mutate(
        tool="mutate",
        cid=cid,
        login_customer_id=login_customer_id,
        operations=operations,
        validate_only=validate_only,
        checksum=checksum,
    )


# --------------------------------------------------------------------------
# Search campaign builder
# --------------------------------------------------------------------------


class KeywordSpec(BaseModel):
    """A keyword for the new ad group."""

    text: str = Field(description="Keyword text without quotes or brackets.")
    match_type: MatchType = Field(default=MatchType.PHRASE, description="BROAD, PHRASE or EXACT.")


@management_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False)
)
def create_search_campaign(
    customer_id: str | int,
    campaign_name: str,
    daily_budget: float,
    ad_group_name: str,
    keywords: list[KeywordSpec],
    final_url: str,
    headlines: list[str],
    descriptions: list[str],
    location_ids: list[str] | None = None,
    language_ids: list[str] | None = None,
    target_cpa: float | None = None,
    negative_keywords: list[str] | None = None,
    path1: str | None = None,
    path2: str | None = None,
    login_customer_id: str | int | None = None,
    validate_only: bool = True,
    checksum: str | None = None,
) -> str:
    """Creates a complete Search campaign in one atomic request, always PAUSED.

    Creates: a daily budget, the campaign (Google Search only, no search
    partners or display, location targeting by PRESENCE, Maximize
    Conversions with optional target CPA), location and language targets,
    optional campaign negatives, one ad group, its keywords and one
    responsive search ad. Nothing spends money until the campaign is enabled
    (e.g. with update_campaign_status) after review.

    Defaults: location 2376 (Israel), language 1027 (Hebrew). Look up other
    IDs with a search on `geo_target_constant` / `language_constant`.

    Propose & Confirm Workflow (`validate_only` and `checksum`):
    1. Call with `validate_only=True` (the default) to validate the whole structure and get `change_items` and a `checksum`.
    2. Present the `change_items` to the user and wait for explicit approval.
    3. Only after approval, call again with the exact same parameters, `validate_only=False` and the `checksum`.

    Args:
        customer_id: Google Ads customer ID.
        campaign_name: Unique campaign name.
        daily_budget: Daily budget in account currency (e.g. 150 for ₪150).
        ad_group_name: Name of the first ad group.
        keywords: Keywords with match types (max 500).
        final_url: Landing page URL for the ad (https://...).
        headlines: 3-15 headlines, max 30 characters each.
        descriptions: 2-4 descriptions, max 90 characters each.
        location_ids: Geo target constant IDs. Default ['2376'] (Israel).
        language_ids: Language constant IDs. Default ['1027'] (Hebrew).
        target_cpa: Optional target cost per conversion in account currency.
        negative_keywords: Optional campaign negative keywords (phrase match).
        path1: Optional display URL path 1 (max 15 characters).
        path2: Optional display URL path 2 (max 15 characters, requires path1).
        login_customer_id: Optional manager customer ID for the login-customer-id header.
        validate_only: If True (default), validate only and return a proposal. If False, commit; requires `checksum`.
        checksum: Checksum returned by the prior `validate_only=True` call.
    """
    cid = _clean_cid(customer_id)
    if not campaign_name.strip() or not ad_group_name.strip():
        raise ToolError("Error: 'campaign_name' and 'ad_group_name' are required.")
    try:
        budget = float(daily_budget)
    except (TypeError, ValueError) as exc:
        raise ToolError("Error: 'daily_budget' must be a number.") from exc
    if budget <= 0:
        raise ToolError("Error: 'daily_budget' must be greater than 0.")
    if not final_url.startswith(("https://", "http://")):
        raise ToolError("Error: 'final_url' must start with https:// or http://.")

    heads = [h.strip() for h in headlines if h and h.strip()]
    descs = [d.strip() for d in descriptions if d and d.strip()]
    if not 3 <= len(heads) <= 15 or any(len(h) > 30 for h in heads):
        raise ToolError("Error: Provide 3-15 headlines of at most 30 characters.")
    if not 2 <= len(descs) <= 4 or any(len(d) > 90 for d in descs):
        raise ToolError("Error: Provide 2-4 descriptions of at most 90 characters.")
    for p in (path1, path2):
        if p and len(p) > 15:
            raise ToolError("Error: 'path1' and 'path2' are limited to 15 characters.")
    if path2 and not path1:
        raise ToolError("Error: 'path2' requires 'path1'.")

    kw_specs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for spec in keywords or []:
        if isinstance(spec, dict):
            spec = KeywordSpec(**spec)
        text = _clean_keywords([spec.text])[0]
        mt = _enum_value(spec.match_type, MatchType, "match_type")
        if (text.lower(), mt) not in seen:
            seen.add((text.lower(), mt))
            kw_specs.append((text, mt))
    if not kw_specs:
        raise ToolError("Error: Provide at least one keyword.")
    if len(kw_specs) > 500:
        raise ToolError("Error: At most 500 keywords.")
    negatives = _clean_keywords(negative_keywords) if negative_keywords else []

    locations = [_clean_id(x, "location_ids") for x in (location_ids or ["2376"])]
    languages = [_clean_id(x, "language_ids") for x in (language_ids or ["1027"])]
    budget_micros = int(round(budget * 100)) * 10_000
    cpa_micros = int(round(float(target_cpa) * 100)) * 10_000 if target_cpa else 0

    budget_rn = f"customers/{cid}/campaignBudgets/-1"
    campaign_rn = f"customers/{cid}/campaigns/-2"
    ad_group_rn = f"customers/{cid}/adGroups/-3"

    ops: list[dict] = [
        {"campaign_budget_operation": {"create": {
            "resource_name": budget_rn,
            "name": f"{campaign_name} - budget",
            "amount_micros": str(budget_micros),
            "delivery_method": "STANDARD",
            "explicitly_shared": False,
        }}},
        {"campaign_operation": {"create": {
            "resource_name": campaign_rn,
            "name": campaign_name,
            "status": "PAUSED",
            "advertising_channel_type": "SEARCH",
            "campaign_budget": budget_rn,
            "maximize_conversions": {"target_cpa_micros": str(cpa_micros)},
            "network_settings": {
                "target_google_search": True,
                "target_search_network": False,
                "target_content_network": False,
                "target_partner_search_network": False,
            },
            "geo_target_type_setting": {"positive_geo_target_type": "PRESENCE"},
            "contains_eu_political_advertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING",
        }}},
    ]
    for loc in locations:
        ops.append({"campaign_criterion_operation": {"create": {
            "campaign": campaign_rn,
            "location": {"geo_target_constant": f"geoTargetConstants/{loc}"},
        }}})
    for lang in languages:
        ops.append({"campaign_criterion_operation": {"create": {
            "campaign": campaign_rn,
            "language": {"language_constant": f"languageConstants/{lang}"},
        }}})
    for neg in negatives:
        ops.append({"campaign_criterion_operation": {"create": {
            "campaign": campaign_rn,
            "negative": True,
            "keyword": {"text": neg, "match_type": "PHRASE"},
        }}})
    ops.append({"ad_group_operation": {"create": {
        "resource_name": ad_group_rn,
        "name": ad_group_name,
        "campaign": campaign_rn,
        "status": "ENABLED",
        "type": "SEARCH_STANDARD",
    }}})
    for text, mt in kw_specs:
        ops.append({"ad_group_criterion_operation": {"create": {
            "ad_group": ad_group_rn,
            "status": "ENABLED",
            "keyword": {"text": text, "match_type": mt},
        }}})
    rsa: dict[str, Any] = {
        "headlines": [{"text": h} for h in heads],
        "descriptions": [{"text": d} for d in descs],
    }
    if path1:
        rsa["path1"] = path1
    if path2:
        rsa["path2"] = path2
    ops.append({"ad_group_ad_operation": {"create": {
        "ad_group": ad_group_rn,
        "status": "ENABLED",
        "ad": {"final_urls": [final_url], "responsive_search_ad": rsa},
    }}})

    overview = pac.build_change_items(
        operation="CREATE",
        entity_readable="Search Campaign (PAUSED)",
        primary_key_readable=campaign_name,
        fields={
            "Daily Budget": f"{budget_micros / 1_000_000:.2f}",
            "Bidding": "MAXIMIZE_CONVERSIONS"
            + (f", target CPA {cpa_micros / 1_000_000:.2f}" if cpa_micros else ""),
            "Locations": ", ".join(locations),
            "Languages": ", ".join(languages),
            "Ad Group": ad_group_name,
            "Keywords": ", ".join(f"{t} [{m}]" for t, m in kw_specs),
            "Negative Keywords": ", ".join(negatives) or None,
            "Final URL": final_url,
            "Headlines": " | ".join(heads),
            "Descriptions": " | ".join(descs),
        },
    )
    return _run_mutate(
        tool="create_search_campaign",
        cid=cid,
        login_customer_id=login_customer_id,
        operations=ops,
        validate_only=validate_only,
        checksum=checksum,
        extra_change_items=overview,
    )


# --------------------------------------------------------------------------
# Offline conversion import
# --------------------------------------------------------------------------


class ClickConversionSpec(BaseModel):
    """One offline conversion tied to an ad click."""

    gclid: str = Field(description="Google click ID captured with the lead.")
    conversion_action_id: str = Field(description="ID of an UPLOAD_CLICKS conversion action.")
    conversion_date_time: str = Field(
        description="'yyyy-mm-dd hh:mm:ss+hh:mm', e.g. '2026-11-09 14:30:00+02:00'."
    )
    conversion_value: float | None = Field(default=None, description="Optional value.")
    currency_code: str | None = Field(default=None, description="e.g. 'ILS'.")
    order_id: str | None = Field(default=None, description="Optional unique ID to prevent duplicates.")


@management_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False)
)
def upload_click_conversions(
    customer_id: str | int,
    conversions: list[ClickConversionSpec],
    login_customer_id: str | int | None = None,
    validate_only: bool = True,
    checksum: str | None = None,
) -> str:
    """Uploads offline conversions (e.g. 'meeting set', 'deal closed') by GCLID.

    The conversion action must be of type UPLOAD_CLICKS (create one with
    `mutate` if needed). Clicks must be at most 90 days old. Rows are
    processed with partial failure: valid rows are accepted and each failing
    row is reported.

    Propose & Confirm Workflow (`validate_only` and `checksum`):
    1. Call with `validate_only=True` (the default) to validate and get `change_items` and a `checksum`.
    2. Present the `change_items` to the user and wait for explicit approval.
    3. Only after approval, call again with the exact same parameters, `validate_only=False` and the `checksum`.

    Args:
        customer_id: Google Ads customer ID.
        conversions: Conversions to upload (max 2000 per call).
        login_customer_id: Optional manager customer ID for the login-customer-id header.
        validate_only: If True (default), validate only and return a proposal. If False, commit; requires `checksum`.
        checksum: Checksum returned by the prior `validate_only=True` call.
    """
    cid = _clean_cid(customer_id)
    rows: list[dict[str, Any]] = []
    for spec in conversions or []:
        if isinstance(spec, dict):
            spec = ClickConversionSpec(**spec)
        if not spec.gclid.strip():
            raise ToolError("Error: Every conversion needs a 'gclid'.")
        rows.append(
            {
                "gclid": spec.gclid.strip(),
                "conversion_action": f"customers/{cid}/conversionActions/"
                + _clean_id(spec.conversion_action_id, "conversion_action_id"),
                "conversion_date_time": spec.conversion_date_time.strip(),
                "conversion_value": spec.conversion_value,
                "currency_code": spec.currency_code,
                "order_id": spec.order_id,
            }
        )
    if not rows:
        raise ToolError("Error: 'conversions' must contain at least one conversion.")
    if len(rows) > _MAX_CONVERSIONS:
        raise ToolError(f"Error: At most {_MAX_CONVERSIONS} conversions per call.")

    ga_client = utils.get_googleads_client(login_customer_id=login_customer_id)
    service = utils.get_googleads_service_from_client(ga_client, "ConversionUploadService")

    request = ga_client.get_type("UploadClickConversionsRequest")
    request.customer_id = cid
    request.partial_failure = True
    for row in rows:
        conv = ga_client.get_type("ClickConversion")
        conv.gclid = row["gclid"]
        conv.conversion_action = row["conversion_action"]
        conv.conversion_date_time = row["conversion_date_time"]
        if row["conversion_value"] is not None:
            conv.conversion_value = float(row["conversion_value"])
        if row["currency_code"]:
            conv.currency_code = row["currency_code"]
        if row["order_id"]:
            conv.order_id = row["order_id"]
        request.conversions.append(conv)

    change_items = [
        pac.ChangeItem(
            operation="CREATE",
            entity_readable="Offline Conversion",
            primary_key_readable=row["conversion_action"],
            field_readable=row["conversion_date_time"],
            value_readable=(
                f"gclid {row['gclid'][:12]}..."
                + (f", value {row['conversion_value']}" if row["conversion_value"] is not None else "")
            ),
        )
        for row in rows
    ]

    def _partial_errors(response: Any) -> str:
        err = getattr(response, "partial_failure_error", None)
        message = getattr(err, "message", "") if err is not None else ""
        return message or ""

    def _validate() -> None:
        request.validate_only = True
        response = service.upload_click_conversions(request=request)
        errors = _partial_errors(response)
        if errors:
            raise ToolError(f"Validation found problems:\n{errors}")

    def _commit() -> str:
        request.validate_only = False
        response = service.upload_click_conversions(request=request)
        errors = _partial_errors(response)
        accepted = sum(
            1 for r in (getattr(response, "results", []) or []) if getattr(r, "gclid", "")
        )
        text = f"Uploaded {accepted} of {len(rows)} conversion(s)."
        if errors:
            text += f"\nRejected rows:\n{errors}"
        return text

    return pac.propose_and_confirm(
        customer_id=cid,
        validate_only=validate_only,
        checksum=checksum,
        operation_payload={"tool": "upload_click_conversions", "conversions": rows},
        change_items=change_items,
        validate_fn=_validate,
        commit_fn=_commit,
        error_prefix="Failed to upload click conversions",
    )
