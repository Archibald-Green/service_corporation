from django.db import models


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField("Название роли", max_length=255)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        db_table = '"portal"."roles"'
        managed = True
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


#
# 2) portal.users
#
class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField("Логин", max_length=255)
    email = models.CharField("Email", max_length=255)
    password = models.CharField("Пароль", max_length=255)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        db_table = '"portal"."users"'
        managed = True
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


#
# 3) portal.user_roles
#    — связывает users и roles; полей id нет, поэтому managed=False
#
class UserRoles(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="role_links",
        verbose_name="Пользователь"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        db_column="role_id",
        related_name="user_links",
        verbose_name="Роль"
    )
    created_at = models.DateTimeField("Создано", blank=True, null=True)
    updated_at = models.DateTimeField("Обновлено", blank=True, null=True)

    class Meta:
        db_table = '"portal"."user_roles"'
        managed = True
        verbose_name = "Связь пользователь–роль"
        verbose_name_plural = "Связи пользователь–роль"
        unique_together = (("user", "role"),)

    def __str__(self):
        return f"{self.user.username} → {self.role.name}"


class Account(models.Model):
    id        = models.AutoField(primary_key=True)
    userid    = models.IntegerField(db_column='userid', verbose_name='User ID')
    entity    = models.CharField(max_length=50, verbose_name='Entity')
    isdeleted = models.BooleanField(verbose_name='Is Deleted')

    class Meta:
        db_table = '"public"."accounts"'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return f"{self.entity} ({self.userid})"


class EnergoDevice(models.Model):
    id               = models.AutoField(primary_key=True)
    ctime            = models.DateTimeField(verbose_name='Ctime')
    dmodel_id        = models.IntegerField(verbose_name='Model ID')
    dmodel_sensor    = models.CharField(max_length=255, verbose_name='Sensor Model')
    serial_num       = models.CharField(max_length=255, verbose_name='Serial Number')
    device_id        = models.IntegerField(verbose_name='Device ID')
    folder_id        = models.IntegerField(verbose_name='Folder ID')
    location         = models.CharField(max_length=255, verbose_name='Location')
    physical_person  = models.BooleanField(verbose_name='Physical Person')
    owner_name       = models.CharField(max_length=255, verbose_name='Owner Name')
    beg_value        = models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Beginning Value')
    phones           = models.CharField(max_length=255, verbose_name='Phones')
    sector_id        = models.IntegerField(verbose_name='Sector ID')
    mount_id         = models.IntegerField(verbose_name='Mount ID')
    mount            = models.CharField(max_length=255, verbose_name='Mount')
    archives         = models.IntegerField(verbose_name='Archives')
    alias            = models.CharField(max_length=255, verbose_name='Alias')
    enable           = models.BooleanField(verbose_name='Enabled')
    resource_id      = models.IntegerField(verbose_name='Resource ID')
    resource_inx     = models.IntegerField(verbose_name='Resource Index')
    scheme_id        = models.IntegerField(verbose_name='Scheme ID')
    dscan            = models.CharField(max_length=255, verbose_name='DScan')
    calc             = models.CharField(max_length=255, verbose_name='Calc')
    account          = models.CharField(max_length=255, verbose_name='Account')
    date_next        = models.DateField(verbose_name='Next Date', blank=True, null=True)
    date_verification= models.DateField(verbose_name='Verification Date', blank=True, null=True)
    c                = models.IntegerField(verbose_name='C', blank=True, null=True)
    dpu              = models.CharField(max_length=255, verbose_name='DPU')
    position_vertical= models.CharField(max_length=255, verbose_name='Position Vertical')
    owner_device     = models.CharField(max_length=255, verbose_name='Owner Device')
    created_at       = models.DateTimeField(verbose_name='Created At', auto_now_add=True)

    class Meta:
        db_table = '"public"."energo_devices"'
        verbose_name = 'Energo Device'
        verbose_name_plural = 'Energo Devices'

    def __str__(self):
        return f"{self.serial_num} ({self.device_id})"


