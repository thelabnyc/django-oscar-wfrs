from decimal import Decimal
from django.contrib.auth.models import Group
from django.utils import timezone
from oscar.core.loading import get_model, get_class
from oscar.test import factories
from wellsfargo.tests.base import BaseTest
from wellsfargo.core.constants import TRANS_TYPE_AUTH, TRANS_APPROVED
from wellsfargo.models import (
    APIMerchantNum,
    TransferMetadata,
    FinancingPlan,
    FinancingPlanBenefit,
)
import datetime
import uuid

Range = get_model("offer", "Range")
Condition = get_model("offer", "Condition")
Benefit = get_model("offer", "Benefit")
ConditionalOffer = get_model("offer", "ConditionalOffer")
OfferGroup = get_model("offer", "OfferGroup")

Applicator = get_class("offer.applicator", "Applicator")


class APIMerchantNumTest(BaseTest):
    def test_selection_no_user(self):
        APIMerchantNum.objects.create(merchant_num="0000", user_group=None, priority=1)
        APIMerchantNum.objects.create(merchant_num="1111", user_group=None, priority=2)
        self.assertEqual(APIMerchantNum.get_for_user().merchant_num, "1111")

    def test_selection_user_no_group(self):
        APIMerchantNum.objects.create(merchant_num="0000", user_group=None, priority=1)
        APIMerchantNum.objects.create(merchant_num="1111", user_group=None, priority=2)
        self.assertEqual(APIMerchantNum.get_for_user(self.joe).merchant_num, "1111")

    def test_selection_user_group(self):
        group = Group.objects.create(name="Special Group")
        APIMerchantNum.objects.create(merchant_num="0000", user_group=None, priority=1)
        APIMerchantNum.objects.create(merchant_num="1111", user_group=group, priority=2)
        self.assertEqual(APIMerchantNum.get_for_user(self.joe).merchant_num, "0000")
        self.joe.groups.add(group)
        self.assertEqual(APIMerchantNum.get_for_user(self.joe).merchant_num, "1111")
        self.joe.groups.remove(group)
        self.assertEqual(APIMerchantNum.get_for_user(self.joe).merchant_num, "0000")


class TransferMetadataTest(BaseTest):
    def test_account_number(self):
        transfer = TransferMetadata()
        transfer.user = self.joe
        transfer.merchant_name = self.credentials.name
        transfer.merchant_num = self.credentials.merchant_num
        transfer.merchant_reference = uuid.uuid1()
        transfer.amount = Decimal("10.00")
        transfer.type_code = TRANS_TYPE_AUTH
        transfer.ticket_number = "123"
        transfer.status = TRANS_APPROVED
        transfer.message = "message"
        transfer.disclosure = "disclosure"
        transfer.save()

        # No account number is set
        transfer = TransferMetadata.objects.get(pk=transfer.pk)
        self.assertEqual(transfer.last4_account_number, "")
        self.assertEqual(transfer.masked_account_number, "xxxxxxxxxxxxxxxx")
        self.assertEqual(transfer.account_number, "xxxxxxxxxxxxxxxx")

        # Set an account number
        transfer.account_number = "9999999999999991"
        transfer.save()

        # Retrieve account number via decryption
        transfer = TransferMetadata.objects.get(pk=transfer.pk)
        self.assertEqual(transfer.last4_account_number, "9991")
        self.assertEqual(transfer.masked_account_number, "xxxxxxxxxxxx9991")
        self.assertEqual(transfer.account_number, "9999999999999991")

        # Purge encrypted copy of account number, leaving on the last 4 digits around
        transfer.purge_encrypted_account_number()

        # Make sure only the last 4 digits still exist
        transfer = TransferMetadata.objects.get(pk=transfer.pk)
        self.assertEqual(transfer.last4_account_number, "9991")
        self.assertEqual(transfer.masked_account_number, "xxxxxxxxxxxx9991")
        self.assertEqual(transfer.account_number, "xxxxxxxxxxxx9991")


