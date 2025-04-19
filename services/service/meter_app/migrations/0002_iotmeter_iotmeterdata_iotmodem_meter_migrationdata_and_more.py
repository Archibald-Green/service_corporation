# Generated by Django 4.2.5 on 2025-04-19 13:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meter_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IotMeter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('modem_id', models.IntegerField(verbose_name='Modem ID')),
                ('port', models.IntegerField(verbose_name='Port')),
                ('serial_number', models.TextField(verbose_name='Serial Number')),
                ('consumer', models.TextField(verbose_name='Consumer')),
                ('account_id', models.TextField(db_column='account_id', verbose_name='Account ID')),
                ('last_reading', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='Last Reading')),
                ('created_at', models.DateTimeField(verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'IOT Meter',
                'verbose_name_plural': 'IOT Meters',
                'db_table': '"public"."iot_meters"',
            },
        ),
        migrations.CreateModel(
            name='IotMeterData',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('dt', models.DateTimeField(verbose_name='DateTime')),
                ('type_of_data', models.TextField(db_column='type_of_data', verbose_name='Data Type')),
                ('rssi', models.IntegerField(verbose_name='RSSI')),
                ('snr', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='SNR')),
                ('num_of_pulse', models.IntegerField(db_column='num_of_pulse', verbose_name='Pulse Count')),
                ('reading', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='Reading')),
                ('data', models.JSONField(verbose_name='Raw Data')),
                ('battery_level', models.DecimalField(db_column='battery_level', decimal_places=6, max_digits=20, verbose_name='Battery Level')),
                ('start_reading', models.DecimalField(db_column='start_reading', decimal_places=6, max_digits=20, verbose_name='Start Reading')),
                ('diff_reading', models.DecimalField(db_column='diff_reading', decimal_places=6, max_digits=20, verbose_name='Difference')),
                ('created_at', models.DateTimeField(verbose_name='Created At')),
                ('meter_id', models.IntegerField(db_column='meter_id', verbose_name='Meter ID')),
            ],
            options={
                'verbose_name': 'IOT Meter Data',
                'verbose_name_plural': 'IOT Meter Data',
                'db_table': '"public"."iot_meter_data"',
            },
        ),
        migrations.CreateModel(
            name='IotModem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('address_name', models.TextField(verbose_name='Address Name')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='Latitude')),
                ('lng', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='Longitude')),
                ('gateway_eui', models.TextField(verbose_name='Gateway EUI')),
                ('type_name', models.TextField(verbose_name='Type Name')),
                ('eui', models.TextField(verbose_name='EUI')),
                ('description', models.TextField(verbose_name='Description')),
                ('sent_date', models.DateTimeField(verbose_name='Sent Date')),
                ('timezone', models.IntegerField(verbose_name='Timezone')),
                ('sending_period', models.IntegerField(verbose_name='Sending Period')),
                ('last_net_server_sync_time', models.DateTimeField(db_column='last_net_server_sync_time', verbose_name='Last Net‑Server Sync')),
                ('is_active', models.BooleanField(verbose_name='Is Active')),
                ('snr', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='SNR')),
                ('rssi', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='RSSI')),
                ('battery_level', models.DecimalField(decimal_places=6, max_digits=20, verbose_name='Battery Level')),
                ('active', models.BooleanField(verbose_name='Active')),
                ('dealer_company', models.TextField(verbose_name='Dealer Company')),
                ('type', models.IntegerField(db_column='type', verbose_name='Type')),
                ('network_server', models.IntegerField(verbose_name='Network Server')),
                ('address', models.IntegerField(verbose_name='Address')),
                ('gateway', models.IntegerField(verbose_name='Gateway')),
                ('node_service_company', models.IntegerField(verbose_name='Node Service Company')),
                ('created_at', models.DateTimeField(verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'IOT Modem',
                'verbose_name_plural': 'IOT Modems',
                'db_table': '"public"."iot_modems"',
            },
        ),
        migrations.CreateModel(
            name='Meter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('entity', models.CharField(max_length=50)),
                ('punumber', models.CharField(max_length=50, verbose_name='PUNumber')),
                ('readings', models.IntegerField(verbose_name='Readings')),
                ('yearmonth', models.CharField(max_length=6, verbose_name='YearMonth')),
                ('code', models.CharField(max_length=7)),
                ('address', models.CharField(max_length=150)),
                ('location', models.CharField(max_length=2)),
                ('verification_date', models.CharField(max_length=10)),
                ('seal_number', models.CharField(max_length=20)),
                ('bitness', models.IntegerField()),
                ('initial_readings', models.IntegerField(verbose_name='Initial Readings')),
                ('installation_date', models.DateField(verbose_name='Installation Date')),
                ('final_readings', models.IntegerField(verbose_name='Final Readings')),
                ('deinstallation_date', models.DateField(verbose_name='De‑installation Date')),
                ('outter_id', models.CharField(max_length=255, verbose_name='Outer ID')),
                ('erc_meter_id', models.IntegerField(verbose_name='ERC Meter ID')),
                ('bit_depth', models.SmallIntegerField(verbose_name='Bit Depth')),
                ('last_send_date', models.CharField(max_length=16, verbose_name='Last Send Date')),
                ('meter_serial', models.CharField(max_length=50)),
                ('meter_model', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Meter',
                'verbose_name_plural': 'Meters',
                'db_table': '"public"."meters"',
            },
        ),
        migrations.CreateModel(
            name='MigrationData',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('entity_id', models.CharField(db_column='entity_id', max_length=20)),
                ('surname', models.CharField(max_length=255)),
                ('given_name', models.CharField(max_length=255)),
                ('fathers_name', models.CharField(max_length=255)),
                ('street_group', models.CharField(max_length=64)),
                ('street_prefix', models.CharField(max_length=64)),
                ('street_name', models.CharField(max_length=255)),
                ('house_type', models.CharField(max_length=64)),
                ('house_number', models.CharField(max_length=64)),
                ('house_literal', models.CharField(max_length=64)),
                ('flat_number', models.CharField(max_length=64)),
                ('flat_postfix', models.CharField(max_length=64)),
                ('meter_type', models.CharField(max_length=64)),
                ('meter_model', models.CharField(max_length=64)),
                ('meter_number', models.CharField(max_length=64)),
                ('verification_date', models.CharField(max_length=20)),
                ('send_date', models.CharField(max_length=20)),
                ('readings', models.CharField(max_length=20)),
                ('sector', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name': 'Migration Data',
                'verbose_name_plural': 'Migration Data',
                'db_table': '"public"."migration_data"',
            },
        ),
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=3)),
                ('pass_field', models.CharField(db_column='pass', max_length=10)),
                ('begindate', models.DateTimeField(db_column='begindate')),
                ('enddate', models.DateTimeField(db_column='enddate')),
                ('isactual', models.BooleanField()),
                ('code', models.CharField(max_length=255)),
                ('mode', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Sector',
                'verbose_name_plural': 'Sectors',
                'db_table': '"public"."sectors"',
            },
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.CharField(max_length=500)),
                ('createdate', models.DateTimeField()),
                ('curyearmonth', models.CharField(max_length=6)),
                ('email1', models.CharField(max_length=255)),
                ('ivcemail', models.CharField(max_length=50)),
                ('dirmail', models.CharField(max_length=50)),
                ('meteryearmonth', models.CharField(db_column='meteryearmonth', max_length=6)),
                ('meteryearmonthelec', models.CharField(db_column='meteryearmonthelec', max_length=6)),
                ('ivcemail2', models.CharField(max_length=255)),
                ('bank_year_month', models.CharField(db_column='bank_year_month', max_length=255)),
                ('poliv_email', models.CharField(db_column='poliv_email', max_length=255)),
                ('water_email', models.CharField(db_column='water_email', max_length=255)),
                ('ee_email', models.CharField(db_column='ee_email', max_length=255)),
            ],
            options={
                'verbose_name': 'Setting',
                'verbose_name_plural': 'Settings',
                'db_table': '"public"."settings"',
            },
        ),
        migrations.CreateModel(
            name='YourTableName',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('rso_name', models.CharField(max_length=255)),
                ('contract_num', models.CharField(max_length=255)),
                ('contract_date', models.DateField()),
                ('consumer', models.CharField(max_length=255)),
                ('district', models.CharField(max_length=255)),
                ('town', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Your Table',
                'verbose_name_plural': 'Your Tables',
                'db_table': '"public"."your_table_name"',
            },
        ),
        migrations.CreateModel(
            name='Seal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('txt', models.CharField(max_length=500)),
                ('createdate', models.DateTimeField()),
                ('type', models.CharField(max_length=10)),
                ('entity', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=20)),
                ('status', models.CharField(max_length=10)),
                ('ishot', models.BooleanField()),
                ('iscold', models.BooleanField()),
                ('iselect', models.BooleanField()),
                ('operatorid', models.IntegerField(db_column='operatorid')),
                ('verificationcode', models.CharField(max_length=50)),
                ('verificationphone', models.CharField(max_length=12)),
                ('aktnumber', models.CharField(max_length=50)),
                ('scheduledate', models.DateField()),
                ('answer', models.CharField(blank=True, max_length=255, null=True)),
                ('answer_date', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, related_name='seals', to='meter_app.meteruser')),
            ],
            options={
                'verbose_name': 'Seal',
                'verbose_name_plural': 'Seals',
                'db_table': '"public"."seals"',
            },
        ),
        migrations.CreateModel(
            name='Reading',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('entity', models.CharField(max_length=50)),
                ('punumber', models.CharField(max_length=50)),
                ('readings', models.DecimalField(decimal_places=3, max_digits=12)),
                ('createdate', models.DateTimeField()),
                ('code', models.CharField(max_length=7)),
                ('disabled', models.BooleanField()),
                ('meterid', models.IntegerField(db_column='meterid')),
                ('disconnected', models.BooleanField()),
                ('corrected', models.BooleanField()),
                ('isactual', models.BooleanField()),
                ('sourcecode', models.CharField(max_length=10)),
                ('yearmonth', models.CharField(max_length=6)),
                ('restricted', models.BooleanField()),
                ('consumption', models.IntegerField()),
                ('operator_id', models.IntegerField(db_column='operatorid')),
                ('erc_meter_id', models.BigIntegerField(db_column='erc_meter_id')),
                ('reading2', models.DecimalField(db_column='reading2', decimal_places=3, max_digits=10)),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='meter_app.meteruser')),
            ],
            options={
                'verbose_name': 'Reading',
                'verbose_name_plural': 'Readings',
                'db_table': '"public"."readings"',
            },
        ),
    ]