class EnergoDeviceData(models.Model):
    id           = models.AutoField(primary_key=True)
    value        = models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Value')
    value_error  = models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Value Error', blank=True, null=True)
    rvalue_id    = models.IntegerField(verbose_name='RValue ID')
    c            = models.IntegerField(verbose_name='C', blank=True, null=True)
    ctime        = models.DateTimeField(verbose_name='Ctime')
    datetime     = models.DateTimeField(verbose_name='Datetime')
    type_arch_orig = models.IntegerField(verbose_name='Original Archive Type')
    type_arch    = models.IntegerField(verbose_name='Archive Type')
    success      = models.BooleanField(verbose_name='Success')
    error_arch   = models.TextField(verbose_name='Error Archive', blank=True, null=True)
    created_at   = models.DateTimeField(verbose_name='Created At', auto_now_add=True)
    device_id    = models.IntegerField(verbose_name='Device ID')

    class Meta:
        db_table = '"public"."energo_device_data"'
        verbose_name = 'Energo Device Data'
        verbose_name_plural = 'Energo Device Data'

    def __str__(self):
        return f"Data {self.id} for device {self.device_id}"
    
class Street(models.Model):
    id   = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = '"public"."streets"'
        verbose_name = 'Street'
        verbose_name_plural = 'Streets'

    def __str__(self):
        return self.name


class Entity(models.Model):
    id          = models.AutoField(primary_key=True)
    entity      = models.CharField(max_length=50)
    amount      = models.CharField(max_length=50)
    address     = models.CharField(max_length=150)
    street      = models.ForeignKey(
                      Street,
                      on_delete=models.CASCADE,
                      db_column='street_id',
                      related_name='entities',
                      verbose_name='Street'
                  )
    house       = models.CharField(max_length=64)
    flat        = models.CharField(max_length=64)
    sector      = models.CharField(max_length=3)
    addressid   = models.IntegerField(db_column='addressid')
    city        = models.CharField(max_length=20)
    type        = models.CharField(max_length=255)
    created_at  = models.DateTimeField(auto_now_add=True)
    coefficient = models.SmallIntegerField()
    team        = models.SmallIntegerField()
    tur         = models.SmallIntegerField()

    class Meta:
        db_table = '"public"."entities"'
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'

    def __str__(self):
        return f"{self.entity} @ {self.address}"
    
    
class EnergoFolder(models.Model):
    id            = models.AutoField(primary_key=True)
    name          = models.CharField(max_length=255)
    rso_name      = models.CharField(max_length=255)
    contract_num  = models.CharField(max_length=255)
    contract_date = models.DateField()
    consumer      = models.CharField(max_length=255)
    district      = models.CharField(max_length=255)
    town          = models.CharField(max_length=255)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"public"."energo_folders"'
        verbose_name = 'Energo Folder'
        verbose_name_plural = 'Energo Folders'

    def __str__(self):
        return f"{self.name} ({self.contract_num})"
    
    
    
class ErcData(models.Model):
    id                 = models.AutoField(primary_key=True)
    abonent            = models.CharField(max_length=64)
    entity             = models.CharField(max_length=64)
    surname            = models.CharField(max_length=64)
    given_name         = models.CharField(max_length=64)
    fathers_name       = models.CharField(max_length=64)
    entity_gar_su      = models.CharField(max_length=64)
    entity_type        = models.CharField(max_length=64)
    sector             = models.CharField(max_length=64)
    team               = models.CharField(max_length=64)
    city               = models.CharField(max_length=64)
    street_group       = models.CharField(max_length=64)
    street_prefix      = models.CharField(max_length=64)
    street             = models.CharField(max_length=64)
    house_prefix       = models.CharField(max_length=64)
    house_type         = models.CharField(max_length=64)
    house_number       = models.CharField(max_length=64)
    litera             = models.CharField(max_length=64)
    flat               = models.CharField(max_length=64)
    flat_test          = models.CharField(max_length=64)
    flat_type          = models.CharField(max_length=64)
    object             = models.CharField(max_length=64, db_column='object')
    registered_amount  = models.CharField(max_length=64)
    floor              = models.CharField(max_length=64)
    phone_number1      = models.CharField(max_length=64)
    phone_number2      = models.CharField(max_length=64)
    iin                = models.CharField(max_length=64)
    whaelthy_code      = models.CharField(max_length=64)
    tarif_type         = models.CharField(max_length=64)
    tarif_water        = models.CharField(max_length=64)
    tarif_saverage     = models.CharField(max_length=64)
    tu                 = models.CharField(max_length=64)
    meter_type         = models.CharField(max_length=64)
    meter_subtype      = models.CharField(max_length=64)
    meter_number       = models.CharField(max_length=64)
    verification_date  = models.CharField(max_length=64)
    readings_date      = models.CharField(max_length=64)
    readings           = models.CharField(max_length=64)
    norma              = models.CharField(max_length=64)
    test1              = models.CharField(max_length=64)
    test2              = models.CharField(max_length=64)
    area               = models.CharField(max_length=64)
    area_type          = models.CharField(max_length=64)
    seal_date          = models.CharField(max_length=64)
    seal_number        = models.CharField(max_length=64)
    source             = models.CharField(max_length=64)
    poliv              = models.CharField(max_length=64)
    tu_saverage        = models.CharField(max_length=64)
    saverage_type      = models.CharField(max_length=64)
    start_date         = models.CharField(max_length=64)
    meter_id           = models.CharField(max_length=64)
    blank_number       = models.CharField(max_length=64)
    tur                = models.CharField(max_length=64)
    bit_depth          = models.CharField(max_length=64)
    reagings_date      = models.CharField(max_length=50)

    class Meta:
        db_table = '"public"."erc_data"'
        verbose_name = 'ERC Data'
        verbose_name_plural = 'ERC Data'

    def __str__(self):
        return f"{self.abonent} / {self.entity}"
    
