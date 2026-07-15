from django import forms

from core.plans import (
    can_add_product,
    can_add_service,
    plan_allows_products,
    plan_product_limit,
    plan_service_limit,
)
from .models import Service, ServiceCategory, Product


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "category",
            "name",
            "description",
            "image_url",
            "image",
            "duration_mins",
            "price",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)
        if self.business:
            self.fields["category"].queryset = ServiceCategory.objects.filter(
                business=self.business
            )

    def clean_duration_mins(self):
        duration = self.cleaned_data["duration_mins"]
        if duration <= 0:
            raise forms.ValidationError("Duration must be greater than 0 minutes.")
        return duration

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_image_url(self):
        return self.cleaned_data.get("image_url", "").strip()

    def clean(self):
        cleaned = super().clean()
        if not self.business:
            return cleaned
        creating = self.instance.pk is None
        becoming_active = cleaned.get("is_active", True)
        hitting_limit = creating and becoming_active and not can_add_service(self.business)
        reactivating = (
            not creating
            and becoming_active
            and not self.instance.is_active
            and not can_add_service(self.business)
        )
        if hitting_limit or reactivating:
            limit = plan_service_limit(self.business.listing_plan)
            raise forms.ValidationError(
                f"Your {self.business.plan_label} allows only {limit} active services. "
                "Upgrade to Pro or Premium to add more."
            )
        return cleaned


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ["name"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "image_url",
            "image",
            "buy_url",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop("business", None)
        super().__init__(*args, **kwargs)

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean(self):
        cleaned = super().clean()
        if not self.business:
            return cleaned
        if not plan_allows_products(self.business.listing_plan):
            raise forms.ValidationError(
                "Product listings start on Pro. Upgrade your listing plan to sell products."
            )
        creating = self.instance.pk is None
        becoming_active = cleaned.get("is_active", True)
        if creating and becoming_active and not can_add_product(self.business):
            limit = plan_product_limit(self.business.listing_plan)
            raise forms.ValidationError(
                f"Your {self.business.plan_label} allows only {limit} active products. "
                "Upgrade to Premium for unlimited products."
            )
        if (
            not creating
            and becoming_active
            and not self.instance.is_active
            and not can_add_product(self.business)
        ):
            limit = plan_product_limit(self.business.listing_plan)
            raise forms.ValidationError(
                f"Your {self.business.plan_label} allows only {limit} active products. "
                "Upgrade to add more."
            )
        return cleaned
