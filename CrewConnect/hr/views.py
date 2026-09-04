from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache


from hr.models import Employee, Department, Designation, Leave, Payroll

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

# Create your views here.
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request, user)
            if Employee.objects.filter(user=user).exists():
                return redirect("employee_dashboard")
            return redirect("dashboard")
        return render(request,"login.html",{"error": "Invalid username or password"})
    return render(request, "login.html")


@login_required
@never_cache
def dashboard(request):
    return render(request, "dashboard.html")


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
@never_cache
def employee_list(request):
    employees = (Employee.objects.select_related("department","designation").filter(status=True))
    return render(request,"employee_list.html",{"employees": employees})

@login_required
@never_cache
def employee_create(request):

    departments = Department.objects.all()
    designations = Designation.objects.all()

    if request.method == "POST":

        employee_id = request.POST.get("employee_id")
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")

        department_id = request.POST.get("department")
        designation_id = request.POST.get("designation")

        joining_date = request.POST.get("joining_date")
        employment_type = request.POST.get("employment_type")
        salary = request.POST.get("salary")
        address = request.POST.get("address")

        status = request.POST.get("status") == "on"
        if Employee.objects.filter(email=email).exists():
            messages.error(
                request,
                "Employee with this email already exists."
            )
            return redirect("employee_create")

        # Create Django User
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=name
        )

        # Disable password until employee creates one
        user.set_unusable_password()
        user.save()

        # Create Employee
        employee = Employee.objects.create(
            user=user,
            employee_id=employee_id,
            name=name,
            email=email,
            phone=phone,
            department_id=department_id,
            designation_id=designation_id,
            joining_date=joining_date,
            employment_type=employment_type,
            salary=salary,
            address=address,
            status=status
        )

        # Generate password setup token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Password setup URL
        setup_link = request.build_absolute_uri(
            reverse(
                "set_password",
                kwargs={
                    "uidb64": uid,
                    "token": token
                }
            )
        )

        # Send email
        send_mail(
            subject="CrewConnect - Set Your Password",
            message=f"""
Hello {name},

Your CrewConnect employee account has been created.

Please click the link below to create your password:

{setup_link}

After setting your password, you can log in to CrewConnect.

Regards,
CrewConnect HR
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return redirect("employee_list")

    return render(
        request,
        "employee_add_update.html",
        {
            "departments": departments,
            "designations": designations,
            "employment_types": Employee.EMPLOYMENT_TYPES,
            "is_update": False,
        }
    )

@login_required
@never_cache
def employee_update(request, id):


    employee = get_object_or_404(Employee,id=id)


    departments = Department.objects.all()
    designations = Designation.objects.all()


    if request.method == "POST":


        employee.employee_id = request.POST.get("employee_id")
        employee.name = request.POST.get("name")
        employee.email = request.POST.get("email")
        employee.phone = request.POST.get("phone")


        employee.department_id = request.POST.get("department")
        employee.designation_id = request.POST.get("designation")


        employee.joining_date = request.POST.get("joining_date")
        employee.employment_type = request.POST.get("employment_type")
        employee.salary = request.POST.get("salary")
        employee.address = request.POST.get("address")


        employee.status = request.POST.get("status") == "on"


        employee.save()


        return redirect(
            "employee_list"
        )


    return render(request,"employee_add_update.html",
        {
            "employee": employee,
            "departments": departments,
            "designations": designations,
            "employment_types": Employee.EMPLOYMENT_TYPES,
            "is_update": True,
        }
    )

@login_required
@never_cache
def employee_delete(request, id):
    employee = get_object_or_404(Employee,id=id)
    employee.status = not employee.status
    employee.save()
    return redirect("employee_list")

@login_required
def leave_approve(request):

   # Check whether logged-in user is an employee
   if Employee.objects.filter(user=request.user).exists():
       return redirect("employee_dashboard")


   leaves = Leave.objects.select_related(
       "employee",
       "employee__department",
       "employee__designation"
   ).order_by("-applied_date")


   return render(
       request,
       "leave_approval.html",
       {
           "leaves": leaves,
           "is_employee": False,
       }
   )

@login_required
def leave_action(request, id):


    # Employee cannot approve/reject
    if Employee.objects.filter(user=request.user).exists():
        return redirect("employee_dashboard")

    if request.method == "POST":

        leave = Leave.objects.get(id=id)

        action = request.POST.get("action")

        if action == "approve":

            leave.status = "Approved"
            leave.save()

        elif action == "reject":

            leave.status = "Rejected"
            leave.save()

    return redirect("leave_approve")

@login_required
def department_data(request):
    departments = Department.objects.all()
    return render(request, "department_data.html", {
        "departments": departments
    })

@login_required()
def department_create(request):
    if request.method == "POST":
        name = request.POST.get("name")

        if name:
            Department.objects.create(name=name)
            return redirect("department_data")

    return render(request, "department_form.html")

@login_required
def department_update(request, id):

    department = get_object_or_404(Department, id=id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if name:
            department.name = name
            department.save()

            return redirect("department_data")

    return render(request, "department_form.html", {
        "department": department
    })

@login_required
def department_delete(request, id):

    department = get_object_or_404(
        Department,
        id=id
    )

    if request.method == "POST":

        department.delete()

        return redirect("department_data")

    return render(
        request,
        "department_confirm_delete.html",
        {
            "department": department
        }
    )

@login_required
def designation_data(request):

    designations = Designation.objects.all().order_by("name")

    return render(request, "designation_data.html", {
        "designations": designations
    })

@login_required
def designation_create(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if name:
            Designation.objects.create(name=name)

            return redirect("designation_data")

    return render(request, "designation_form.html")

@login_required
def designation_update(request, id):

    designation = get_object_or_404(
        Designation,
        id=id
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if name:
            designation.name = name
            designation.save()

            return redirect("designation_data")

    return render(request, "designation_form.html", {
        "designation": designation
    })

@login_required
def designation_delete(request, id):

    designation = get_object_or_404(
        Designation,
        id=id
    )

    if request.method == "POST":

        designation.delete()

        return redirect("designation_data")

    return render(request, "designation_confirm_delete.html", {
        "designation": designation
    })

@login_required
def reports(request):

    total_employees = Employee.objects.count()

    total_departments = Department.objects.count()

    total_designations = Designation.objects.count()

    active_employees = Employee.objects.filter(
        status=True
    ).count()


    department_report = Department.objects.annotate(
        employee_count=Count("employee")
    ).order_by("name")


    designation_report = Designation.objects.annotate(
        employee_count=Count("employee")
    ).order_by("name")


    employment_report = Employee.objects.values(
        "employment_type"
    ).annotate(
        employee_count=Count("id")
    ).order_by("employment_type")


    context = {

        "total_employees": total_employees,

        "total_departments": total_departments,

        "total_designations": total_designations,

        "active_employees": active_employees,

        "department_report": department_report,

        "designation_report": designation_report,

        "employment_report": employment_report,
    }

    return render(request,"reports.html",context)

@login_required
def settings_view(request):

    return render(request,"settings.html")

@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "Password changed successfully."
            )

            return redirect("settings")

    else:

        form = PasswordChangeForm(request.user)

    return render(
        request,
        "change_password.html",
        {
            "form": form
        }
    )

@login_required
def payroll_list(request):

    payrolls = Payroll.objects.select_related("employee").order_by("-month", "employee__name")

    total_payroll = sum(
        payroll.net_salary for payroll in payrolls
    )

    paid_payroll = sum(
        payroll.net_salary
        for payroll in payrolls
        if payroll.status == "Paid"
    )

    pending_payroll = sum(
        payroll.net_salary
        for payroll in payrolls
        if payroll.status == "Pending"
    )

    context = {
        "payrolls": payrolls,
        "total_payroll": total_payroll,
        "paid_payroll": paid_payroll,
        "pending_payroll": pending_payroll,
    }

    return render(request,"payroll_list.html",context)


@login_required
def payroll_create(request):

    employees = Employee.objects.filter(
        status=True
    ).order_by("name")

    if request.method == "POST":

        employee_id = request.POST.get("employee")
        month = request.POST.get("month")

        allowances = Decimal(
            request.POST.get("allowances") or "0"
        )

        deductions = Decimal(
            request.POST.get("deductions") or "0"
        )

        status = request.POST.get("status")

        employee = get_object_or_404(
            Employee,
            id=employee_id
        )

        Payroll.objects.create(
            employee=employee,
            month=month,
            basic_salary=employee.salary,
            allowances=allowances,
            deductions=deductions,
            status=status
        )

        messages.success(
            request,
            "Payroll created successfully."
        )

        return redirect("payroll_list")

    return render(request,"payroll_form.html",
                  {"employees": employees}
                  )

@login_required
def payroll_update(request, id):

    payroll = get_object_or_404(
        Payroll,
        id=id
    )

    employees = Employee.objects.filter(
        status=True
    ).order_by("name")

    if request.method == "POST":

        employee_id = request.POST.get("employee")
        month = request.POST.get("month")

        allowances = Decimal(
            request.POST.get("allowances") or "0"
        )

        deductions = Decimal(
            request.POST.get("deductions") or "0"
        )

        status = request.POST.get("status")

        employee = get_object_or_404(
            Employee,
            id=employee_id
        )

        payroll.employee = employee
        payroll.month = month
        payroll.basic_salary = employee.salary
        payroll.allowances = allowances
        payroll.deductions = deductions
        payroll.status = status

        payroll.save()

        messages.success(
            request,
            "Payroll updated successfully."
        )

        return redirect("payroll_list")

    return render(request,"payroll_form.html",
                  {
                      "payroll": payroll,
                      "employees": employees
                  }
                  )

@login_required
def payroll_delete(request, id):

    payroll = get_object_or_404(
        Payroll,
        id=id
    )

    if request.method == "POST":

        payroll.delete()

        messages.success(request,"Payroll deleted successfully.")

        return redirect("payroll_list")

    return render(request,"payroll_confirm_delete.html",
                  {"payroll": payroll}
                  )