class ErcData2(models.Model):
    id                 = models.AutoField(primary_key=True)
    abonent            = models.CharField(max_length=64)
    entity             = models.CharField(max_length=64)
    surname            = models.CharField(max_length=64)
    given_name         = models.CharField(max_length=64)
    fathers_name       = models.CharField(max_length=64)
    entity_gar_su      = models.CharField(max_length=64)
    entity_type        = models.CharField(max_length=64)
    sector             = models.CharField(max_length=64)
    team               = models.CharField(max_length=64)
    city               = models.CharField(max_length=64)
    street_group       = models.CharField(max_length=64)
    street_prefix      = models.CharField(max_length=64)
    street             = models.CharField(max_length=64)
    house_prefix       = models.CharField(max_length=64)
    house_type         = models.CharField(max_length=64)
    house_number       = models.CharField(max_length=64)
    litera             = models.CharField(max_length=64)
    flat               = models.CharField(max_length=64)
    flat_test          = models.CharField(max_length=64)
    flat_type          = models.CharField(max_length=64)
    object             = models.CharField(max_length=64, db_column='object')
    registered_amount  = models.CharField(max_length=64)
    floor              = models.CharField(max_length=64)
    phone_number1      = models.CharField(max_length=64)
    phone_number2      = models.CharField(max_length=64)
    iin                = models.CharField(max_length=64)
    whaelthy_code      = models.CharField(max_length=64)
    tarif_type         = models.CharField(max_length=64)
    tarif_water        = models.CharField(max_length=64)
    tarif_saverage     = models.CharField(max_length=64)
    tu                 = models.CharField(max_length=64)
    meter_type         = models.CharField(max_length=64)
    meter_subtype      = models.CharField(max_length=64)
    meter_number       = models.CharField(max_length=64)
    verification_date  = models.CharField(max_length=64)
    readings_date      = models.CharField(max_length=64)
    readings           = models.CharField(max_length=64)
    norma              = models.CharField(max_length=64)
    test1              = models.CharField(max_length=64)
    test2              = models.CharField(max_length=64)
    area               = models.CharField(max_length=64)
    area_type          = models.CharField(max_length=64)
    seal_date          = models.CharField(max_length=64)
    seal_number        = models.CharField(max_length=64)
    source             = models.CharField(max_length=64)
    poliv              = models.CharField(max_length=64)
    tu_saverage        = models.CharField(max_length=64)
    saverage_type      = models.CharField(max_length=64)
    start_date         = models.CharField(max_length=64)
    meter_id           = models.CharField(max_length=64)
    blank_number       = models.CharField(max_length=64)
    tur                = models.CharField(max_length=64)
    bit_depth          = models.CharField(max_length=64)

    class Meta:
        db_table = '"public"."erc_data2"'
        verbose_name = 'ERC Data 2'
        verbose_name_plural = 'ERC Data 2'

    def __str__(self):
        return f"{self.abonent} / {self.entity}"

