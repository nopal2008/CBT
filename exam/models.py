from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils.text import slugify
from datetime import timedelta
import secrets
import string

# Custom User Model untuk extended functionality

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members'  # bisa dipakai dari Department untuk menghitung jumlah siswa
    )
    
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'teacher'},
        related_name='members'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    credits = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# exam/models.py - update model Exam
class Exam(models.Model):
    EXAM_TYPES = (
        ('quiz', 'Quiz'),
        ('midterm', 'Midterm Examination'),
        ('final', 'Final Examination'),
        ('practice', 'Practice Test'),
        ('assignment', 'Assignment'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    # Basic Information
    exam_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=False, null=True, blank=True)
    title = models.CharField(max_length=200)
    max_score = models.IntegerField(default=100)
    description = models.TextField()
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='quiz')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timing
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    result_publish_time = models.DateTimeField(blank=True, null=True)
    
    # Token System
    access_token = models.CharField(
        max_length=6,
        unique=True,
        blank=True,
        null=True,
        help_text="6-digit exam access token"
    )
    token_expiry = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Token expiry time (optional)"
    )
    
    # Settings
    passing_score = models.IntegerField(default=60, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_attempts = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    shuffle_questions = models.BooleanField(default=True)
    shuffle_choices = models.BooleanField(default=True)
    show_result_immediately = models.BooleanField(default=False)
    allow_back_navigation = models.BooleanField(default=True)
    require_webcam = models.BooleanField(default=False)
    require_microphone = models.BooleanField(default=False)
    enable_proctoring = models.BooleanField(default=False)
    
    # Relations
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='exam_subjects')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_exams', limit_choices_to={'user_type__in': ['admin', 'teacher']})
    allowed_departments = models.ManyToManyField(Department, blank=True, related_name='allowed_exams')
    allowed_users = models.ManyToManyField(CustomUser, blank=True, related_name='allowed_exams')
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['exam_id']),
            models.Index(fields=['status']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['access_token']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_exam_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.exam_id:
            self.exam_id = uuid.uuid4()
        
        # Auto-generate token if not provided and exam is published
        if not self.access_token and self.status == 'published':
            self.generate_token()
        
        super().save(*args, **kwargs)
    
    def generate_token(self):
        """Generate 6-digit random token"""
        import random
        import string
        
        while True:
            # Generate 6-digit alphanumeric token (uppercase letters + digits)
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Check if token already exists
            if not Exam.objects.filter(access_token=token).exists():
                self.access_token = token
                break
        
        return token

    def is_token_valid(self):
        """Check if token is still valid"""
        if not self.access_token:
            return False
        
        if self.token_expiry and timezone.now() > self.token_expiry:
            return False
            
        return True
    
    @property
    def is_available(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == 'published'

class QuestionBank(models.Model):
    DIFFICULTY_LEVELS = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        related_name='questionbank_subjects'
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type__in': ['admin', 'teacher']}
    )
    is_shared = models.BooleanField(default=False)

    # ✅ tambahkan field difficulty di sini
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_LEVELS,
        default='medium'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPES = (
        ('MC', 'Multiple Choice - Single Answer'),
        ('MCA', 'Multiple Choice - Multiple Answers'),
        ('TF', 'True/False'),
        ('FB', 'Fill in the Blank'),
        ('ESS', 'Essay'),
        ('MAT', 'Matching'),
        ('ORD', 'Ordering'),
    )
    
    # Basic Information
    question_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)
    text = models.TextField()
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    
    # Settings
    points = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    difficulty = models.CharField(max_length=10, choices=QuestionBank.DIFFICULTY_LEVELS, default='medium')
    is_active = models.BooleanField(default=True)
    
    # Media
    image = models.ImageField(upload_to='questions/images/', blank=True, null=True)
    audio = models.FileField(upload_to='questions/audio/', blank=True, null=True)
    video = models.FileField(upload_to='questions/video/', blank=True, null=True)
    
    # Relations
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type__in': ['admin', 'teacher']})
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.text[:50]}... ({self.get_question_type_display()})"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    image = models.ImageField(upload_to='choices/images/', blank=True, null=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.text[:50]}... ({'Correct' if self.is_correct else 'Incorrect'})"

