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

"""Test cases for the general-purpose write tools."""

import json
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from google.ads.googleads.client import GoogleAdsClient
from google.auth.credentials import AnonymousCredentials
from google.protobuf import json_format

from ads_mcp.config import ToolsConfig
from ads_mcp.coordinator import initialize_and_mount_tools
from ads_mcp.tools import advanced_mutate as am

CID = "1234567890"


class TestAdvancedMutate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.real_ga_client = GoogleAdsClient(
            credentials=AnonymousCredentials(),
            developer_token="fake-token",
            use_proto_plus=True,
        )

    def setUp(self):
        self.services: dict[str, MagicMock] = {}
        self.mock_client = MagicMock()

        def get_service(name, **kwargs):
            if name not in self.services:
                self.services[name] = MagicMock()
            return self.services[name]

        self.mock_client.get_service.side_effect = get_service
        self.mock_client.get_type.side_effect = self.real_ga_client.get_type
        patcher = patch("ads_mcp.utils.get_googleads_client", return_value=self.mock_client)
        patcher.start()
        self.addCleanup(patcher.stop)

        resp = self.real_ga_client.get_type("MutateGoogleAdsResponse")
        json_format.ParseDict(
            {"mutate_operation_responses": [
                {"campaign_result": {"resource_name": f"customers/{CID}/campaigns/5"}}
            ]},
            type(resp).pb(resp),
        )
        self.mock_client.get_service("GoogleAdsService").mutate.return_value = resp

    def _propose_then_commit(self, fn, **kwargs):
        proposal = json.loads(fn(**kwargs))
        self.assertEqual(proposal["status"], "PROPOSED")
        result = fn(**kwargs, validate_only=False, checksum=proposal["checksum"])
        return proposal, result

    # ---- mutate ---------------------------------------------------------

    def test_mutate_update_campaign(self):
        ops = [{"campaignOperation": {
            "update": {"resourceName": f"customers/{CID}/campaigns/5", "status": "PAUSED"},
            "updateMask": "status",
        }}]
        proposal, result = self._propose_then_commit(am.mutate, customer_id=CID, operations=ops)
        item = proposal["change_items"][0]
        self.assertEqual(item["operation"], "UPDATE")
        self.assertEqual(item["entity_readable"], "campaign")
        self.assertIn("PAUSED", item["value_readable"])

        svc = self.mock_client.get_service("GoogleAdsService")
        self.assertEqual(svc.mutate.call_count, 2)
        request = svc.mutate.call_args.kwargs["request"]
        self.assertFalse(request.validate_only)
        op = request.mutate_operations[0].campaign_operation
        self.assertEqual(op.update.status.name, "PAUSED")
        self.assertEqual(list(op.update_mask.paths), ["status"])
        self.assertIn(f"customers/{CID}/campaigns/5", result)

    def test_mutate_remove_is_flagged(self):
        ops = [{"campaign_criterion_operation": {"remove": f"customers/{CID}/campaignCriteria/5~9"}}]
        proposal = json.loads(am.mutate(customer_id=CID, operations=ops))
        self.assertEqual(proposal["change_items"][0]["operation"], "REMOVE")
        self.assertIn("irreversible", proposal["change_items"][0]["field_readable"])

    def test_mutate_rejects_other_account(self):
        ops = [{"campaign_operation": {"remove": "customers/999/campaigns/5"}}]
        with self.assertRaises(ToolError):
            am.mutate(customer_id=CID, operations=ops)

    def test_mutate_rejects_bad_shapes(self):
        bad = [
            [],
            [{"campaign_operation": {}}],
            [{"campaign_operation": {"update": {"resource_name": f"customers/{CID}/campaigns/5", "status": "PAUSED"}}}],
            [{"not_an_operation": {"remove": "x"}}],
            [{"a_operation": {}, "b_operation": {}}],
        ]
        for ops in bad:
            with self.assertRaises(ToolError, msg=str(ops)):
                am.mutate(customer_id=CID, operations=ops)

    def test_mutate_changed_operations_invalidate_checksum(self):
        ops = [{"campaign_operation": {
            "update": {"resource_name": f"customers/{CID}/campaigns/5", "status": "PAUSED"},
            "update_mask": "status"}}]
        proposal = json.loads(am.mutate(customer_id=CID, operations=ops))
        ops[0]["campaign_operation"]["update"]["status"] = "ENABLED"
        with self.assertRaises(ToolError):
            am.mutate(customer_id=CID, operations=ops, validate_only=False,
                      checksum=proposal["checksum"])

    # ---- create_search_campaign ----------------------------------------

    def _campaign_kwargs(self, **overrides):
        kwargs = dict(
            customer_id=CID,
            campaign_name="אזעקה לעסק - חדש",
            daily_budget=150,
            ad_group_name="אזעקה לעסק",
            keywords=[{"text": "אזעקה לעסק", "match_type": "EXACT"},
                      {"text": "אזעקה לעסק", "match_type": "PHRASE"}],
            final_url="https://www.team3.co.il/lp2/business-alarm/",
            headlines=["אזעקה לעסק", "התקנה מהירה", "מוקד 24/7"],
            descriptions=["מערכות אזעקה לעסקים עם מוקד", "התקשרו לייעוץ חינם"],
            target_cpa=200,
            negative_keywords=["דרושים"],
        )
        kwargs.update(overrides)
        return kwargs

    def test_create_search_campaign_builds_paused_structure(self):
        self._propose_then_commit(am.create_search_campaign, **self._campaign_kwargs())
        request = self.mock_client.get_service("GoogleAdsService").mutate.call_args.kwargs["request"]
        kinds = [json_format.MessageToDict(type(o).pb(o), preserving_proto_field_name=True)
                 for o in request.mutate_operations]
        keys = [next(iter(k)) for k in kinds]
        self.assertEqual(keys[0], "campaign_budget_operation")
        self.assertEqual(keys[1], "campaign_operation")
        self.assertEqual(keys.count("ad_group_criterion_operation"), 2)
        self.assertEqual(keys[-1], "ad_group_ad_operation")

        campaign = request.mutate_operations[1].campaign_operation.create
        self.assertEqual(campaign.status.name, "PAUSED")
        self.assertEqual(campaign.advertising_channel_type.name, "SEARCH")
        self.assertEqual(campaign.maximize_conversions.target_cpa_micros, 200_000_000)
        self.assertFalse(campaign.network_settings.target_content_network)
        self.assertEqual(campaign.geo_target_type_setting.positive_geo_target_type.name, "PRESENCE")
        self.assertEqual(campaign.campaign_budget, f"customers/{CID}/campaignBudgets/-1")

        budget = request.mutate_operations[0].campaign_budget_operation.create
        self.assertEqual(budget.amount_micros, 150_000_000)

    def test_create_search_campaign_validation(self):
        for overrides in (
            {"headlines": ["a", "b"]},
            {"headlines": ["x" * 31, "b", "c"]},
            {"descriptions": ["only one"]},
            {"final_url": "www.team3.co.il"},
            {"daily_budget": 0},
            {"keywords": []},
            {"path2": "abc"},
        ):
            with self.assertRaises(ToolError, msg=str(overrides)):
                am.create_search_campaign(**self._campaign_kwargs(**overrides))

    # ---- upload_click_conversions --------------------------------------

    def test_upload_click_conversions(self):
        svc = self.mock_client.get_service("ConversionUploadService")
        ok = SimpleNamespace(partial_failure_error=SimpleNamespace(message=""),
                             results=[SimpleNamespace(gclid="abc")])
        svc.upload_click_conversions.return_value = ok
        convs = [{"gclid": "abc", "conversion_action_id": "77",
                  "conversion_date_time": "2026-11-09 14:30:00+02:00",
                  "conversion_value": 1500, "currency_code": "ILS"}]
        _, result = self._propose_then_commit(
            am.upload_click_conversions, customer_id=CID, conversions=convs)
        request = svc.upload_click_conversions.call_args.kwargs["request"]
        self.assertTrue(request.partial_failure)
        self.assertFalse(request.validate_only)
        self.assertEqual(request.conversions[0].conversion_action,
                         f"customers/{CID}/conversionActions/77")
        self.assertIn("Uploaded 1 of 1", result)

    def test_upload_validation_errors_block_proposal(self):
        svc = self.mock_client.get_service("ConversionUploadService")
        svc.upload_click_conversions.return_value = SimpleNamespace(
            partial_failure_error=SimpleNamespace(message="The click is too old"), results=[])
        with self.assertRaises(ToolError):
            am.upload_click_conversions(customer_id=CID, conversions=[
                {"gclid": "abc", "conversion_action_id": "77",
                 "conversion_date_time": "2026-01-01 00:00:00+02:00"}])


class TestAdvancedMounting(unittest.IsolatedAsyncioTestCase):

    @patch("ads_mcp.config.ToolsConfig.load")
    async def test_tools_are_mounted(self, mock_load):
        mock_load.return_value = ToolsConfig({"namespaces": {"management": True}})
        parent = FastMCP("Test Parent")
        initialize_and_mount_tools(parent)
        names = {t.name for t in await parent.list_tools()}
        for expected in ("management_mutate", "management_create_search_campaign",
                         "management_upload_click_conversions",
                         "management_set_campaign_ad_schedule"):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
