from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegisterForm(UserCreationForm):
    """
    自定义注册表单：
    1. 继承自 Django 原生 UserCreationForm (自动处理密码加密/确认)
    2. 绑定我们要使用的 UserProfile 模型
    3. 额外让用户选 'role' (身份)
    """
    class Meta(UserCreationForm.Meta):
        model = UserProfile
        # 这里定义表单里要显示的字段
        fields = ('username', 'email', 'role') 
        
    # 我们可以给字段加一点样式类 (虽然我们在模板里也会手动写)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].label = "选择身份"
        self.fields['email'].required = True


    class RegisterForm(UserCreationForm):
        """
        自定义注册表单：支持 email, phone, department
        """
    email = forms.EmailField(label="电子邮箱", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label="联系电话", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(label="所属科室", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：放射科'}))
    
    class Meta(UserCreationForm.Meta):
        model = UserProfile
        # 在这里定义表单中显示的字段顺序
        fields = ('username', 'email', 'role', 'phone', 'department')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 统一给所有字段加 Bootstrap 样式
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})