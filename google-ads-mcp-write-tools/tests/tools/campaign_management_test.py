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

"""Test cases for the campaign management write tools."""

import json
import unittest
from unittest.mock import MagicMock, patch

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from google.ads.googleads.client import GoogleAdsClient
from google.auth.credentials import AnonymousCredentials

from ads_mcp.config import ToolsConfig
from ads_mcp.coordinator import initialize_and_mount_tools
from ads_mcp.tools import campaign_management as cm

CID = "1234567890"


def _resp(*resource_names: str) -> MagicMock:
    resp = MagicMock()
    items = []
    for rn in resource_names:
        item = MagicMock()
        item.resource_name = rn
        items.append(item)
    resp.results = items
    return resp


class TestCampaignManagement(unittest.TestCase):
    """Propose/confirm behaviour and request construction for each tool."""

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
                svc = MagicMock()
                if name == "GoogleAdsService":
                    svc.search.return_value = []
                self.services[name] = svc
            return self.services[name]

        self.mock_client.get_service.side_effect = get_service
        self.mock_client.get_type.side_effect = self.real_ga_client.get_type
        patcher = patch(
            "ads_mcp.utils.get_googleads_client", return_value=self.mock_client
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _propose_then_commit(self, fn, **kwargs):
        proposal = json.loads(fn(**kwargs))
        self.assertEqual(proposal["status"], "PROPOSED")
        result = fn(**kwargs, validate_only=False, checksum=proposal["checksum"])
        return proposal, result

    # ---- conversion actions -------------------------------------------

    def test_update_conversion_action(self):
        svc = self.mock_client.get_service("ConversionActionService")
        svc.mutate_conversion_actions.return_value = _resp(
            f"customers/{CID}/conversionActions/460688052"
        )
        proposal, result = self._propose_then_commit(
            cm.update_conversion_action,
            customer_id="123-456-7890",
            conversion_action_id="460688052",
            phone_call_duration_seconds=90,
            counting_type="ONE_PER_CLICK",
        )
        fields = {i["field_readable"]: i["value_readable"] for i in proposal["change_items"]}
        self.assertEqual(fields["Phone Call Duration (s)"], "90")
        self.assertEqual(fields["Counting Type"], "ONE_PER_CLICK")
        self.assertIn("Successfully updated 1", result)

        # First call validated only, second committed.
        calls = svc.mutate_conversion_actions.call_args_list
        self.assertEqual(len(calls), 2)
        request = calls[-1].kwargs["request"]
        self.assertFalse(request.validate_only)
        op = request.operations[0]
        self.assertEqual(
            op.update.resource_name, f"customers/{CID}/conversionActions/460688052"
        )
        self.assertEqual(op.update.phone_call_duration_seconds, 90)
        self.assertEqual(op.update.counting_type.name, "ONE_PER_CLICK")
        self.assertCountEqual(
            list(op.update_mask.paths), ["counting_type", "phone_call_duration_seconds"]
        )

    def test_update_conversion_action_requires_a_field(self):
        with self.assertRaises(ToolError):
            cm.update_conversion_action(customer_id=CID, conversion_action_id="1")

    def test_commit_without_checksum_is_rejected(self):
        svc = self.mock_client.get_service("ConversionActionService")
        with self.assertRaises(ToolError):
            cm.update_conversion_action(
                customer_id=CID,
                conversion_action_id="1",
                primary_for_goal=False,
                validate_only=False,
            )
        svc.mutate_conversion_actions.assert_not_called()

    def test_changed_parameters_invalidate_checksum(self):
        svc = self.mock_client.get_service("ConversionActionService")
        proposal = json.loads(
            cm.update_conversion_action(
                customer_id=CID, conversion_action_id="1", phone_call_duration_seconds=90
            )
        )
        with self.assertRaises(ToolError):
            cm.update_conversion_action(
                customer_id=CID,
                conversion_action_id="1",
                phone_call_duration_seconds=10,
                validate_only=False,
                checksum=proposal["checksum"],
            )
        # Only the validation call reached the API.
        self.assertEqual(svc.mutate_conversion_actions.call_count, 1)
        self.assertTrue(
            svc.mutate_conversion_actions.call_args.kwargs["request"].validate_only
        )

    # ---- negatives ------------------------------------------------------

    def test_add_shared_negative_keywords_dedupes_and_strips(self):
        svc = self.mock_client.get_service("SharedCriterionService")
        svc.mutate_shared_criteria.return_value = _resp(
            f"customers/{CID}/sharedCriteria/1~1", f"customers/{CID}/sharedCriteria/1~2"
        )
        proposal, result = self._propose_then_commit(
            cm.add_shared_negative_keywords,
            customer_id=CID,
            shared_set_id="555",
            keywords=['"מוקד מבצר"', "מוקד מבצר", "  g1  ", ""],
        )
        self.assertEqual(
            [i["value_readable"] for i in proposal["change_items"]], ["מוקד מבצר", "g1"]
        )
        request = svc.mutate_shared_criteria.call_args.kwargs["request"]
        self.assertEqual(len(request.operations), 2)
        crit = request.operations[0].create
        self.assertEqual(crit.shared_set, f"customers/{CID}/sharedSets/555")
        self.assertEqual(crit.keyword.match_type.name, "PHRASE")
        self.assertIn("Successfully added 2", result)

    def test_add_campaign_negative_keywords(self):
        svc = self.mock_client.get_service("CampaignCriterionService")
        svc.mutate_campaign_criteria.return_value = _resp(
            f"customers/{CID}/campaignCriteria/9~1"
        )
        self._propose_then_commit(
            cm.add_campaign_negative_keywords,
            customer_id=CID,
            campaign_id="9",
            keywords=["טלפון"],
            match_type="EXACT",
        )
        crit = svc.mutate_campaign_criteria.call_args.kwargs["request"].operations[0].create
        self.assertTrue(crit.negative)
        self.assertEqual(crit.campaign, f"customers/{CID}/campaigns/9")
        self.assertEqual(crit.keyword.match_type.name, "EXACT")

    def test_keyword_validation(self):
        with self.assertRaises(ToolError):
            cm.add_campaign_negative_keywords(
                customer_id=CID, campaign_id="9", keywords=["x" * 81]
            )
        with self.assertRaises(ToolError):
            cm.add_campaign_negative_keywords(
                customer_id=CID, campaign_id="9", keywords=[" ".join(["a"] * 11)]
            )
        with self.assertRaises(ToolError):
            cm.add_campaign_negative_keywords(customer_id=CID, campaign_id="9", keywords=[])

    # ---- keywords -------------------------------------------------------

    def test_add_keywords(self):
        svc = self.mock_client.get_service("AdGroupCriterionService")
        svc.mutate_ad_group_criteria.return_value = _resp(
            f"customers/{CID}/adGroupCriteria/77~1"
        )
        self._propose_then_commit(
            cm.add_keywords,
            customer_id=CID,
            ad_group_id="77",
            keywords=["מוקד אבטחה"],
            match_type="EXACT",
        )
        crit = svc.mutate_ad_group_criteria.call_args.kwargs["request"].operations[0].create
        self.assertEqual(crit.ad_group, f"customers/{CID}/adGroups/77")
        self.assertEqual(crit.status.name, "ENABLED")
        self.assertEqual(crit.keyword.text, "מוקד אבטחה")

    def test_update_keyword_status_pause(self):
        svc = self.mock_client.get_service("AdGroupCriterionService")
        svc.mutate_ad_group_criteria.return_value = _resp(
            f"customers/{CID}/adGroupCriteria/77~88"
        )
        self._propose_then_commit(
            cm.update_keyword_status,
            customer_id=CID,
            keyword_ids=["77~88"],
            status="PAUSED",
        )
        op = svc.mutate_ad_group_criteria.call_args.kwargs["request"].operations[0]
        self.assertEqual(op.update.resource_name, f"customers/{CID}/adGroupCriteria/77~88")
        self.assertEqual(op.update.status.name, "PAUSED")
        self.assertEqual(list(op.update_mask.paths), ["status"])

    def test_update_keyword_status_bad_id(self):
        with self.assertRaises(ToolError):
            cm.update_keyword_status(customer_id=CID, keyword_ids=["88"], status="PAUSED")

    # ---- campaigns ------------------------------------------------------

    def test_update_campaign_status(self):
        svc = self.mock_client.get_service("CampaignService")
        svc.mutate_campaigns.return_value = _resp(f"customers/{CID}/campaigns/5")
        self._propose_then_commit(
            cm.update_campaign_status, customer_id=CID, campaign_id="5", status="PAUSED"
        )
        op = svc.mutate_campaigns.call_args.kwargs["request"].operations[0]
        self.assertEqual(op.update.status.name, "PAUSED")

    def test_update_campaign_status_rejects_removed(self):
        with self.assertRaises(ToolError):
            cm.update_campaign_status(customer_id=CID, campaign_id="5", status="REMOVED")

    def test_update_campaign_budget(self):
        svc = self.mock_client.get_service("CampaignBudgetService")
        svc.mutate_campaign_budgets.return_value = _resp(
            f"customers/{CID}/campaignBudgets/3"
        )
        proposal, _ = self._propose_then_commit(
            cm.update_campaign_budget,
            customer_id=CID,
            campaign_budget_id="3",
            daily_amount=150.005,
        )
        op = svc.mutate_campaign_budgets.call_args.kwargs["request"].operations[0]
        self.assertEqual(op.update.amount_micros % 10_000, 0)
        self.assertEqual(op.update.amount_micros, 150_000_000)
        self.assertEqual(proposal["change_items"][0]["value_readable"], "150.00")

    def test_update_campaign_budget_rejects_zero(self):
        with self.assertRaises(ToolError):
            cm.update_campaign_budget(customer_id=CID, campaign_budget_id="3", daily_amount=0)


class TestManagementMounting(unittest.IsolatedAsyncioTestCase):
    """The management namespace mounts with the expected prefixed names."""

    @patch("ads_mcp.config.ToolsConfig.load")
    async def test_tools_are_mounted(self, mock_load):
        mock_load.return_value = ToolsConfig({"namespaces": {"management": True}})
        parent = FastMCP("Test Parent")
        initialize_and_mount_tools(parent)
        names = {t.name for t in await parent.list_tools()}
        for expected in (
            "management_update_conversion_action",
            "management_add_shared_negative_keywords",
            "management_add_campaign_negative_keywords",
            "management_add_keywords",
            "management_update_keyword_status",
            "management_update_campaign_status",
            "management_update_campaign_budget",
        ):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
