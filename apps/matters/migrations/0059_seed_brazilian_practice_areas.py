"""Seed initial Brazilian practice areas without altering historical references."""

from django.db import migrations


BRAZILIAN_PRACTICE_AREAS = (
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
    "Outras áreas",
)


def seed_brazilian_areas(apps, schema_editor):
    PracticeArea = apps.get_model("matters", "PracticeArea")
    alias = schema_editor.connection.alias
    for name in BRAZILIAN_PRACTICE_AREAS:
        # Do not reactivate administrator-disabled areas or change old rows.
        PracticeArea.objects.using(alias).get_or_create(
            name=name, defaults={"is_active": True}
        )


class Migration(migrations.Migration):
    dependencies = [("matters", "0058_proceeding_brazilian_fields")]
    operations = [
        migrations.RunPython(seed_brazilian_areas, migrations.RunPython.noop),
    ]
