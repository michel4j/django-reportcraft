from django.db import models
from django.utils.text import gettext_lazy as _


class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Institution(models.Model):
    name = models.CharField(_('Name'), max_length=200, unique=True)
    city = models.CharField(max_length=200)
    province = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey('Country', on_delete=models.PROTECT, verbose_name=_('Country'))
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, verbose_name=_('Parent Institution'), blank=True, null=True
    )
    subjects = models.ManyToManyField(Subject, related_name='institutions')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


# Through links
Institution.subjects.through.__str__ = lambda x: f'{x.subject}/{x.institution}'
Institution.subjects.through._meta.verbose_name = _('Institution Subject')
Institution.subjects.through._meta.verbose_name_plural = _('Institution Subjects')


class Person(models.Model):
    class Type(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        USER = 'user', _('User')
        GUEST = 'guest', _('Guest')

    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    age = models.IntegerField()
    bio = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=5, choices=Type.choices, default=Type.USER)
    institution = models.ForeignKey(Institution, related_name='people', on_delete=models.PROTECT)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)
    continent = models.CharField(max_length=50, blank=True, null=True)
    subregion = models.CharField(max_length=100, blank=True, null=True)
    population = models.IntegerField(default=0)
    area = models.FloatField(help_text="Area in square kilometers", default=0.0)
    gdp = models.FloatField(help_text="Gross Domestic Product in USD", default=0.0)
    capital = models.CharField(max_length=100, blank=True, null=True)
    names = models.IntegerField(default=0)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

