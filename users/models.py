from django.db import models
from django.contrib.auth.models import AbstractUser
#ajouter 
from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Le champ Email doit être renseigné')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    name = models.CharField(max_length=255, default="")
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = None
    estValide = models.BooleanField(default=False)
    
    code = models.IntegerField(unique=False, null=True)
    dateCodeCreation = models.DateTimeField(null = True, auto_now_add=True)
     
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    #ajouter
    objects = UserManager()
    


class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    numero_mobile = models.CharField(max_length=20)
    numero_fix = models.CharField(max_length=20, blank=True, null=True)
    biographie = models.TextField(blank=True, null=True)
    nb_reference = models.IntegerField(default=0, editable=False)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

class CategorieEmploi(models.Model):
    
    desc_en = models.CharField(max_length=255)
    desc_fr = models.CharField(max_length=255)
    principal = models.CharField(max_length=255, default="", null=True)
    parent_id = models.IntegerField(default=0)


class ProfileMarketing(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_marketing')
    categorieEmploi = models.ForeignKey(CategorieEmploi, on_delete=models.CASCADE, related_name='profile_marketing')
    nomEntreprise = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    numero_mobile = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='profileMarketing_images/', blank=True, null=True)
    #Description 

class UserConnexions(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_connexions', null=True)
    dateConnexion = models.DateTimeField(null=True, auto_now_add=True)

class DemandeAjoutContact(models.Model):
    choix_etats = [
        ('en_attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('refusee', 'Refusée'),
        ('annulee', 'Annulée'),
    ]

    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandes_envoyees')
    recepteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandes_recues')
    contact_commun = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_commun', default=1)
    etat = models.CharField(max_length=20, choices=choix_etats, default='en_attente')
    dateCreation = models.DateTimeField(auto_now_add=True)
    raison =  models.CharField(max_length=255, default="")
    
    class Meta:
        unique_together = ['expediteur', 'recepteur']

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    contact = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts_de')
    dateAjout = models.DateTimeField(auto_now_add=True)

