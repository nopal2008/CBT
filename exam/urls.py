from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

app_name = 'exam'

urlpatterns = [
    # ===== AUTHENTICATION & REDIRECT =====
    path('', views.login_redirect, name='home'),
    
    path('login/', auth_views.LoginView.as_view(template_name='exam/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('login-redirect/', views.login_redirect, name='login_redirect'),

    # ===== STUDENT ROUTES =====
    path('student/my-exams/', views.my_exams, name='my_exams'),
    path('student/exam/<int:exam_id>/', views.take_exam, name='take_exam'),

    path('exam/<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('exams/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),

    path('results/<int:session_id>/', views.exam_results, name='exam_results'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/exam-token/', views.exam_token_access, name='exam_token_access'),
    path('api/validate-token/', views.validate_exam_token, name='validate_exam_token'),
    path('student/validate-token/', views.validate_exam_token, name='validate_exam_token'),
    path('student/exam/token/<str:token>/', views.access_exam_with_token, name='access_exam_with_token'),
    path('student/results/', views.student_results, name='student_results'),
    path('student/results/<int:session_id>/', views.student_result_detail, name='student_result_detail'),
    path('exam/<int:exam_id>/details/', views.student_exam_details, name='exam_details'),
    path('exam/<int:exam_id>/', views.student_exam_details, name='exam_details_short'),
     # Error pages
    path('exam/not-available/', views.exam_not_available, name='exam_not_available'),
    path('exam/ended/', views.exam_ended, name='exam_ended'),
    path('exam/access-denied/', views.exam_access_denied, name='exam_access_denied'),

    
  # ===== TEACHER ROUTES =====
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/questions/', views.teacher_questions, name='teacher_questions'),
    path('teacher/questions/add/', views.add_question, name='add_question'),
    path('teacher/questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('teacher/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('teacher/questions/bulk-upload/', views.bulk_upload_questions, name='bulk_upload_questions'),
    path('teacher/questions/sample-csv/', views.download_question_template, name='download_question_template'),
    path('teacher/question-banks/create/', views.create_question_bank, name='create_question_bank'),
    path('teacher/question-banks/<int:bank_id>/', views.question_bank_detail, name='question_bank_detail'),

    # ✅ EXAM CRUD - NEW
    path('teacher/exams/', views.exam_list, name='exam_list'),  
    path('teacher/exams/create/', views.create_exam, name='create_exam'),
    path('teacher/exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('teacher/exams/<int:exam_id>/edit/', views.edit_exam, name='edit_exam'),
    path('teacher/exams/<int:exam_id>/delete/', views.delete_exam, name='delete_exam'),

    # ===== ADMIN ROUTES =====
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('stats/', views.admin_stats, name='admin_stats'),
    path('admin/tokens/', views.token_management, name='token_management'),
    path('admin/exams/', views.admin_exam_monitor, name='admin_exam_monitor'),
    path('admin/exams/<int:exam_id>/', views.admin_exam_detail, name='admin_exam_detail'),
    path('api/validate-token/', views.validate_exam_token, name='validate_exam_token'),
    path('api/active-tokens/', views.get_active_tokens, name='get_active_tokens'),
    path('admin/tokens/rotate/', views.auto_rotate_tokens, name='auto_rotate_tokens'),
    
   # ========== ADMIN USER MANAGEMENT ==========
    path('admin/users/', views.user_management_list, name='admin_user_list'),
    path('admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/<int:user_id>/view/', views.admin_user_detail, name='admin_user_view'),
    path('admin/users/<int:user_id>/toggle/', views.user_management_toggle, name='admin_user_toggle'),
    path('admin/users/<int:user_id>/delete/', views.user_management_delete, name='admin_user_delete'),
    path('admin/users/download-template/', views.download_user_template, name='admin_user_download'),

    # token management actions
    path('admin/tokens/refresh/<int:token_id>/', views.refresh_token, name='refresh_token'),
    path('admin/tokens/export/', views.export_tokens, name='export_tokens'),
    path('admin/tokens/bulk-generate/', views.bulk_generate_tokens, name='bulk_generate_tokens'),

    # ===== FALLBACK REDIRECTS =====
    path('teacher/', lambda request: redirect('exam:teacher_dashboard')),
    path('student/', lambda request: redirect('exam:my-exams')),
    path('admin/', lambda request: redirect('exam:admin_dashboard')),


]
