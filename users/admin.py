from django.contrib import admin

# Register your models here.
from .models import User , DemandeAjoutContact


class UserAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'email', 'username', 'estValide', 'code', 'dateCodeCreation')
    

class DemandeAjoutContactAdmin(admin.ModelAdmin):
    list_display = ('choix_etats', 'expediteur', 'recepteur', 'contact_commun', 'etat', 'dateCreation', 'raison')
    


admin.site.register(User, UserAdmin)
admin.site.register(DemandeAjoutContact, DemandeAjoutContactAdmin)

