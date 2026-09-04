from django.urls import path

from hr import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    # path("viewemployees/", viewemployees, name="viewemployees"),
    #employees related urls
    path('employees/',views.employee_list, name="employee_list"),
    path('employees/add/',views.employee_create, name="employee_create"),
    path("employees/<int:id>/edit/", views.employee_update, name="employee_update"),
    path("employees/<int:id>/delete/", views.employee_delete, name="employee_delete"),
    # leave related urls
    path('leave_approve/',views.leave_approve, name='leave_approve'),
    path('leave/<int:id>/action/',views.leave_action, name='leave_action'),
    path("departments/", views.department_data, name="department_data"),
    path("departments/create/", views.department_create, name="department_create"),
    path("departments/<int:id>/update/", views.department_update, name="department_update"),
    path("departments/<int:id>/delete/", views.department_delete, name="department_delete"),
    path("designations/", views.designation_data, name="designation_data"),
    path("designations/create/", views.designation_create, name="designation_create"),
    path("designations/<int:id>/update/", views.designation_update, name="designation_update"),
    path("designations/<int:id>/delete/", views.designation_delete, name="designation_delete"),
    path("reports/",views.reports,name="reports"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/password/", views.change_password, name="change_password"),
    path("payroll/",views.payroll_list,name="payroll_list"),
    path("payroll/create/",views.payroll_create,name="payroll_create"),
    path("payroll/<int:id>/update/",views.payroll_update,name="payroll_update"),
    path("payroll/<int:id>/delete/",views.payroll_delete,name="payroll_delete"),




]