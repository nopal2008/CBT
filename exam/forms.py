from django import forms
from django.utils import timezone
import pytz
from .models import Question, Choice, Exam, QuestionBank, Subject, CustomUser
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question_type', 'text', 'explanation', 'points', 'difficulty',
            'is_active', 'image', 'audio', 'video', 'exam', 'question_bank'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Enter question text...'}),
            'explanation': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Explanation (optional)...'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'question_bank': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['exam'].empty_label = "Select Exam (Optional)"
        self.fields['question_bank'].empty_label = "Select Question Bank (Optional)"
        if user and user.user_type == 'teacher':
            self.fields['exam'].queryset = Exam.objects.filter(created_by=user)
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(created_by=user)
        else:
            self.fields['exam'].queryset = Exam.objects.all()
            self.fields['question_bank'].queryset = QuestionBank.objects.all()


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter choice text...'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.HiddenInput(),
        }


ChoiceFormSet = forms.inlineformset_factory(
    Question, Choice, form=ChoiceForm, extra=5, can_delete=True, max_num=5
)

class BulkQuestionForm(forms.Form):
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Question Bank (Optional)"
    )
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Exam (Optional)"
    )
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload CSV file with questions. Format: question_text,choice1,choice2,choice3,choice4,correct_answer_index',
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'accept': '.csv',
            'required': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BulkQuestionForm, self).__init__(*args, **kwargs)
        
        if user and user.user_type == 'teacher':
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(created_by=user)
            self.fields['exam'].queryset = Exam.objects.filter(created_by=user)
        else:
            # Jika bukan teacher, tampilkan semua (untuk admin)
            self.fields['question_bank'].queryset = QuestionBank.objects.all()
            self.fields['exam'].queryset = Exam.objects.all()

class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'description', 'subject', 'is_shared']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter question bank name...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter description (optional)...'
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'is_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(QuestionBankForm, self).__init__(*args, **kwargs)
        # Pastikan subject queryset ada
        self.fields['subject'].queryset = Subject.objects.all()
        
        # Untuk teacher, filter subjects berdasarkan department mereka jika ada
        if user and user.user_type == 'teacher':
            # Anda bisa menambahkan logika filter di sini jika diperlukan
            pass


class ExamForm(forms.ModelForm):
    """Form untuk Create & Edit Exam - TANPA Token Fields"""
    
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'exam_type', 'subject',
            'duration_minutes', 'start_time', 'end_time', 'result_publish_time',
            'passing_score', 'max_attempts', 'shuffle_questions', 'shuffle_choices',
            'show_result_immediately', 'allow_back_navigation', 'require_webcam',
            'require_microphone', 'enable_proctoring', 'allowed_departments',
            'allowed_users', 'status'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'placeholder': 'Enter exam title...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'rows': 4,
                'placeholder': 'Describe the exam purpose and content...'
            }),
            'exam_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'min': 1,
                'placeholder': '60'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition flatpickr-datetime',
                'placeholder': 'Select start date & time'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition flatpickr-datetime',
                'placeholder': 'Select end date & time'
            }),
            'result_publish_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition flatpickr-datetime',
                'placeholder': 'When to publish results (optional)'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'min': 0,
                'max': 100,
                'placeholder': '70'
            }),
            'max_attempts': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'min': 1,
                'placeholder': '1'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
            'allowed_departments': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'size': 5
            }),
            'allowed_users': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition',
                'size': 5
            }),
        }
        
        help_texts = {
            'duration_minutes': 'Time limit in minutes',
            'passing_score': 'Minimum score to pass (0-100)',
            'max_attempts': 'How many times students can take this exam',
            'allowed_departments': 'Leave empty to allow all departments',
            'allowed_users': 'Leave empty to allow all students',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set empty labels untuk select multiple
        self.fields['allowed_departments'].empty_label = None
        self.fields['allowed_users'].empty_label = None
        
    def clean(self):
        cleaned_data = super().clean()
        tz = pytz.timezone('Asia/Jakarta')

        def to_jakarta(dt):
            """
            Interpret user input as Asia/Jakarta local time.
            Django may already convert to the project TIME_ZONE (UTC), so we
            strip tzinfo and re-localize to Jakarta to avoid double shifting.
            """
            if not dt:
                return dt
            if dt.tzinfo == tz:
                return dt
            naive = dt.replace(tzinfo=None)
            return tz.localize(naive)

        start_time = to_jakarta(cleaned_data.get('start_time'))
        end_time = to_jakarta(cleaned_data.get('end_time'))
        result_publish_time = to_jakarta(cleaned_data.get('result_publish_time'))

        cleaned_data['start_time'] = start_time
        cleaned_data['end_time'] = end_time
        cleaned_data['result_publish_time'] = result_publish_time
        
        # Validasi: End time harus setelah start time
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        
        # Validasi: Result publish time harus setelah end time
        if end_time and result_publish_time:
            if result_publish_time <= end_time:
                raise forms.ValidationError({
                    'result_publish_time': 'Result publish time must be after exam end time'
                })
        
        return cleaned_data

    def save(self, commit=True):
        exam = super().save(commit=False)
        
        # ✅ TIDAK ada logic token lagi - token hanya di admin panel
        
        if commit:
            exam.save()
            self.save_m2m()
        return exam


class SimpleQuestionForm(forms.ModelForm):
    """Form sederhana untuk quick question creation"""
    class Meta:
        model = Question
        fields = ['question_type', 'text', 'points', 'difficulty']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter question text...'
            }),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 1
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }

