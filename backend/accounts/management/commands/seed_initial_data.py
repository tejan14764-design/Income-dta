"""
Management command: seed_initial_data
Creates default permissions, roles, school and admin user.
Run: python manage.py seed_initial_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config

User = get_user_model()

DEFAULT_PERMISSIONS = [
    # Students
    ("students.register", "Register Students", "students"),
    ("students.edit", "Edit Student Information", "students"),
    ("students.delete", "Delete Students", "students"),
    ("students.view", "View Students", "students"),
    ("students.view_confidential", "View Confidential Student Info", "students"),
    # Finance
    ("finance.manage", "Manage Fee Configuration", "finance"),
    ("finance.view", "View Financial Records", "finance"),
    ("finance.adjust", "Apply Discounts and Waivers", "finance"),
    # Payments
    ("payments.record", "Record Payments", "payments"),
    ("payments.verify", "Verify Payments", "payments"),
    ("payments.reverse", "Reverse Payments", "payments"),
    ("payments.view", "View Payments", "payments"),
    # Receipts
    ("receipts.generate", "Generate Receipts", "receipts"),
    ("receipts.print", "Print Receipts", "receipts"),
    # Reports
    ("reports.view", "View Financial Reports", "reports"),
    ("reports.export", "Export Reports", "reports"),
    # Users
    ("users.manage", "Manage Users and Roles", "users"),
    # Audit
    ("audit.view", "View Audit Logs", "audit"),
    # Academic
    ("academics.manage", "Manage Classes and Academic Years", "academics"),
]

DEFAULT_ROLES = {
    "super_admin": {
        "name": "Super Administrator",
        "description": "Full system access",
        "permissions": [p[0] for p in DEFAULT_PERMISSIONS],
    },
    "school_admin": {
        "name": "School Administrator",
        "description": "Manages all school operations",
        "permissions": [p[0] for p in DEFAULT_PERMISSIONS],
    },
    "registrar": {
        "name": "Registrar",
        "description": "Manages student registration and academic records",
        "permissions": [
            "students.register", "students.edit", "students.view",
            "academics.manage", "reports.view",
        ],
    },
    "bursar": {
        "name": "Bursar / Cashier",
        "description": "Records payments and generates receipts",
        "permissions": [
            "payments.record", "payments.view",
            "receipts.generate", "receipts.print",
            "students.view", "finance.view",
        ],
    },
    "financial_officer": {
        "name": "Financial Officer",
        "description": "Verifies payments, manages fee structures, generates reports",
        "permissions": [
            "payments.verify", "payments.reverse", "payments.view",
            "finance.manage", "finance.view", "finance.adjust",
            "receipts.generate", "receipts.print",
            "reports.view", "reports.export",
            "students.view",
        ],
    },
    "auditor": {
        "name": "Auditor",
        "description": "Read-only access to financial and audit records",
        "permissions": [
            "payments.view", "finance.view",
            "reports.view", "reports.export",
            "audit.view", "students.view",
        ],
    },
}


class Command(BaseCommand):
    help = "Seeds initial permissions, roles, school and admin user."

    def handle(self, *args, **options):
        from accounts.models import Permission, Role, RolePermission, SchoolMembership
        from schools.models import School, SchoolSettings

        self.stdout.write("Seeding permissions...")
        perm_map = {}
        for codename, name, module in DEFAULT_PERMISSIONS:
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={"name": name, "module": module},
            )
            perm_map[codename] = perm
            if created:
                self.stdout.write(f"  + Permission: {codename}")

        self.stdout.write("Creating default school...")
        school_name = config("DEFAULT_SCHOOL_NAME", default="Demo School")
        school_email = config("DEFAULT_SCHOOL_EMAIL", default="admin@demoschool.edu")
        school, _ = School.objects.get_or_create(
            code="DEMO",
            defaults={"name": school_name, "email": school_email},
        )
        SchoolSettings.objects.get_or_create(school=school)
        self.stdout.write(f"  School: {school.name}")

        self.stdout.write("Creating default roles...")
        for slug, role_data in DEFAULT_ROLES.items():
            role, created = Role.objects.get_or_create(
                school=school,
                slug=slug,
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "is_system_role": True,
                },
            )
            if created:
                self.stdout.write(f"  + Role: {role.name}")
            # Assign permissions
            for codename in role_data["permissions"]:
                if codename in perm_map:
                    RolePermission.objects.get_or_create(role=role, permission=perm_map[codename])

        self.stdout.write("Creating default admin user...")
        admin_username = config("DEFAULT_ADMIN_USERNAME", default="admin")
        admin_password = config("DEFAULT_ADMIN_PASSWORD", default="Admin@12345!")
        admin_email = config("DEFAULT_SCHOOL_EMAIL", default="admin@demoschool.edu")

        user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                "email": admin_email,
                "first_name": "System",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(admin_password)
            user.save()
            self.stdout.write(f"  + Admin user created: {admin_username}")
        else:
            self.stdout.write(f"  Admin user already exists: {admin_username}")

        # Assign admin to school with super_admin role
        super_admin_role = Role.objects.get(school=school, slug="super_admin")
        SchoolMembership.objects.get_or_create(
            user=user,
            school=school,
            defaults={"role": super_admin_role},
        )

        self.stdout.write(self.style.SUCCESS("\nInitial data seeded successfully!"))
        self.stdout.write(f"  School: {school.name}")
        self.stdout.write(f"  Admin username: {admin_username}")
        self.stdout.write(f"  Admin password: {admin_password}")
        self.stdout.write("\nIMPORTANT: Change the default admin password immediately!")
