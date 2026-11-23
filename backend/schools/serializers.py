from rest_framework import serializers
from .models import School, SchoolSettings, SchoolBranch


class SchoolSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSettings
        fields = [
            "id", "currency_code", "currency_symbol", "receipt_footer",
            "receipt_printer_name", "receipt_copies", "enable_sms_notifications",
            "max_payment_evidence_size_mb",
        ]
        read_only_fields = ["id"]


class SchoolSerializer(serializers.ModelSerializer):
    settings = SchoolSettingsSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = [
            "id", "name", "code", "address", "phone_number", "email",
            "website", "logo", "logo_url", "is_active", "settings",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "logo_url"]

    def get_logo_url(self, obj):
        request = self.context.get("request")
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None


class SchoolBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolBranch
        fields = ["id", "school", "name", "address", "phone_number", "is_active"]
        read_only_fields = ["id"]
