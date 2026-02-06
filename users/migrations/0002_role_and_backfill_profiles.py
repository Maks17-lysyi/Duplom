from django.db import migrations, models


def backfill_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    GamerProfile = apps.get_model("users", "GamerProfile")

    existing_user_ids = set(GamerProfile.objects.values_list("user_id", flat=True))
    missing = [GamerProfile(user_id=u.id) for u in User.objects.exclude(id__in=existing_user_ids)]
    if missing:
        GamerProfile.objects.bulk_create(missing, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamerprofile",
            name="role",
            field=models.CharField(blank=True, choices=[
                ("entry", "Entry"),
                ("support", "Support"),
                ("igl", "IGL"),
                ("awp", "AWP / Sniper"),
                ("lurk", "Lurker"),
                ("flex", "Flex"),
                ("duelist", "Duelist"),
                ("initiator", "Initiator"),
                ("controller", "Controller"),
                ("sentinel", "Sentinel"),
                ("pos1", "Dota Pos 1 (Carry)"),
                ("pos2", "Dota Pos 2 (Mid)"),
                ("pos3", "Dota Pos 3 (Offlane)"),
                ("pos4", "Dota Pos 4 (Soft Support)"),
                ("pos5", "Dota Pos 5 (Hard Support)"),
            ], max_length=16),
        ),
        migrations.RunPython(backfill_profiles, migrations.RunPython.noop),
    ]

