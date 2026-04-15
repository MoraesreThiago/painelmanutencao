# Generated manually to bridge equipamentos.Motor and motores.ElectricMotor.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipamentos", "0002_equipment_unidade"),
        ("motores", "0003_burnedmotorcase_unidade_electricmotor_unidade"),
    ]

    operations = [
        migrations.AddField(
            model_name="motor",
            name="electric_motor",
            field=models.ForeignKey(
                blank=True,
                help_text="Vínculo com o cadastro técnico em motores.ElectricMotor, quando existir.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="equipment_motors",
                to="motores.electricmotor",
                verbose_name="Motor elétrico do catálogo",
            ),
        ),
    ]