class ErcData1(models.Model):
    id                  = models.AutoField(primary_key=True)
    abonent             = models.CharField(max_length=64)
    entity              = models.CharField(max_length=64)
    surname             = models.CharField(max_length=64)
    given_name          = models.CharField(max_length=64)
    fathers_name        = models.CharField(max_length=64)
    entity_gar_su       = models.CharField(max_length=64)
    entity_type         = models.CharField(max_length=64)
    sector              = models.CharField(max_length=64)
    team                = models.CharField(max_length=64)
    city                = models.CharField(max_length=64)
    street_group        = models.CharField(max_length=64)
    street_prefix       = models.CharField(max_length=64)
    street              = models.CharField(max_length=64)
    house_prefix        = models.CharField(max_length=64)
    house_type          = models.CharField(max_length=64)
    house_number        = models.CharField(max_length=64)
    litera              = models.CharField(max_length=64)
    flat                = models.CharField(max_length=64)
    flat_test           = models.CharField(max_length=64)
    flat_type           = models.CharField(max_length=64)
    object              = models.CharField(max_length=64, db_column='object')
    registered_amount   = models.CharField(max_length=64)
    floor               = models.CharField(max_length=64)
    phone_number1       = models.CharField(max_length=64)
    phone_number2       = models.CharField(max_length=64)
    iin                 = models.CharField(max_length=64)
    whaelthy_code       = models.CharField(max_length=64)
    tarif_type          = models.CharField(max_length=64)
    tarif_water         = models.CharField(max_length=64)
    tarif_saverage      = models.CharField(max_length=64)
    tu                  = models.CharField(max_length=64)
    meter_type          = models.CharField(max_length=64)
    meter_subtype       = models.CharField(max_length=64)
    meter_number        = models.CharField(max_length=64)
    verification_date   = models.CharField(max_length=64)
    readings_date       = models.CharField(max_length=64)
    norma               = models.CharField(max_length=64)
    test1               = models.CharField(max_length=64)
    test2               = models.CharField(max_length=64)
    area                = models.CharField(max_length=64)
    area_type           = models.CharField(max_length=64)
    seal_date           = models.CharField(max_length=64)
    seal_number         = models.CharField(max_length=64)
    source              = models.CharField(max_length=64)
    poliv               = models.CharField(max_length=64)
    tu_saverage         = models.CharField(max_length=64)
    saverage_type       = models.CharField(max_length=64)
    start_date          = models.CharField(max_length=64)
    meter_id            = models.CharField(max_length=64)
    blank_number        = models.CharField(max_length=64)
    tur                 = models.CharField(max_length=64)
    bit_depth           = models.CharField(max_length=64)

    class Meta:
        db_table = '"public"."erc_data1"'
        verbose_name = 'ERC Data 1'
        verbose_name_plural = 'ERC Data 1'

    def __str__(self):
        return f"{self.abonent} / {self.entity}"
class MeterUser(models.Model):
    id               = models.AutoField(primary_key=True)
    isactual         = models.BooleanField(verbose_name='Is Actual')
    joined           = models.DateTimeField(verbose_name='Joined')
    last_logged_in   = models.DateTimeField(verbose_name='Last Logged In')
    number           = models.CharField(max_length=20)
    type             = models.CharField(max_length=10)
    intent           = models.CharField(max_length=50)
    intententity     = models.CharField(max_length=50)
    intentmeter      = models.CharField(max_length=50)
    intentmetercode  = models.CharField(max_length=7)
    intentseal       = models.CharField(max_length=10)
    name             = models.CharField(max_length=100)
    isadmin          = models.BooleanField(verbose_name='Is Admin')
    username         = models.CharField(max_length=50)
    phone            = models.CharField(max_length=20)
    lang             = models.CharField(max_length=10)
    return_menu      = models.CharField(max_length=100)

    class Meta:
        db_table = '"public"."users"'
        verbose_name = 'Meter User'
        verbose_name_plural = 'Meter Users'

    def __str__(self):
        return f"{self.username} (ID={self.id})"


