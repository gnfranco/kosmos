"""Populate Brazilian practice areas without erasing legacy legal classifications.

This management command deliberately does not run in a migration: disabling
historical seed values is an opt-in operational change for the Brazilian Lex
instance, not a global policy for all Kosmos deployments.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.intakes.models import Intake
from apps.matters.models import Matter, PracticeArea

BR_AREAS = (
    "Direito Trabalhista",
    "Direito Previdenciário",
    "Direito Cível",
    "Direito de Família e Sucessões",
    "Direito do Consumidor",
    "Direito Empresarial",
    "Direito Administrativo",
    "Direito Tributário",
    "Direito Imobiliário",
    "Direito Criminal",
    "Direito Ambiental",
    "Direito Digital",
    "Outras áreas",
)

# Seeds from the existing migrations 0023 and 0048. No other custom areas are
# considered for deactivation. Used rows are never modified or deleted.
LEGACY_SEEDED_AREAS = (
    "General",
    "Interpleader",
    "Construction",
    "Boundary",
    "LLT-L",
    "LLT-T",
    "QT",
    "Title",
    "HOA",
    "Fraud",
    "Easement",
    "Purchase / Sale",
    "Commercial",
)


class Command(BaseCommand):
    help = (
        "Create Brazilian practice-area names. Optionally deactivate unused "
        "old US seed values for a Portuguese-Brazilian deployment."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--deactivate-unused-legacy", action="store_true",
            help="Deactivate only historical US seeds with no Matter or Intake.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Simulate the changes with the database transaction rolled back.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.LANGUAGE_CODE.lower().startswith("pt-br"):
            raise CommandError(
                "Brazilian practice-area setup requires LANGUAGE_CODE=pt-br."
            )

        created = 0
        for name in BR_AREAS:
            if not PracticeArea.objects.filter(name=name).exists():
                PracticeArea.objects.create(name=name, is_active=True)
                created += 1

        deactivated = 0
        protected = 0
        if options["deactivate_unused_legacy"]:
            areas = PracticeArea.objects.filter(
                name__in=LEGACY_SEEDED_AREAS, is_active=True,
            ).order_by("name", "pk")
            for area in areas:
                if (
                    Matter.objects.filter(practice_area=area).exists()
                    or Intake.objects.filter(practice_area=area).exists()
                ):
                    protected += 1
                    continue
                area.is_active = False
                area.save(update_fields=["is_active"])
                deactivated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        self.stdout.write(
            f"{'DRY RUN' if options['dry_run'] else 'APPLIED'}: "
            f"Brazilian areas created={created}; "
            f"unused US seeds deactivated={deactivated}; "
            f"referenced legacy areas preserved={protected}."
        )
