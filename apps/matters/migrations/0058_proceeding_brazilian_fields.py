# Brazilian process metadata: additive, no backfill or currency conversion.
# See Resolução CNJ 65/2008 for the number check-digit implementation.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matters", "0057_remove_matter_drive_folder"),
    ]

    operations = [
        migrations.AlterField(
            model_name="proceeding",
            name="case_number",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="historicalproceeding",
            name="case_number",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ] + [
        migrations.AddField(
            model_name=target,
            name="numbering_scheme",
            field=models.CharField(
                choices=[("OTHER", "Other / legacy number"), ("CNJ", "CNJ (Brazil)")],
                default="OTHER",
                max_length=8,
            ),
        )
        for target in ("proceeding", "historicalproceeding")
    ] + [
        migrations.AddField(
            model_name=target,
            name=field,
            field=models.CharField(blank=True, max_length=160),
        )
        for field in ("case_class", "court_division")
        for target in ("proceeding", "historicalproceeding")
    ] + [
        migrations.AddField(
            model_name=target,
            name=field,
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=15, null=True
            ),
        )
        for field in ("claim_amount_brl", "claim_updated_brl")
        for target in ("proceeding", "historicalproceeding")
    ] + [
        migrations.AddField(
            model_name=target,
            name="date_final_judgment",
            field=models.DateField(blank=True, null=True),
        )
        for target in ("proceeding", "historicalproceeding")
    ] + [
        migrations.AddField(
            model_name=target,
            name="case_url",
            field=models.URLField(blank=True, max_length=500),
        )
        for target in ("proceeding", "historicalproceeding")
    ]