class Feedback(models.Model):
    id                = models.AutoField(primary_key=True)
    user              = models.ForeignKey(
                           MeterUser,
                           on_delete=models.CASCADE,
                           db_column='userid',
                           related_name='feedbacks'
                        )
    txt               = models.CharField(max_length=500)
    createdate        = models.DateTimeField()
    type              = models.CharField(max_length=10)
    entity            = models.CharField(max_length=50)
    phone             = models.CharField(max_length=20)
    status            = models.CharField(max_length=10)
    ishot             = models.BooleanField()
    iscold            = models.BooleanField()
    iselect           = models.BooleanField()
    operatorid        = models.IntegerField(db_column='operatorid')
    verificationcode  = models.CharField(max_length=50)
    verificationphone = models.CharField(max_length=12)
    aktnumber         = models.CharField(max_length=50)
    scheduledate      = models.DateField()
    answer            = models.CharField(max_length=255, blank=True, null=True)
    answer_date       = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = '"public"."feedbacks"'
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'

    def __str__(self):
        return f"#{self.id} — {self.user.username}: {self.txt[:20]}…"
    
    

class IotMeter(models.Model):
    id             = models.AutoField(primary_key=True)
    modem_id       = models.IntegerField(verbose_name='Modem ID')
    port           = models.IntegerField(verbose_name='Port')
    serial_number  = models.TextField(verbose_name='Serial Number')
    consumer       = models.TextField(verbose_name='Consumer')
    account_id     = models.TextField(db_column='account_id', verbose_name='Account ID')
    last_reading   = models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Last Reading')
    created_at     = models.DateTimeField(verbose_name='Created At')

    class Meta:
        db_table = '"public"."iot_meters"'
        verbose_name = 'IOT Meter'
        verbose_name_plural = 'IOT Meters'

    def __str__(self):
        return f"{self.serial_number} (ID={self.id})"


class IotMeterData(models.Model):
    id             = models.AutoField(primary_key=True)
    dt             = models.DateTimeField(verbose_name='DateTime')
    type_of_data   = models.TextField(db_column='type_of_data', verbose_name='Data Type')
    rssi           = models.IntegerField(verbose_name='RSSI')
    snr            = models.DecimalField(max_digits=20, decimal_places=6, verbose_name='SNR')
    num_of_pulse   = models.IntegerField(db_column='num_of_pulse', verbose_name='Pulse Count')
    reading        = models.DecimalField(max_digits=20, decimal_places=6, verbose_name='Reading')
    data           = models.JSONField(verbose_name='Raw Data')
    battery_level  = models.DecimalField(max_digits=20, decimal_places=6, db_column='battery_level', verbose_name='Battery Level')
    start_reading  = models.DecimalField(max_digits=20, decimal_places=6, db_column='start_reading', verbose_name='Start Reading')
    diff_reading   = models.DecimalField(max_digits=20, decimal_places=6, db_column='diff_reading', verbose_name='Difference')
    created_at     = models.DateTimeField(verbose_name='Created At')
    meter_id       = models.IntegerField(db_column='meter_id', verbose_name='Meter ID')

    class Meta:
        db_table = '"public"."iot_meter_data"'
        verbose_name = 'IOT Meter Data'
        verbose_name_plural = 'IOT Meter Data'

    def __str__(self):
        return f"Data #{self.id} for meter {self.meter_id}"
    
    
class IotModem(models.Model):
    id                         = models.AutoField(primary_key=True)
    address_name               = models.TextField(verbose_name="Address Name")
    lat                        = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="Latitude")
    lng                        = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="Longitude")
    gateway_eui                = models.TextField(verbose_name="Gateway EUI")
    type_name                  = models.TextField(verbose_name="Type Name")
    eui                        = models.TextField(verbose_name="EUI")
    description                = models.TextField(verbose_name="Description")
    sent_date                  = models.DateTimeField(verbose_name="Sent Date")
    timezone                   = models.IntegerField(verbose_name="Timezone")
    sending_period             = models.IntegerField(verbose_name="Sending Period")
    last_net_server_sync_time  = models.DateTimeField(db_column="last_net_server_sync_time",
                                                     verbose_name="Last Net‑Server Sync")
    is_active                  = models.BooleanField(verbose_name="Is Active")
    snr                        = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="SNR")
    rssi                       = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="RSSI")
    battery_level              = models.DecimalField(max_digits=20, decimal_places=6,
                                                     verbose_name="Battery Level")
    active                     = models.BooleanField(verbose_name="Active")
    dealer_company             = models.TextField(verbose_name="Dealer Company")
    type                       = models.IntegerField(db_column="type", verbose_name="Type")
    network_server             = models.IntegerField(verbose_name="Network Server")
    address                    = models.IntegerField(verbose_name="Address")
    gateway                    = models.IntegerField(verbose_name="Gateway")
    node_service_company       = models.IntegerField(verbose_name="Node Service Company")
    created_at                 = models.DateTimeField(verbose_name="Created At")

    class Meta:
        db_table = '"public"."iot_modems"'
        verbose_name = "IOT Modem"
        verbose_name_plural = "IOT Modems"

    def __str__(self):
        return f"Modem {self.id} – {self.eui}"