class ExamSession(models.Model):
    SESSION_STATUS = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('submitted', 'Submitted'),
        ('timeout', 'Timeout'),
        ('terminated', 'Terminated by Admin'),
    )

    # === Basic Info ===
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='exam_sessions')

    # === Timing ===
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")

    # === Results ===
    score = models.FloatField(
        blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    total_questions = models.IntegerField(default=0)
    answered_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)

    # === Status ===
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='in_progress')
    is_completed = models.BooleanField(default=False)
    attempt_number = models.IntegerField(default=1)

    # === Security ===
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        unique_together = ['exam', 'user', 'attempt_number']
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} (Attempt {self.attempt_number})"

    # === Properties ===
    @property
    def completed(self):
        """True jika end_time sudah lewat, atau is_completed = True"""
        if self.end_time:
            return timezone.now() > self.end_time or self.is_completed
        return self.is_completed

    @property
    def is_ongoing(self):
        """True jika waktu sekarang di antara start_time dan end_time"""
        now = timezone.now()
        return self.end_time and self.start_time <= now <= self.end_time and not self.is_completed

    @property
    def is_upcoming(self):
        """True jika belum dimulai"""
        return timezone.now() < self.start_time

    @property
    def time_until_start(self):
        """Berapa lama lagi sebelum exam dimulai"""
        if self.is_upcoming:
            return self.start_time - timezone.now()
        return None

    @property
    def time_remaining(self):
        """Sisa waktu exam (kalau sedang berlangsung)"""
        if self.is_ongoing and self.end_time:
            return self.end_time - timezone.now()
        return None

    @property
    def is_passed(self):
        """True jika skor lebih tinggi dari passing score"""
        return self.score >= self.exam.passing_score if self.score is not None else False

    # === Methods ===
    def calculate_score(self):
        """Hitung skor berdasarkan jawaban yang sudah disimpan"""
        if not self.is_completed:
            return None

        total_points = sum(q.points for q in self.exam.questions.all())
        earned_points = sum(
            a.points_earned for a in self.user_answers.all()
            if a.points_earned is not None
        )

        if total_points > 0:
            self.score = (earned_points / total_points) * 100
        else:
            self.score = 0
        self.save(update_fields=['score'])
        return self.score
class UserAnswer(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # For multiple choice
    selected_choices = models.ManyToManyField(Choice, blank=True)
    
    # For text-based answers
    text_answer = models.TextField(blank=True, null=True)
    
    # For matching/ordering types
    matching_data = models.JSONField(blank=True, null=True)
    
    # Scoring
    is_correct = models.BooleanField(blank=True, null=True)
    points_earned = models.FloatField(blank=True, null=True)
    evaluated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, limit_choices_to={'user_type__in': ['admin', 'teacher']})
    evaluated_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    answered_at = models.DateTimeField(auto_now_add=True)
    time_spent = models.IntegerField(default=0, help_text="Time spent on this question in seconds")
    
    class Meta:
        unique_together = ['session', 'question']
    
    def __str__(self):
        return f"{self.session.user.username} - {self.question.text[:30]}"

class ProctoringEvent(models.Model):
    EVENT_TYPES = (
        ('tab_switch', 'Tab Switch Detected'),
        ('fullscreen_exit', 'Fullscreen Exit'),
        ('multiple_faces', 'Multiple Faces Detected'),
        ('no_face', 'No Face Detected'),
        ('voice_detected', 'Voice Detected'),
        ('mobile_detected', 'Mobile Device Detected'),
        ('system_check', 'System Check Failed'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='proctoring_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    description = models.TextField()
    screenshot = models.ImageField(upload_to='proctoring/screenshots/', blank=True, null=True)
    recorded_video = models.FileField(upload_to='proctoring/videos/', blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.session} - {self.get_event_type_display()}"

class Certificate(models.Model):
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.OneToOneField(ExamSession, on_delete=models.CASCADE, related_name='certificate')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    download_count = models.IntegerField(default=0)
    verification_url = models.URLField(blank=True)
    
    def __str__(self):
        return f"Certificate - {self.user.username} - {self.exam.title}"

class SystemLog(models.Model):
    LOG_LEVELS = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True)
    level = models.CharField(max_length=10, choices=LOG_LEVELS, default='info')
    action = models.CharField(max_length=200)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_level_display()} - {self.action}"

