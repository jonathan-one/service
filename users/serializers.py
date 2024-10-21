from rest_framework import serializers
from .models import (
    User,
    Profile,
    CategorieEmploi,
    ProfileMarketing,
    DemandeAjoutContact,
    Contact,
)
from random import randint
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password", "code", "estValide"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = self.Meta.model(**validated_data)
        code = randint(1000, 9999)
        instance = self.Meta.model(code=code, **validated_data)
        if password is not None:
            instance.set_password(password)

        # Sauvegarde de l'utilisateur
        instance.save()

        # Création du profil associé
        profile_data = {
            "user": instance,
            "prenom": "",
            "nom": "",
            "adresse": "",
            "numero_mobile": "",
            "image": settings.MEDIA_ROOT + "profile_images/profileVide.png",
        }
        Profile.objects.create(**profile_data)

        # Création du profil marketing associé
        categorie_emploi = CategorieEmploi.objects.first()

        # verification (add)
        if not categorie_emploi:
            raise serializers.ValidationError(
                "Aucune catégorie d'emploi trouvée. Veuillez en créer une avant de continuer."
            )

        profile_marketing_data = {
            "user": instance,
            "nomEntreprise": "",
            "adresse": "",
            "numero_mobile": "",
            "description": "",
            "categorieEmploi": categorie_emploi,
            "image": settings.MEDIA_ROOT
            + "profileMarketing_images/logoVideMarketing.png",
        }
        ProfileMarketing.objects.create(**profile_marketing_data)

        # Envoi du courriel de confirmation (code non modifié)
        sg = sendgrid.SendGridAPIClient(api_key=str(settings.SENDGRID_API_KEY))
        message = Mail(
            from_email="support@goconnexions.com",
            to_emails=instance.email,
            subject="Confirmation de votre adresse courriel goConnexions",
            html_content=f"Votre code de confirmation est : {code}<br>Ce code sera valable pour une période de 10 minutes.",
        )
        sg.send(message)

        return instance


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "prenom",
            "nom",
            "adresse",
            "numero_mobile",
            "numero_fix",
            "biographie",
            "nb_reference",
            "image",
        ]


class CategorieEmploiSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieEmploi
        fields = ["id", "desc_fr", "desc_en", "parent_id", "principal"]


class ProfileMarketingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileMarketing
        fields = [
            "nomEntreprise",
            "adresse",
            "numero_mobile",
            "description",
            "image",
            "categorieEmploi",
        ]


class DemandeAjoutContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeAjoutContact
        fields = [
            "id",
            "expediteur",
            "recepteur",
            "contact_commun",
            "etat",
            "dateCreation",
        ]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "user", "contact", "dateAjout"]