class Meter(models.Model):
    id                 = models.AutoField(primary_key=True)
    entity             = models.CharField(max_length=50)
    punumber           = models.CharField(max_length=50, verbose_name="PUNumber")
    readings           = models.IntegerField(verbose_name="Readings")
    yearmonth          = models.CharField(max_length=6, verbose_name="YearMonth")
    code               = models.CharField(max_length=7)
    address            = models.CharField(max_length=150)
    location           = models.CharField(max_length=2)
    verification_date  = models.CharField(max_length=10)
    seal_number        = models.CharField(max_length=20)
    bitness            = models.IntegerField()
    initial_readings   = models.IntegerField(verbose_name="Initial Readings")
    installation_date  = models.DateField(verbose_name="Installation Date")
    final_readings     = models.IntegerField(verbose_name="Final Readings")
    deinstallation_date= models.DateField(verbose_name="De‑installation Date")
    outter_id          = models.CharField(max_length=255, verbose_name="Outer ID")
    erc_meter_id       = models.IntegerField(verbose_name="ERC Meter ID")
    bit_depth          = models.SmallIntegerField(verbose_name="Bit Depth")
    last_send_date     = models.CharField(max_length=16, verbose_name="Last Send Date")
    meter_serial       = models.CharField(max_length=50)
    meter_model        = models.CharField(max_length=50)

    class Meta:
        db_table = '"public"."meters"'
        verbose_name = "Meter"
        verbose_name_plural = "Meters"

    def __str__(self):
        return f"{self.entity} – {self.punumber}"
    
class MigrationData(models.Model):
    id                = models.AutoField(primary_key=True)
    entity_id         = models.CharField(max_length=20, db_column='entity_id')
    surname           = models.CharField(max_length=255)
    given_name        = models.CharField(max_length=255)
    fathers_name      = models.CharField(max_length=255)
    street_group      = models.CharField(max_length=64)
    street_prefix     = models.CharField(max_length=64)
    street_name       = models.CharField(max_length=255)
    house_type        = models.CharField(max_length=64)
    house_number      = models.CharField(max_length=64)
    house_literal     = models.CharField(max_length=64)
    flat_number       = models.CharField(max_length=64)
    flat_postfix      = models.CharField(max_length=64)
    meter_type        = models.CharField(max_length=64)
    meter_model       = models.CharField(max_length=64)
    meter_number      = models.CharField(max_length=64)
    verification_date = models.CharField(max_length=20)
    send_date         = models.CharField(max_length=20)
    readings          = models.CharField(max_length=20)
    sector            = models.CharField(max_length=20)

    class Meta:
        db_table = '"public"."migration_data"'
        verbose_name = 'Migration Data'
        verbose_name_plural = 'Migration Data'

    def __str__(self):
        return f"{self.entity_id} – {self.surname}"


