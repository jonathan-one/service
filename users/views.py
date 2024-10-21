from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import CategorieEmploiSerializer, ProfileMarketingSerializer, UserSerializer, ProfileSerializer, DemandeAjoutContactSerializer, ContactSerializer
from .models import ProfileMarketing, User, Profile, CategorieEmploi, UserConnexions, DemandeAjoutContact, Contact
import jwt, datetime
from django.utils import timezone
import sendgrid
from sendgrid.helpers.mail import Mail
from rest_framework.permissions import IsAuthenticated
from random import randint, random
from rest_framework import status
import base64
from django.db.models import Q
from django.conf import settings
from django.core.files.base import ContentFile
import random


# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            raise AuthenticationFailed("Votre mot de passe ou courriel n'est pas valide.")
        
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')

        response = Response()
        user.last_login = timezone.now()
        user.save()
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }
        return response


class UserView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Session non valide!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.DecodeError:
            raise AuthenticationFailed('Session non valide!')

        user = User.objects.filter(id=payload.get('id')).first()
        serializer = UserSerializer(user)
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        return Response(serializer.data)



class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response


class ActivateView(APIView):
    def post(self, request):
        codeValider = request.data['code']
        emailUtilisateur = request.data['email']
        user = User.objects.filter(email=emailUtilisateur).first()


        if codeValider == user.code:
            if timezone.now() - user.dateCodeCreation > timezone.timedelta(minutes=10):
                return Response("Le code que vous avez composé a expiré")
            user.estValide = True
            user.save()
            message = "Le compte de " + user.email + " a été validé"
            return Response(message)
        else:
            message = "Le code saisie est invalide"
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        

class ResendCodeView(APIView):

    def post(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')

        user = User.objects.filter(id=payload['id']).first()

        user.code = randint(1000, 9999)
        user.dateCodeCreation = timezone.now()
        user.save()
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())

        sg = sendgrid.SendGridAPIClient(api_key=str(settings.SENDGRID_API_KEY))

        message = Mail(
            from_email='support@goconnexions.com',
            to_emails = user.email,
            subject = "Nouveau code de confirmation",
            html_content = f'Votre nouveau code de confirmation est : {user.code}'
        )

        sg.send(message)

        return Response("Nouveau code généré avec succès !")
    

