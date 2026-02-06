from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lobbies", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lobby",
            name="required_role",
            field=models.CharField(
                choices=[
                    ("any", "Any"),
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
                ],
                default="any",
                max_length=16,
            ),
        ),
    ]

