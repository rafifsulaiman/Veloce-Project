from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import re
from django.core.exceptions import ValidationError

def validate_email(value):
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, value):
        raise ValidationError('Format email tidak valid. Contoh: user@example.com')

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)
    
class CustomUser(AbstractUser):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
    )
    
    email = models.CharField(
            max_length=255, 
            unique=True, 
            validators=[validate_email]  # Validasi email manual
        )
    profile_pic_url = models.CharField(max_length=255, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    location = models.CharField(max_length=50, blank=True, null=True, default="Indonesia")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @property
    def is_regular_user(self):
        return not self.is_admin and not self.is_superuser

    def get_addresses(self):
        """Return all addresses belonging to this user."""
        return self.addresses.all()

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    
    # Detailed address fields
    street_address = models.CharField(max_length=255, help_text="Nama jalan dan nomor")
    rt_rw = models.CharField(max_length=20, blank=True, null=True, help_text="RT/RW (opsional)")
    village = models.CharField(max_length=100, help_text="Kelurahan/Desa")
    district = models.CharField(max_length=100, help_text="Kecamatan")
    city = models.CharField(max_length=100, help_text="Kota/Kabupaten")
    province = models.CharField(max_length=100, help_text="Provinsi")
    postal_code = models.CharField(max_length=10, help_text="Kode Pos")
    
    additional_info = models.TextField(blank=True, null=True, help_text="Informasi tambahan, seperti patokan atau detail lainnya")
    is_main = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.street_address}, {self.city}"
    
    def get_complete_address(self):
        parts = [self.street_address]
        if self.rt_rw:
            parts.append(f"RT/RW: {self.rt_rw}")
        parts.extend([
            f"Kel. {self.village}",
            f"Kec. {self.district}",
            self.city,
            self.province,
            f"Kode Pos: {self.postal_code}"
        ])
        if self.additional_info:
            parts.append(self.additional_info)
        return ", ".join(parts)
    
    def get_full_address_en(self):
        parts = [self.street_address]
        if self.rt_rw:
            parts.append(f"RT/RW: {self.rt_rw}")
        parts.extend([
            f"Village: {self.village}",
            f"District: {self.district}",
            f"City: {self.city}",
            f"Province: {self.province}",
            f"Postal Code: {self.postal_code}"
        ])
        if self.additional_info:
            parts.append(self.additional_info)
        return ", ".join(parts)
    
    def save(self, *args, **kwargs):
        # If this address is set as main, unset all other addresses as main
        if self.is_main:
            Address.objects.filter(user=self.user, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)
