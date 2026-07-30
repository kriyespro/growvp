from django import forms

from users.models import Business, User


class RegistrationForm(forms.Form):
    business_name = forms.CharField(max_length=255, required=True, label="Business Name")
    industry_type = forms.ChoiceField(
        choices=Business.INDUSTRY_CHOICES, required=True, label="Industry Type"
    )
    public_phone = forms.CharField(max_length=20, required=True, label="Business Phone")
    email = forms.EmailField(required=True, label="Email Address")
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Password",
        min_length=8,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Confirm Password",
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_public_phone(self):
        phone = (self.cleaned_data.get("public_phone") or "").strip()
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError(
                "Enter a valid phone number with at least 10 digits."
            )
        return phone

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password and confirm and password != confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned


class SimpleAccountForm(forms.Form):
    """Partner or client registration."""

    email = forms.EmailField(required=True, label="Email Address")
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Password",
        min_length=8,
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Confirm Password",
    )
    phone = forms.CharField(max_length=20, required=False, label="Phone")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password and confirm and password != confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned


class PartnerListingForm(forms.Form):
    name = forms.CharField(max_length=255, required=True, label="Business name")
    industry_type = forms.ChoiceField(
        choices=Business.INDUSTRY_CHOICES, required=True, label="Category"
    )
    public_phone = forms.CharField(max_length=20, required=False, label="Phone")


class BusinessLandingForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            "name",
            "industry_type",
            "hero_title",
            "hero_subtitle",
            "hero_image_url",
            "public_phone",
            "public_email",
            "public_address",
            "website_url",
            "map_embed_url",
            "testimonial_quote",
            "testimonial_author",
        ]

    def clean_public_phone(self):
        phone = (self.cleaned_data.get("public_phone") or "").strip()
        if not phone:
            raise forms.ValidationError(
                "Phone is required so customers can contact you."
            )
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError(
                "Enter a valid phone number with at least 10 digits."
            )
        return phone

    def clean_public_address(self):
        address = (self.cleaned_data.get("public_address") or "").strip()
        if not address:
            raise forms.ValidationError(
                "Address is required so customers can find you."
            )
        return address


class ListingPlanForm(forms.Form):
    listing_plan = forms.ChoiceField(
        choices=Business.PLAN_CHOICES,
        widget=forms.RadioSelect,
    )


class AssignPartnerForm(forms.Form):
    partner_id = forms.IntegerField()
    business_id = forms.IntegerField()


class ListingImportForm(forms.Form):
    """CSV / Excel upload or Google Sheets URL."""

    file = forms.FileField(
        required=False,
        label="CSV or Excel file",
        help_text="Accepts .csv, .xlsx",
    )
    google_sheet_url = forms.CharField(
        required=False,
        label="Google Sheet URL",
        widget=forms.URLInput(
            attrs={"placeholder": "https://docs.google.com/spreadsheets/d/…"}
        ),
    )
    partner_id = forms.IntegerField(
        required=False,
        label="Assign created listings to partner (optional)",
    )

    def clean(self):
        cleaned = super().clean()
        uploaded = cleaned.get("file")
        sheet_url = (cleaned.get("google_sheet_url") or "").strip()
        cleaned["google_sheet_url"] = sheet_url
        has_file = bool(uploaded and getattr(uploaded, "name", None))
        if not has_file and not sheet_url:
            raise forms.ValidationError(
                "Upload a CSV/Excel file or paste a Google Sheet URL."
            )
        if has_file and sheet_url:
            raise forms.ValidationError(
                "Use either a file upload or a Google Sheet URL, not both."
            )
        if has_file:
            name = uploaded.name.lower()
            if not name.endswith((".csv", ".tsv", ".xlsx", ".xlsm", ".txt")):
                raise forms.ValidationError(
                    "Unsupported file type. Use .csv or .xlsx."
                )
            if uploaded.size and uploaded.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File too large (max 5 MB).")
        partner_id = cleaned.get("partner_id")
        if partner_id:
            partner = User.objects.filter(
                pk=partner_id, platform_role="marketing_partner"
            ).first()
            if partner is None:
                raise forms.ValidationError("Selected partner was not found.")
            cleaned["partner"] = partner
        else:
            cleaned["partner"] = None
        return cleaned


class ControlBusinessEditForm(forms.ModelForm):
    """Admin edit for partner listings — includes plan."""

    class Meta:
        model = Business
        fields = [
            "name",
            "industry_type",
            "hero_title",
            "hero_subtitle",
            "hero_image_url",
            "public_phone",
            "public_email",
            "public_address",
            "website_url",
            "map_embed_url",
            "testimonial_quote",
            "testimonial_author",
            "listing_plan",
            "slug",
        ]

    def clean_public_phone(self):
        phone = (self.cleaned_data.get("public_phone") or "").strip()
        if phone:
            digits = "".join(ch for ch in phone if ch.isdigit())
            if len(digits) < 10:
                raise forms.ValidationError(
                    "Enter a valid phone number with at least 10 digits."
                )
        return phone