# ——————————————
# Таблица public.readings
# ——————————————
class Reading(models.Model):
    id               = models.AutoField(primary_key=True)
    user             = models.ForeignKey(
                         'MeterUser',
                         on_delete=models.CASCADE,
                         db_column='userid',
                         related_name='readings'
                       )
    entity           = models.CharField(max_length=50)
    punumber         = models.CharField(max_length=50)
    readings         = models.DecimalField(max_digits=12, decimal_places=3)
    createdate       = models.DateTimeField()
    code             = models.CharField(max_length=7)
    disabled         = models.BooleanField()
    meterid          = models.IntegerField(db_column='meterid')
    disconnected     = models.BooleanField()
    corrected        = models.BooleanField()
    isactual         = models.BooleanField()
    sourcecode       = models.CharField(max_length=10)
    yearmonth        = models.CharField(max_length=6)
    restricted       = models.BooleanField()
    consumption      = models.IntegerField()
    operator_id      = models.IntegerField(db_column='operatorid')
    erc_meter_id     = models.BigIntegerField(db_column='erc_meter_id')
    reading2         = models.DecimalField(max_digits=10, decimal_places=3, db_column='reading2')

    class Meta:
        db_table = '"public"."readings"'
        verbose_name = 'Reading'
        verbose_name_plural = 'Readings'

    def __str__(self):
        return f"{self.entity} @ {self.punumber} → {self.readings}"


# ——————————————
# Таблица public.seals
# ——————————————
class Seal(models.Model):
    id                 = models.AutoField(primary_key=True)
    user               = models.ForeignKey(
                           'MeterUser',
                           on_delete=models.CASCADE,
                           db_column='userid',
                           related_name='seals'
                       )
    txt                = models.CharField(max_length=500)
    createdate         = models.DateTimeField()
    type               = models.CharField(max_length=10)
    entity             = models.CharField(max_length=255)
    phone              = models.CharField(max_length=20)
    status             = models.CharField(max_length=10)
    ishot              = models.BooleanField()
    iscold             = models.BooleanField()
    iselect            = models.BooleanField()
    operatorid         = models.IntegerField(db_column='operatorid')
    verificationcode   = models.CharField(max_length=50)
    verificationphone  = models.CharField(max_length=12)
    aktnumber          = models.CharField(max_length=50)
    scheduledate       = models.DateField()
    answer             = models.CharField(max_length=255, blank=True, null=True)
    answer_date        = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = '"public"."seals"'
        verbose_name = 'Seal'
        verbose_name_plural = 'Seals'

    def __str__(self):
        return f"Seal #{self.id} for user {self.user_id}"
    
class Sector(models.Model):
    id         = models.AutoField(primary_key=True)
    name       = models.CharField(max_length=3)
    pass_field = models.CharField(max_length=10, db_column='pass')
    begindate  = models.DateTimeField(db_column='begindate')
    enddate    = models.DateTimeField(db_column='enddate')
    isactual   = models.BooleanField()
    code       = models.CharField(max_length=255)
    mode       = models.CharField(max_length=255)

    class Meta:
        db_table = '"public"."sectors"'
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectors'

    def __str__(self):
        return f"{self.name} ({'active' if self.isactual else 'inactive'})"


class Setting(models.Model):
    id                   = models.AutoField(primary_key=True)
    email                = models.CharField(max_length=500)
    createdate           = models.DateTimeField()
    curyearmonth         = models.CharField(max_length=6)
    email1               = models.CharField(max_length=255)
    ivcemail             = models.CharField(max_length=50)
    dirmail              = models.CharField(max_length=50)
    meteryearmonth       = models.CharField(max_length=6,  db_column='meteryearmonth')
    meteryearmonthelec   = models.CharField(max_length=6,  db_column='meteryearmonthelec')
    ivcemail2            = models.CharField(max_length=255)
    bank_year_month      = models.CharField(max_length=255, db_column='bank_year_month')
    poliv_email          = models.CharField(max_length=255, db_column='poliv_email')
    water_email          = models.CharField(max_length=255, db_column='water_email')
    ee_email             = models.CharField(max_length=255, db_column='ee_email')

    class Meta:
        db_table = '"public"."settings"'
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return self.email


class YourTableName(models.Model):
    id            = models.IntegerField(primary_key=True)
    name          = models.CharField(max_length=255)
    rso_name      = models.CharField(max_length=255)
    contract_num  = models.CharField(max_length=255)
    contract_date = models.DateField()
    consumer      = models.CharField(max_length=255)
    district      = models.CharField(max_length=255)
    town          = models.CharField(max_length=255)

    class Meta:
        db_table = '"public"."your_table_name"'
        verbose_name = 'Your Table'
        verbose_name_plural = 'Your Tables'

    def __str__(self):
        return f"{self.name} – {self.contract_num}"