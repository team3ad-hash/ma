"""Core write path: turns operation dicts into a GoogleAdsService.Mutate call.

Every write tool in this package funnels through `run_mutate`, so the safety
rules live in one place:

* Dry run by default: requests are sent with `validate_only=True`, which makes
  Google validate the full request without changing anything.
* Real writes require the environment variable
  `GOOGLE_ADS_MCP_ENABLE_WRITES=true` on the server.
* Remove operations (irreversible) require `allow_remove=True`.
* New campaigns, ad groups, ads and asset groups are created PAUSED unless a
  status is given explicitly.
"""

import os
import re
from typing import Any, Dict, Iterable, List

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v26.errors.types.errors import GoogleAdsFailure
from google.ads.googleads.v26.services.types.google_ads_service import (
    MutateGoogleAdsRequest,
    MutateOperation,
)
from google.protobuf import json_format

import ads_mcp.utils as utils
from ads_mcp.mcp_header_interceptor import MCPHeaderInterceptor

API_VERSION = "v26"
WRITES_ENV = "GOOGLE_ADS_MCP_ENABLE_WRITES"

# Operation kinds whose new entities start PAUSED when no status is given.
_PAUSED_BY_DEFAULT = {
    "campaign_operation",
    "ad_group_operation",
    "ad_group_ad_operation",
    "asset_group_operation",
}

_OPERATION_KINDS = set(MutateOperation.meta.fields)


def writes_enabled() -> bool:
    return os.environ.get(WRITES_ENV, "").strip().lower() == "true"


