from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("libros", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="libro",
            name="imagen_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
    ]