class TrueFalseQuestionForm(forms.ModelForm):
    """Form khusus untuk soal True/False"""
    TRUE_FALSE_CHOICES = [
        (True, 'True'),
        (False, 'False'),
    ]
    
    correct_answer = forms.ChoiceField(
        choices=TRUE_FALSE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Correct Answer'
    )
    
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'points', 'difficulty']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter True/False question...'
            }),
            'explanation': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Explanation (optional)...'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 1
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }

class EssayQuestionForm(forms.ModelForm):
    """Form khusus untuk soal Essay"""
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'points', 'difficulty']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Enter essay question...'
            }),
            'explanation': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Expected answer or grading criteria...'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 5
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
        }

# Form untuk filter dan pencarian
class QuestionFilterForm(forms.Form):
    QUESTION_TYPE_CHOICES = [
        ('', 'All Types'),
        ('MC', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('FB', 'Fill in Blank'),
        ('ESS', 'Essay'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('', 'All Difficulties'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    question_type = forms.ChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    question_bank = forms.ModelChoiceField(
        queryset=QuestionBank.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Question Banks"
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search questions...'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(QuestionFilterForm, self).__init__(*args, **kwargs)
        
        if user and user.user_type == 'teacher':
            self.fields['question_bank'].queryset = QuestionBank.objects.filter(created_by=user)

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'user_type', 'is_active', 'is_staff']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'user_type': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
        }

class AdminCreateUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'password1', 'password2',
            'first_name', 'last_name', 'email',
            'phone', 'date_of_birth', 'profile_picture',
            'user_type', 'department'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg p-2'
            }),
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'user_type': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("⚠ Username sudah dipakai. Coba yang lain.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("⚠ Email ini sudah terdaftar.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password and len(password) < 8:
            raise forms.ValidationError("⚠ Password minimal 8 karakter.")
        return password

from django import forms
from django.core.exceptions import ValidationError
from exam.models import CustomUser

class AdminUserEditForm(forms.ModelForm):
    # Password opsional → user bisa biarkan kosong
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current password"})
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"})
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'profile_picture', 'user_type', 'is_active', 'is_staff'
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg bg-[#fafafa]'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = CustomUser.objects.filter(username=username).exclude(id=self.instance.id)
        if qs.exists():
            raise ValidationError("Username already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = CustomUser.objects.filter(email=email).exclude(id=self.instance.id)
            if qs.exists():
                raise ValidationError("Email already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 or p2:
            if p1 != p2:
                raise ValidationError("Passwords do not match.")
            if len(p1) < 8:
                raise ValidationError("Password must be at least 8 characters.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
