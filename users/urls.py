from django.urls import path
from .views import ContactsCommunsView, PorfileRandomView, ToutProfilesView, RegisterView, LoginView, UserView, LogoutView, ActivateView, ResendCodeView, ProfileView, ImageProfileView, CategorieEmploieView, ProfileMarketingView, ImageProfileMarketingView, ProfileSearchView, AjoutContactView, AccepterContactView, ContactView, RefuserContactView

urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('user', UserView.as_view()),
    path('logout', LogoutView.as_view()),
    path('activate', ActivateView.as_view()),
    path('resend', ResendCodeView.as_view()),
    path('profile', ProfileView.as_view()),
    path('profile/image', ImageProfileView.as_view()),
    path('categorie', CategorieEmploieView.as_view()),
    path('buziness', ProfileMarketingView.as_view()),
    path('buziness/image', ImageProfileMarketingView.as_view()),
    path('recherche', ProfileSearchView.as_view()),
    path('profile_complet', ToutProfilesView.as_view()),
    path('get_random_profiles', PorfileRandomView.as_view()),
    path('contacts_requests', AjoutContactView.as_view()),
    path('accepter', AccepterContactView.as_view()),
    path('contacts', ContactView.as_view()),
    path('refuser', RefuserContactView.as_view()),
    path('contacts_communs', ContactsCommunsView.as_view())

]