def _snake(name: str) -> str:
    """Converts a JSON (camelCase) or python-escaped (`type_`) key to proto."""
    name = name.rstrip("_")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {_snake(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def field_mask_paths(update: Dict[str, Any], prefix: str = "") -> List[str]:
    """Returns the update-mask paths for exactly the fields present in `update`.

    Unlike `protobuf_helpers.field_mask`, this keeps fields explicitly set to
    false/0 and empty messages (e.g. `{"manual_cpc": {}}`), which matter when
    switching bidding strategies or turning networks off.
    """
    paths = []
    for key, value in update.items():
        if key == "resource_name":
            continue
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            paths.extend(field_mask_paths(value, f"{path}."))
        else:
            paths.append(path)
    return paths


def build_operations(
    operations: Iterable[Dict[str, Any]],
    allow_remove: bool = False,
) -> tuple[List[MutateOperation], List[str]]:
    """Parses operation dicts into MutateOperation messages.

    Each dict holds exactly one operation kind, e.g.
    `{"campaign_operation": {"update": {...}, "update_mask": "status"}}`.
    Returns the messages and a list of notes about defaults that were applied.
    """
    parsed: List[MutateOperation] = []
    notes: List[str] = []

    for index, raw in enumerate(operations):
        op = _normalize(raw)
        if len(op) != 1:
            raise ToolError(
                f"Operation {index} must contain exactly one operation kind "
                f"(e.g. 'campaign_operation'), got: {sorted(op)}"
            )
        kind, body = next(iter(op.items()))
        if kind not in _OPERATION_KINDS:
            raise ToolError(f"Operation {index}: unknown operation kind '{kind}'.")
        if not isinstance(body, dict):
            raise ToolError(f"Operation {index}: '{kind}' must be an object.")

        actions = [a for a in ("create", "update", "remove") if a in body]
        if len(actions) != 1:
            raise ToolError(
                f"Operation {index}: '{kind}' needs exactly one of "
                f"create/update/remove, got: {actions or 'none'}"
            )
        action = actions[0]

        if action == "remove" and not allow_remove:
            raise ToolError(
                f"Operation {index} removes '{body['remove']}'. Removal cannot "
                "be undone; pass allow_remove=true only after the user has "
                "explicitly confirmed it (pausing is usually the safer choice)."
            )

        if action == "create" and kind in _PAUSED_BY_DEFAULT:
            if "status" not in body["create"]:
                body["create"]["status"] = "PAUSED"
                notes.append(f"Operation {index}: new {kind[:-10]} set to PAUSED.")

        update_mask = body.pop("update_mask", None)
        if action == "update":
            if update_mask is None:
                paths = field_mask_paths(body["update"])
            elif isinstance(update_mask, str):
                paths = [p.strip() for p in update_mask.split(",") if p.strip()]
            else:
                paths = list(update_mask)
            paths = [".".join(_snake(part) for part in p.split(".")) for p in paths]
            if not paths:
                raise ToolError(f"Operation {index}: update has no fields.")

        message = MutateOperation()
        try:
            json_format.ParseDict({kind: body}, message._pb)
        except json_format.ParseError as ex:
            raise ToolError(f"Operation {index}: invalid fields: {ex}")
        if action == "update":
            getattr(message._pb, kind).update_mask.paths.extend(paths)
        parsed.append(message)

    if not parsed:
        raise ToolError("No operations given.")
    return parsed, notes


def _format_google_ads_errors(failure: GoogleAdsFailure) -> List[str]:
    messages = []
    for error in failure.errors:
        location = ".".join(
            f"{el.field_name}[{el.index}]" if "index" in el else el.field_name
            for el in error.location.field_path_elements
        )
        messages.append(
            f"{error.message}" + (f" (at {location})" if location else "")
        )
    return messages


def _partial_failure_errors(response) -> List[str]:
    status = response.partial_failure_error
    if not status or not status.code:
        return []
    errors = []
    for detail in status.details:
        failure = GoogleAdsFailure.deserialize(detail.value)
        errors.extend(_format_google_ads_errors(failure))
    return errors or [status.message]


def get_service(name: str, login_customer_id: str | int | None = None):
    return utils.get_googleads_client(
        login_customer_id=login_customer_id
    ).get_service(name, version=API_VERSION, interceptors=[MCPHeaderInterceptor()])


def run_mutate(
    customer_id: str | int,
    operations: Iterable[Dict[str, Any]],
    validate_only: bool = True,
    partial_failure: bool = False,
    allow_remove: bool = False,
    login_customer_id: str | int | None = None,
) -> Dict[str, Any]:
    """Validates or executes the given operations atomically (unless partial_failure)."""
    if not validate_only and not writes_enabled():
        raise ToolError(
            "Writes are disabled on this server. Set the environment variable "
            f"{WRITES_ENV}=true and restart it to apply changes. You can still "
            "run with validate_only=true to check the request."
        )

    mutate_operations, notes = build_operations(operations, allow_remove)
    customer_id = utils.clean_customer_id(customer_id)

    request = MutateGoogleAdsRequest(
        customer_id=customer_id,
        mutate_operations=mutate_operations,
        validate_only=validate_only,
        partial_failure=partial_failure,
    )
    utils.logger.info(
        f"ads_write_mcp.mutate customer={customer_id} "
        f"operations={len(mutate_operations)} validate_only={validate_only}"
    )

    service = get_service("GoogleAdsService", login_customer_id)
    try:
        response = service.mutate(request=request)
    except GoogleAdsException as ex:
        raise ToolError(
            f"Request ID: {ex.request_id}\n"
            + "\n".join(
                f"Google Ads API Error: {m}"
                for m in _format_google_ads_errors(ex.failure)
            )
        )

    results = []
    for op_response in response.mutate_operation_responses:
        result = json_format.MessageToDict(
            op_response._pb, preserving_proto_field_name=True
        )
        for kind, value in result.items():
            results.append(
                {"result": kind, "resource_name": value.get("resource_name")}
            )

    output: Dict[str, Any] = {
        "validate_only": validate_only,
        "operation_count": len(mutate_operations),
        "notes": notes,
    }
    if validate_only:
        output["status"] = (
            "VALID - nothing was changed. Show the user what will change and, "
            "after they confirm, call again with validate_only=false."
        )
    else:
        output["status"] = "APPLIED"
        output["results"] = results
    errors = _partial_failure_errors(response)
    if errors:
        output["partial_failure_errors"] = errors
    return output


def search_rows(
    customer_id: str | int,
    query: str,
    login_customer_id: str | int | None = None,
) -> List[Any]:
    """Runs a GAQL query and returns the raw rows (used for lookups)."""
    service = get_service("GoogleAdsService", login_customer_id)
    try:
        stream = service.search_stream(
            customer_id=utils.clean_customer_id(customer_id), query=query
        )
        return [row for batch in stream for row in batch.results]
    except GoogleAdsException as ex:
        raise ToolError(
            f"Request ID: {ex.request_id}\n"
            + "\n".join(_format_google_ads_errors(ex.failure))
        )