# Signal handlers untuk automation
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ExamSession)
def update_exam_session_stats(sender, instance, **kwargs):
    if instance.is_completed and instance.status == 'completed':
        # Hindari rekursi post_save dengan update langsung ke DB
        answered_count = instance.user_answers.count()
        correct_count = instance.user_answers.filter(is_correct=True).count()
        wrong_count = answered_count - correct_count

        # Hitung skor dari jawaban yang tersedia
        total_points = sum(q.points for q in instance.exam.questions.all())
        earned_points = 0
        for answer in instance.user_answers.select_related('question'):
            # Kalau poin manual ada, pakai itu; fallback ke nilai default per soal
            if answer.points_earned is not None:
                earned_points += answer.points_earned
            elif answer.is_correct:
                earned_points += answer.question.points

        score = (earned_points / total_points) * 100 if total_points > 0 else 0

        ExamSession.objects.filter(pk=instance.pk).update(
            answered_questions=answered_count,
            correct_answers=correct_count,
            wrong_answers=wrong_count,
            score=score,
        )

class StudentAnswer(models.Model):
    session = models.ForeignKey('ExamSession', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    selected_choice = models.ForeignKey('Choice', null=True, blank=True, on_delete=models.SET_NULL)
    
    # kalau short / essay / numeric answer
    text_answer = models.TextField(null=True, blank=True)

    is_correct = models.BooleanField(default=False)

    answered_at = models.DateTimeField(auto_now_add=True)

    def chosen_answer_text(self):
        # buat display jawaban lebih gampang di template
        if self.selected_choice:
            return self.selected_choice.text
        return self.text_answer or "—"

    def __str__(self):
        return f"{self.session.user} - {self.question.id}"

def get_exam_display(self):
    """Return exam title or 'All Exams' for global tokens"""
    if self.is_global:
        return "All Exams (Global)"
    return self.exam.title

class ExamToken(models.Model):
    TOKEN_STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    token = models.CharField(max_length=6, unique=True, db_index=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='tokens')
    status = models.CharField(max_length=10, choices=TOKEN_STATUS, default='active')
    is_global = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_count = models.IntegerField(default=0)
    max_usage = models.IntegerField(default=100)  # Maximum usage before expiry
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.token} - {self.exam.title}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at or self.used_count >= self.max_usage
    
    @property
    def time_remaining(self):
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - timezone.now()
    
    @classmethod
    def generate_token(cls):
        """Generate random 6-character alphanumeric token"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(6))
    
    @classmethod
    def create_token(cls, exam, created_by, duration_minutes=15, is_global=False, max_usage=100):
        """Create new token with automatic expiry"""
        token = cls.generate_token()
        expires_at = timezone.now() + timedelta(minutes=duration_minutes)
        
        return cls.objects.create(
            token=token,
            exam=exam,
            created_by=created_by,
            expires_at=expires_at,
            is_global=is_global,
            max_usage=max_usage
        )
    
    def renew_token(self, duration_minutes=15):
        """Renew token expiry time"""
        self.expires_at = timezone.now() + timedelta(minutes=duration_minutes)
        self.status = 'active'
        self.save()
    
    def revoke_token(self):
        """Manually revoke token"""
        self.status = 'revoked'
        self.save()

    def refresh_token(self):
        """Refresh expired token dengan durasi yang sama"""
        if self.status == 'expired':
            # Hitung durasi original
            original_duration = (self.expires_at - self.created_at).total_seconds() / 60

            # Set waktu baru
            self.expires_at = timezone.now() + timedelta(minutes=int(original_duration))
            self.status = 'active'
            self.used_count = 0  # Reset usage count
            self.save()
            return True

        return False