class FinancingPlanBenefitTest(BaseTest):
    def test_apply_financing_offer(self):
        # Make a basket with a single 1-qty line
        basket = self._create_basket()

        # Make a financing offer to apply to our basket
        offer = self._create_financing_offer()

        # Basket should be devoid of discounts and offers
        self.assertEqual(basket.num_items_without_discount, 1)
        self.assertEqual(basket.offer_applications.applications, {})

        # Apply our financing offer
        Applicator().apply_offers(basket, [offer])

        # Financing shouldn't be registered as a discount
        self.assertEqual(basket.num_items_without_discount, 0)

        # Financing should show up as an offer application
        self.assertTrue(offer.pk in basket.offer_applications.applications)

        # Application details should be correct
        result = basket.offer_applications.applications[offer.pk]
        self.assertEqual(result["name"], "Financing")
        self.assertEqual(result["description"], "Financing is available for your order")
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["offer"], offer)
        self.assertEqual(
            result["result"].description, "Financing is available for your order"
        )

    def test_apply_financing_offer_then_discount_offer_same_group(self):
        # Make a basket with a single 1-qty line
        basket = self._create_basket()

        # Make a financing offer to apply to our basket
        offer_financing = self._create_financing_offer(priority=2)

        # Make a percentage discount offer to apply to the basket
        offer_discount = self._create_offer("10% Off", priority=1)

        # Basket should be devoid of discounts and offers
        self.assertEqual(basket.num_items_without_discount, 1)
        self.assertEqual(basket.offer_applications.applications, {})

        # Apply our financing offer
        Applicator().apply_offers(basket, [offer_financing, offer_discount])

        # Line should be consumed by the financing offer
        self.assertEqual(basket.num_items_without_discount, 0)

        # The financing offer should show as being applied, the discount should not be applied
        self.assertIn(offer_financing.pk, basket.offer_applications.applications)
        self.assertNotIn(offer_discount.pk, basket.offer_applications.applications)

        # Financing application details should be correct
        result = basket.offer_applications.applications[offer_financing.pk]
        self.assertEqual(result["name"], "Financing")
        self.assertEqual(result["description"], "Financing is available for your order")
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["offer"], offer_financing)
        self.assertEqual(
            result["result"].description, "Financing is available for your order"
        )

    def test_apply_financing_offer_then_discount_offer_different_groups(self):
        # Make a basket with a single 1-qty line
        basket = self._create_basket()

        # Make a financing offer to apply to our basket
        offer_financing = self._create_financing_offer(
            priority=1, group_name="Wells Fargo", group_priority=2
        )

        # Make a percentage discount offer to apply to the basket
        offer_discount = self._create_offer(
            "10% Off", priority=1, group_name="Default", group_priority=1
        )

        # Basket should be devoid of discounts and offers
        self.assertEqual(basket.num_items_without_discount, 1)
        self.assertEqual(basket.offer_applications.applications, {})

        # Apply our financing offer
        Applicator().apply_offers(basket, [offer_financing, offer_discount])

        # Line should be consumed by the offers
        self.assertEqual(basket.num_items_without_discount, 0)

        # Both the discount and financing offers should show as being applied
        self.assertTrue(offer_financing.pk in basket.offer_applications.applications)
        self.assertTrue(offer_discount.pk in basket.offer_applications.applications)

        # Financing application details should be correct
        result = basket.offer_applications.applications[offer_financing.pk]
        self.assertEqual(result["name"], "Financing")
        self.assertEqual(result["description"], "Financing is available for your order")
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["offer"], offer_financing)
        self.assertEqual(
            result["result"].description, "Financing is available for your order"
        )

        # Discount application details should be correct
        result = basket.offer_applications.applications[offer_discount.pk]
        self.assertEqual(result["name"], "10% Off")
        self.assertEqual(result["description"], None)
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("1.00"))
        self.assertEqual(result["offer"], offer_discount)
        self.assertEqual(result["result"].description, None)

    def test_apply_discount_offer_then_financing_offer_same_group(self):
        # Make a basket with a single 1-qty line
        basket = self._create_basket()

        # Make a percentage discount offer to apply to the basket
        offer_discount = self._create_offer("10% Off", priority=2)

        # Make a financing offer to apply to our basket
        offer_financing = self._create_financing_offer(priority=1)

        # Basket should be devoid of discounts and offers
        self.assertEqual(basket.num_items_without_discount, 1)
        self.assertEqual(basket.offer_applications.applications, {})

        # Apply our financing offer
        Applicator().apply_offers(basket, [offer_discount, offer_financing])

        # Line should be consumed by the discount
        self.assertEqual(basket.num_items_without_discount, 0)

        # The discount offer should show as being applied. The financing offer should not be.
        self.assertNotIn(offer_financing.pk, basket.offer_applications.applications)
        self.assertIn(offer_discount.pk, basket.offer_applications.applications)

        # Discount application details should be correct
        result = basket.offer_applications.applications[offer_discount.pk]
        self.assertEqual(result["name"], "10% Off")
        self.assertEqual(result["description"], None)
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("1.00"))
        self.assertEqual(result["offer"], offer_discount)
        self.assertEqual(result["result"].description, None)

    def test_apply_discount_offer_then_financing_offer_different_groups(self):
        # Make a basket with a single 1-qty line
        basket = self._create_basket()

        # Make a percentage discount offer to apply to the basket
        offer_discount = self._create_offer(
            "10% Off", priority=1, group_name="Default", group_priority=2
        )

        # Make a financing offer to apply to our basket
        offer_financing = self._create_financing_offer(
            priority=1, group_name="Wells Fargo", group_priority=1
        )

        # Basket should be devoid of discounts and offers
        self.assertEqual(basket.num_items_without_discount, 1)
        self.assertEqual(basket.offer_applications.applications, {})

        # Apply our financing offer
        Applicator().apply_offers(basket, [offer_discount, offer_financing])

        # Line should be consumed by the discount
        self.assertEqual(basket.num_items_without_discount, 0)

        # Both the discount and financing offers should show as being applied
        self.assertIn(offer_financing.pk, basket.offer_applications.applications)
        self.assertIn(offer_discount.pk, basket.offer_applications.applications)

        # Financing application details should be correct
        result = basket.offer_applications.applications[offer_financing.pk]
        self.assertEqual(result["name"], "Financing")
        self.assertEqual(result["description"], "Financing is available for your order")
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["offer"], offer_financing)
        self.assertEqual(
            result["result"].description, "Financing is available for your order"
        )

        # Discount application details should be correct
        result = basket.offer_applications.applications[offer_discount.pk]
        self.assertEqual(result["name"], "10% Off")
        self.assertEqual(result["description"], None)
        self.assertEqual(result["voucher"], None)
        self.assertEqual(result["freq"], 1)
        self.assertEqual(result["discount"], Decimal("1.00"))
        self.assertEqual(result["offer"], offer_discount)
        self.assertEqual(result["result"].description, None)

    def _create_product(self):
        product = factories.create_product(
            title="My Product", product_class="My Product Class"
        )
        record = factories.create_stockrecord(
            currency="USD", product=product, num_in_stock=10, price=Decimal("10.00")
        )
        factories.create_purchase_info(record)
        return product

    def _create_basket(self):
        basket = factories.create_basket(empty=True)
        product = self._create_product()
        basket.add_product(product)
        return basket

    def _create_offer(
        self, name, benefit=None, priority=0, group_name="Default", group_priority=0
    ):
        rng, _ = Range.objects.get_or_create(
            name="All products range", includes_all_products=True
        )

        condition, _ = Condition.objects.get_or_create(
            proxy_class="oscarbluelight.offer.conditions.BluelightCountCondition",
            range=rng,
            value=1,
        )

        if not benefit:
            benefit = Benefit.objects.create(
                proxy_class="oscarbluelight.offer.benefits.BluelightPercentageDiscountBenefit",
                range=rng,
                value=Decimal("10.00"),
            )

        now = timezone.now()
        start = now - datetime.timedelta(days=1)
        end = now + datetime.timedelta(days=30)

        group, _ = OfferGroup.objects.get_or_create(
            name=group_name, priority=group_priority
        )

        offer = ConditionalOffer.objects.create(
            name=name,
            short_name=name,
            offer_group=group,
            start_datetime=start,
            end_datetime=end,
            status=ConditionalOffer.OPEN,
            offer_type="Site",
            condition=condition,
            benefit=benefit,
            max_basket_applications=None,
            priority=priority,
        )
        return offer

    def _create_financing_offer(
        self, priority=0, group_name="Default", group_priority=0
    ):
        plan = FinancingPlan.objects.create(plan_number=9999)
        benefit = FinancingPlanBenefit.objects.create(group_name="Default Financing")
        benefit.plans.set([plan])
        benefit.save()
        return self._create_offer(
            "Financing", benefit, priority, group_name, group_priority
        )
