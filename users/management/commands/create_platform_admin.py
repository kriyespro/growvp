"""Create or reset a Mission Control super admin (email login).

Usage:
  python manage.py create_platform_admin --email admin@example.com --password 'YourStrongPass'
  docker compose exec web python manage.py create_platform_admin \\
      --email admin@example.com --password 'YourStrongPass'
"""

from django.core.management.base import BaseCommand, CommandError

from users.models import User


class Command(BaseCommand):
    help = "Create or reset a staff super_admin that can sign in with email."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Login email")
        parser.add_argument("--password", required=True, help="Login password")
        parser.add_argument(
            "--username",
            default="",
            help="Optional username (defaults to email)",
        )

    def handle(self, *args, **options):
        email = (options["email"] or "").strip().lower()
        password = options["password"] or ""
        username = (options["username"] or "").strip() or email

        if not email or "@" not in email:
            raise CommandError("Provide a valid --email")
        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters")

        user = User.objects.filter(email__iexact=email).first()
        created = False
        if user is None:
            # Prefer matching username=email so /auth/login/ works either way.
            if User.objects.filter(username=username).exists() and username != email:
                username = email
            if User.objects.filter(username=username).exists():
                raise CommandError(
                    f"Username '{username}' already taken by another account."
                )
            user = User(
                username=username,
                email=email,
                is_staff=True,
                is_superuser=True,
                platform_role="super_admin",
                is_active=True,
            )
            user.set_password(password)
            user.save()
            created = True
        else:
            user.username = user.username or email
            # Keep username aligned with email for login compatibility.
            if user.username != email and not User.objects.filter(
                username=email
            ).exclude(pk=user.pk).exists():
                user.username = email
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.platform_role = "super_admin"
            user.is_active = True
            user.set_password(password)
            user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} super admin {user.email} "
                f"(username={user.username}, role={user.platform_role}). "
                f"Sign in at /auth/login/ then open /admin/"
            )
        )