class ProfileView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        profile = Profile.objects.filter(user_id=user.id).first()
        serializer = ProfileSerializer(profile)
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        return Response(serializer.data)

    def post(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        if user.estValide == False:
            return Response("Vous devez activer votre compte avant de créer un profil", status=status.HTTP_400_BAD_REQUEST)
        profile, created = Profile.objects.get_or_create(user=user)
        serializer = ProfileSerializer(profile, data=request.data)
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        # Vérifier si la photo est nulle et la remplacer si nécessaire
        if serializer.is_valid():
            if 'image' not in request.data or request.data['image'] is None:
                # Chemin de l'image par défaut
                default_image_path = settings.MEDIA_ROOT + 'profile_images/profileVide.png'
                with open(default_image_path, 'rb') as f:
                    # Créer un objet de fichier Django à partir du fichier brut
                    default_image = ContentFile(f.read(), name='default_image.jpg')
                    serializer.validated_data['image'] = default_image
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ImageProfileView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        profile = Profile.objects.filter(user_id=user.id).first()
        if not profile or not profile.image:
            raise AuthenticationFailed("Image de profil introuvable")
        image_path = profile.image.path
        with open(image_path, "rb") as image_file:
            # Encode the image bytes in base64
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            return Response(image_base64)


class CategorieEmploieView(APIView):
    def get(self, request):
        parent_id = request.GET.get('parent')

        if parent_id is not None:
            parent_id = int(parent_id)
            if parent_id==0:
                categories = CategorieEmploi.objects.all()
            else:
                categories = CategorieEmploi.objects.filter(parent_id=parent_id)
            
        else:
            categories = CategorieEmploi.objects.all()
        serializer = CategorieEmploiSerializer(categories, many=True)
        return Response(serializer.data)       
        


class ProfileMarketingView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        profileMarketing = ProfileMarketing.objects.filter(user_id=user.id).first()
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        serializer = ProfileMarketingSerializer(profileMarketing)
        return Response(serializer.data)

    def put(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        print(user)
        profil = Profile.objects.filter(user_id=user.id).first()
        print(profil)
        categorie =  CategorieEmploi.objects.filter(id=request.data.get('categorieEmploi')).first()
        print(categorie)
        if profil is None:
            return Response("Vous devez d'abord mettre à jours votre profil personnel", status=status.HTTP_400_BAD_REQUEST) 
        profileMarketing, created = ProfileMarketing.objects.get_or_create(user=user)
        serializer = ProfileMarketingSerializer(profileMarketing, data=request.data)
        if serializer.is_valid():
            UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        print(user)
        profil = Profile.objects.filter(user_id=user.id).first()
        print(profil)
        categorie =  CategorieEmploi.objects.filter(id=request.data.get('categorieEmploi')).first()
        print(categorie)
        if profil is None:
            return Response("Vous devez d'abord mettre à jours votre profil personnel", status=status.HTTP_400_BAD_REQUEST) 
        profileMarketing, created = ProfileMarketing.objects.get_or_create(user=user, categorieEmploi=categorie)
        serializer = ProfileMarketingSerializer(profileMarketing, data=request.data)
        if serializer.is_valid():
            UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ImageProfileMarketingView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        profileMarketing = ProfileMarketing.objects.filter(user_id=user.id).first()
        if not profileMarketing or not profileMarketing.image:
            raise AuthenticationFailed("Image de profil introuvable")
        image_path = profileMarketing.image.path
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        with open(image_path, "rb") as image_file:
            # Encode the image bytes in base64
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            return Response(image_base64)
        



class ProfileSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('nom', None)
        if not query:
            return Response({"message": "Le paramètre 'nom' est requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        profiles = Profile.objects.filter(Q(nom__icontains=query) | Q(prenom__icontains=query))
  
        if not profiles:
            return Response({"message": "Aucun profil trouvé avec ce nom ou prénom."}, status=status.HTTP_404_NOT_FOUND)
        
        data = []
        for profile in profiles:
            image_file = profile.image
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            profile_data = {
                'id': profile.id,
                'id_user': profile.user.id,
                'prenom': profile.prenom,
                'nom': profile.nom,
                'biographie': profile.biographie,
                'image': image_base64
            }
            data.append(profile_data)

        return Response(data)

    

class ToutProfilesView(APIView):
    def get(self, request):
        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)
    

import base64

class PorfileRandomView(APIView):
    def get(self, request):
        num_profiles = request.query_params.get('num_profiles', 5)  # Default to 2 if 'num_profiles' query parameter is not provided
        profiles = Profile.objects.all()
        random_profiles = random.sample(list(profiles), min(int(num_profiles), len(profiles)))
        serialized_data = []

        for profile in random_profiles:
            # Assuming 'image' is a field in your ProfileSerializer
            profile_data = ProfileSerializer(profile).data
            if profile.image:  # Assuming 'image' is a field in your Profile model
                # Convert image data to base64
                with open(profile.image.path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                profile_data['image'] = base64_image
            serialized_data.append(profile_data)

        return Response(serialized_data)
    
class AjoutContactView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        demandesContacts = DemandeAjoutContact.objects.filter(recepteur=user.id)
        serializer = DemandeAjoutContactSerializer(demandesContacts, many=True)
        UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
        return Response(serializer.data)

    def post(self, request):
        token = request.COOKIES.get('jwt')
        idRecepteur = request.data['idRecepteur']
        idExpediteur = request.data['idExpediteur']
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        contact_commun = User.objects.filter(id=payload['id']).first()
        expediteur = User.objects.filter(id=idExpediteur).first()
        recepteur = User.objects.filter(id=idRecepteur).first()
        if Contact.objects.filter(user=expediteur, contact=recepteur).exists():
            return Response("Les deux personnes sont déjà en contact")
        if not (Contact.objects.filter(user=contact_commun, contact=expediteur).exists() or Contact.objects.filter(user=contact_commun, contact=recepteur).exists()):
            return Response("Un des membres n'est pas dans votre liste de contact", status=status.HTTP_400_BAD_REQUEST)
        else:
            UserConnexions.objects.create(user=contact_commun, dateConnexion=timezone.now())
            DemandeAjoutContact.objects.create(expediteur=expediteur, contact_commun=contact_commun, recepteur_id=recepteur.id, etat="en_attente",dateCreation=timezone.now())
            return Response("Le contact a bien été ajouté", status=status.HTTP_200_OK)
        
    def delete(self, request):
        token = request.COOKIES.get('jwt')
        idDemande = request.data['idDemande']
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        user = User.objects.filter(id=payload['id']).first()
        demande = DemandeAjoutContact.objects.filter(id = idDemande).first()
        if demande.contact_commun.id == user.id:
            if demande.etat=="acceptee":
                return Response("La demande que vous tentez d'annuler a déjà été acceptée", status=status.HTTP_400_BAD_REQUEST)
            demande.etat = "annulee"
            demande.save()
            UserConnexions.objects.create(user=user, dateConnexion=timezone.now())
            return Response("La demande a bien été annulée", status=status.HTTP_200_OK)
        else:
            return Response("La demande que vous essayez d'annuler n'est pas la vôtre !", status=status.HTTP_400_BAD_REQUEST)


class AccepterContactView(APIView):
    def post(self, request):
        token = request.COOKIES.get('jwt')
        idDemande = request.data['idDemande']
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        demande = DemandeAjoutContact.objects.filter(id=idDemande).first()
        id = payload['id']
        if id == demande.recepteur.id:
            if not demande.etat == "en_attente":
                return Response("Cette demande a été annulée ou a déjà été acceptée", status=status.HTTP_400_BAD_REQUEST)
            demande.etat = "acceptee"
            demande.save()
            Contact.objects.create(user = demande.expediteur, contact = demande.recepteur, dateAjout = timezone.now())      
            Contact.objects.create(user = demande.recepteur, contact = demande.expediteur, dateAjout = timezone.now())  
            UserConnexions.objects.create(user=demande.recepteur, dateConnexion=timezone.now())        
            return Response("La demande a été acceptée", status=status.HTTP_200_OK)
        else:
            return Response("La demande est introuvable")
        
class ContactView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        utilisateur = User.objects.filter(id=payload['id']).first()
        contacts = Contact.objects.filter(user = utilisateur)
        serializer = ContactSerializer(contacts, many=True)
        UserConnexions.objects.create(user=utilisateur, dateConnexion=timezone.now())
        return Response(serializer.data)       
    
class RefuserContactView(APIView):
    def post(self, request):
        token = request.COOKIES.get('jwt')
        idDemande = request.data['idDemande']
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')
        demande = DemandeAjoutContact.objects.filter(id=idDemande).first()
        id = payload['id']
        if id == demande.recepteur.id:
            if not demande.etat == "en_attente":
                return Response("Cette demande a été annulée ou a déjà été acceptée", status=status.HTTP_400_BAD_REQUEST)
            demande.etat = "refusee"
            demande.save()
            UserConnexions.objects.create(user=demande.recepteur, dateConnexion=timezone.now())     
            return Response("La demande a été refusée", status=status.HTTP_200_OK)
        else:
            return Response("La demande est introuvable")
        
class ContactsCommunsView(APIView):
    def get(self, request):
        token = request.COOKIES.get('jwt')
        user_id = request.data.get('user_id')  # Utilisez get au lieu de ['user_id'] pour gérer le cas où la clé 'user_id' est manquante
        if not token:
            raise AuthenticationFailed("Vous devez vous connecter")

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Session non valide')

        current_user = User.objects.get(id=payload['id'])
        specified_user = User.objects.get(id=user_id)

        # Récupérer les utilisateurs en commun à partir des objets Contact
        common_contacts = Contact.objects.filter(user__in=[current_user, specified_user]).values_list('contact', flat=True)
        
        # Récupérer les informations des utilisateurs en commun
        common_users = User.objects.filter(id__in=common_contacts)

        # Sérialiser les utilisateurs pour retourner uniquement id et email
        serializer = UserSerializer(common_users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
        #Fonction non finie, à fixer plus tard
