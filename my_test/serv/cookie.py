from aiohttp import web
from .config import web_routes
from .jinjapage import jinjapage

from aiohttp import web
from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet



secret_key = Fernet.generate_key()
fernet = Fernet(secret_key)

'''学生的密码系统'''
passwords = {
    "101": "123",
    "102": "123",
    "103": "123",
    "104": "123",
    "105": "123",
    "106": "123",

    }
@web_routes.get("/login")
async def login_form_page(request):
    return jinjapage('templates/slogin.html')
    

@web_routes.post("/login")
async def handle_login(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    username = parmas.get("username")
    password = parmas.get("password")

    if passwords.get(username) != password:  # 比较密码
        raise web.HTTPFound('/login')  # 比对失败重新登录

    resp = web.HTTPFound('/')
    set_secure_cookie(resp, "session_id", username)
    raise resp

@web_routes.post("/logout")
async def handle_logout(request):
    resp = web.HTTPFound('/login')
    resp.del_cookie("session_id")
    raise resp

'''老师的密码系统'''
t_secret_key = Fernet.generate_key()
t_fernet = Fernet(t_secret_key)

t_passwords = {"101": "123"}

@web_routes.get('/tlogin')
async def tlogin_form_page(request):
    return jinjapage('templates/tlogin.html')

@web_routes.post('/tlogin')
async def handle_tlogin(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    username = parmas.get("username")
    password = parmas.get("password")

    if t_passwords.get(username) != password:  # 比较密码
        raise web.HTTPFound('/tlogin')  # 比对失败重新登录

    resp = web.HTTPFound('/t')
    set_secure_cookie(resp, "session_id", username)
    raise resp

@web_routes.post('/tlogout')    
async def handle_tlogout(request):
    resp = web.HTTPFound('/tlogin')
    resp.del_cookie("session_id")
    raise resp

'''加密cookie'''
def get_current_user(request):
    user_id = get_secure_cookie(request, "session_id")
    return user_id


def get_secure_cookie(request, name):
    value = request.cookies.get(name)
    if value is None:
        return None

    try:
        buffer = value.encode('utf-8')  # 将文本转换成字节串
        buffer = fernet.decrypt(buffer)
        secured_value = buffer.decode('utf-8')  # 将加密的字节串转换成文本
        return secured_value
    except InvalidToken:
        print("Cannot decrypt cookie value")
        return None


def set_secure_cookie(response, name, value, **kwargs):
    value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
    response.set_cookie(name, value, **kwargs)











