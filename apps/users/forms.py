from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    """
    自定义注册表单：适配 AdminLTE 风格
    包含字段：username, email, role, phone, department
    """
    # 显式定义字段，添加 Bootstrap 的 form-control 类
    email = forms.EmailField(
        label="电子邮箱", 
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'})
    )
    role = forms.ChoiceField(
        label="选择身份",
        choices=UserProfile.ROLE_CHOICES, # 确保你的 Model 里定义了 ROLE_CHOICES，如果没有则手动写 choices=(('labeler','标注员'), ('hospital','医生'))
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label="联系电话", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '可选'})
    )
    department = forms.CharField(
        label="所属科室", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：放射科'})
    )

    class Meta(UserCreationForm.Meta):
        model = UserProfile
        # 定义字段顺序，这将决定它们在 HTML 中的渲染顺序
        fields = ('username', 'email', 'role', 'phone', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 兜底操作：确保所有字段都有 form-control 类（适配 Bootstrap 4）
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                field.widget.attrs['class'] = existing_classes + ' form-control'
            
            # 给用户名输入框也加个 placeholder
            if field_name == 'username':
                field.widget.attrs['placeholder'] = '请输入用户名'