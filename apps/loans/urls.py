"""URLs de la app loans bajo el prefijo /api/v1/."""

from django.urls import path

from apps.loans import views

urlpatterns = [
    path('loans/', views.LoanListCreateView.as_view(), name='loans'),
    path('loans/<uuid:loan_id>/', views.LoanDetailView.as_view(), name='loan-detail'),
    path(
        'loans/<uuid:loan_id>/messages/',
        views.LoanMessageListCreateView.as_view(),
        name='loan-messages',
    ),
    path(
        'loans/<uuid:loan_id>/review/',
        views.LoanReviewView.as_view(),
        name='loan-review',
    ),
    path(
        'loans/<uuid:loan_id>/cancel/',
        views.LoanCancelView.as_view(),
        name='loan-cancel',
    ),
    path(
        'loans/<uuid:loan_id>/archive/',
        views.LoanArchiveView.as_view(),
        name='loan-archive',
    ),
    path(
        'reviews/users/<uuid:user_id>/',
        views.UserReputationView.as_view(),
        name='user-reputation',
    ),
    path(
        'loans/<uuid:loan_id>/installments/<int:number>/pay/',
        views.InstallmentPayView.as_view(),
        name='loan-installment-pay',
    ),
]
