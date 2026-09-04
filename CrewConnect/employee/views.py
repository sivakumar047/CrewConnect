from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode

from hr.models import Leave, Employee

User = get_user_model()
# Create your views here.
def set_password(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None


    if user is None or not default_token_generator.check_token(user, token):
        return render(request, "invalid_link.html")


    if request.method == "POST":


        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")


        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(
                "set_password",
                uidb64=uidb64,
                token=token
            )


        user.set_password(password)
        user.save()


        messages.success(
            request,
            "Password created successfully. You can now login."
        )


        return redirect("login")


    return render(request, "set_password.html")

@login_required
def employee_dashboard(request):


   employee = request.user.employee


   return render(request,"employee_dashboard.html",
                 {"employee": employee,"is_employee": True})

@login_required
def employee_profile(request):

    employee = request.user.employee

    return render(request, "profile.html",
                  {"employee": employee, "is_employee": True})

@login_required
def apply_leave(request):

    employee = request.user.employee
    if request.method == "POST":

        leave_type = request.POST.get("leave_type")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason")

        Leave.objects.create(employee=employee,
                             leave_type=leave_type,
                             start_date=start_date,
                             end_date=end_date,
                             reason=reason
                             )

        messages.success(request,"Leave application submitted successfully.")

        return redirect("my_leaves")

    return render(
        request,
        "apply_leave.html",
        {
            "leave_types": Leave.LEAVE_TYPES,
            "is_employee": True,
        }
    )

@login_required
def my_leaves(request):

    employee = request.user.employee

    leaves = Leave.objects.filter(employee=employee).order_by("-applied_date")

    return render(
        request,
        "my_leaves.html",
        {
            "leaves": leaves,
            "is_employee": True,
        }
    )

from calendar import monthrange
from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from hr.models import Leave
@login_required
def leave_calendar(request):

    employee = request.user.employee

    today = date.today()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    # Fix month navigation
    if month < 1:
        month = 12
        year -= 1

    if month > 12:
        month = 1
        year += 1

    # ------------------------------------------------
    # INDIA MNC HOLIDAYS - 2026
    # ------------------------------------------------

    holidays = {
        "2026-01-01": "New Year's Day",
        "2026-01-15": "Makar Sankranti / Pongal",
        "2026-01-26": "Republic Day",

        "2026-03-04": "Holi",
        "2026-03-20": "Eid-ul-Fitr",

        "2026-04-03": "Good Friday",

        "2026-05-01": "May Day / Labour Day",

        "2026-08-15": "Independence Day",
        "2026-09-14": "Ganesh Chaturthi",

        "2026-10-02": "Gandhi Jayanti",
        "2026-10-20": "Dussehra / Vijayadashami",

        "2026-11-08": "Diwali / Deepavali",

        "2026-12-25": "Christmas Day",
    }

    # ------------------------------------------------
    # EMPLOYEE LEAVES
    # ------------------------------------------------

    leaves = Leave.objects.filter(
        employee=employee
    ).order_by("start_date")

    # ------------------------------------------------
    # CREATE CALENDAR
    # Monday = 0
    # Sunday = 6
    # ------------------------------------------------

    first_day = date(year, month, 1)

    first_weekday = first_day.weekday()

    days_in_month = monthrange(year, month)[1]

    weeks = []
    week = []

    # Empty cells before first day
    for _ in range(first_weekday):
        week.append(None)

    # Add actual days
    for day_number in range(1, days_in_month + 1):

        current_date = date(
            year,
            month,
            day_number
        )

        date_key = current_date.strftime("%Y-%m-%d")

        day_leaves = leaves.filter(
            start_date__lte=current_date,
            end_date__gte=current_date
        )

        day_data = {
            "date": current_date,
            "holiday": holidays.get(date_key),
            "is_weekend": current_date.weekday() >= 5,
            "leaves": day_leaves,
            "is_today": current_date == today,
        }

        week.append(day_data)

        # Complete week
        if len(week) == 7:
            weeks.append(week)
            week = []

    # Remaining cells
    if week:
        while len(week) < 7:
            week.append(None)

        weeks.append(week)

    # Previous month
    if month == 1:
        previous_year = year - 1
        previous_month = 12
    else:
        previous_year = year
        previous_month = month - 1

    # Next month
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    return render(
        request,
        "leave_calendar.html",
        {
            "employee": employee,
            "weeks": weeks,

            "year": year,
            "month": month,

            "month_name": first_day.strftime("%B"),

            "previous_year": previous_year,
            "previous_month": previous_month,

            "next_year": next_year,
            "next_month": next_month,

            "is_employee": True,
        }
    )