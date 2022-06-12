from aiohttp import web
import jinja2
from pathlib import Path
from dblock import dblock
from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet
import psycopg
from jinjapage import jinjapage



home_path = str(Path(__file__).parent)
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(home_path))



'''---------------------------------------------------------------------------------------'''
'''设置cookie'''
secret_key = Fernet.generate_key()
fernet = Fernet(secret_key)

passwords = {
    "101": "123",
    "102": "123",
    "103": "123",
    "104": "123",
    "105": "123",
    "106": "123",

    }

async def login_form_page(request):
    template = jinja_env.get_template('slogin.html')
    return web.Response(text=template.render(),
                        content_type="text/html")


async def handle_login(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    username = parmas.get("username")
    password = parmas.get("password")

    if passwords.get(username) != password:  # 比较密码
        raise web.HTTPFound('/login')  # 比对失败重新登录

    resp = web.HTTPFound('/')
    set_secure_cookie(resp, "session_id", username)
    raise resp

async def handle_logout(request):
    resp = web.HTTPFound('/login')
    resp.del_cookie("session_id")
    raise resp


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
'''-------------------------------------------------------------------------------------------------'''



'''主界面'''
async def list_grade(request):
    user = get_current_user(request)
    if not user:
        raise web.HTTPFound('/login')
    with dblock() as db:
        db.execute('''
        SELECT s.name as student_name ,s.no as student_no ,s.class as student_class ,c.name as course_name, g.grade
        FROM course_grade as g
        INNER JOIN student as s ON g.stu_sn = s.sn
        INNER JOIN course as c  ON g.cou_sn = c.sn ;
        
        ''')
        items=[]
        for row in db:
            if row.grade != None:
                items.append(row)

    with dblock() as db2:
        db2.execute(f'''
        SELECT s.name as sn
        FROM  student as s
        WHERE s.sn = {user} ;
        ''')
        user = [row for row in db2] #注意此处的sn指的是学生姓名而非学号
        

    return jinjapage('list.html',
                     user=user,
                     items=items)

'''选课界面'''
async def list_course(request):
    user = get_current_user(request)

    with dblock() as db2:
        db2.execute(f'''
        SELECT g.cou_sn as sn
        FROM  course_grade as g
        WHERE g.stu_sn = {user} ;
        ''')
        stu_cou_sn = [row for row in db2]



    with dblock() as db:
        db.execute(f'''
        SELECT c.name as course_name ,c.sn as sn,c.no as course_no ,t.name as teacher_name ,f.time ,f.loc ,c.credit as course_credit 
        FROM course_freq as f 
        INNER JOIN course as c ON f.cou_sn = c.sn
        INNER JOIN teacher as t ON f.tea_sn = t.sn
        FULL OUTER JOIN course_grade as g ON f.cou_sn = g.cou_sn;        
        ''')
    
        items = [row for row in db]


        sim = []
        for i in stu_cou_sn:
            for j in items:
                if j.sn == i.sn:
                    sim.append(j)   

        for i in sim:
            items.remove(i)

    return jinjapage('choosecourse.html',
                     items=items)

'''添加此课程到自己的已选课程'''
def addmycourse(request):
    user = get_current_user(request)
    course_no = request.match_info.get("course_no")

    with dblock() as db:
        db.execute(f"""
        SELECT c.sn as sn
        FROM course as c
        WHERE c.no = '{course_no}';

        """)
        items = [row for row in db]
        sn = items[0]
    cousn = str(sn.sn)


    with psycopg.connect("dbname=examdb user=examdb") as conn:
        with conn.cursor() as cur:
            stmt = f'INSERT INTO course_grade (stu_sn, cou_sn )  VALUES ({user} ,{cousn} )'
            cur.execute(stmt)       
        conn.commit()


    return web.HTTPFound(location="/choosecourse")


'''个人选课界面'''
async def mycourse(request):
    user = get_current_user(request)
    if not user:
        raise web.HTTPFound('/login')
    with dblock() as db:
        db.execute(f'''
        SELECT s.sn as student_no ,s.class as student_class ,c.name as course_name ,g.stu_sn,g.cou_sn, g.grade
        FROM course_grade as g
        INNER JOIN student as s ON g.stu_sn = s.sn
        INNER JOIN course as c  ON g.cou_sn = c.sn ;        
        ''')
        items=[]
        for row in db:
            if row.student_no == int(user):
                
                items.append(row)      

    return jinjapage('mycourse.html',
                     items=items)




'''删除已选择的课'''
def delete_chosen_course(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")



    with psycopg.connect("dbname=examdb user=examdb") as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM course_grade
                WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
                """, dict(stu_sn=stu_sn, cou_sn=cou_sn))       
        conn.commit()

    return web.HTTPFound(location="/mycourse")




'''以上为学生界面'''
'''--------------------------------------------------------------------------------------------------------------------------------------------------'''
'''以下为教师界面'''


'''设置cookie'''
t_secret_key = Fernet.generate_key()
t_fernet = Fernet(t_secret_key)

t_passwords = {"101": "123"}

async def tlogin_form_page(request):
    template = jinja_env.get_template('tlogin.html')
    return web.Response(text=template.render(),
                        content_type="text/html")


async def handle_tlogin(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    username = parmas.get("username")
    password = parmas.get("password")

    if t_passwords.get(username) != password:  # 比较密码
        raise web.HTTPFound('/tlogin')  # 比对失败重新登录

    resp = web.HTTPFound('/t')
    set_secure_cookie(resp, "session_id", username)
    raise resp

async def handle_tlogout(request):
    resp = web.HTTPFound('/tlogin')
    resp.del_cookie("session_id")
    raise resp



'''-------------------------------------------------------------------------------------------------'''

'''主界面'''
async def tlist_grade(request):
    user = get_current_user(request)
    if not user:
        raise web.HTTPFound('/tlogin')
    with dblock() as db:
        db.execute('''
        SELECT s.name as student_name ,c.sn as cou_sn ,s.no as student_no ,s.class as student_class ,c.name as course_name, g.grade ,s.sn as stu_sn
        FROM course_grade as g
        INNER JOIN student as s ON g.stu_sn = s.sn
        INNER JOIN course as c  ON g.cou_sn = c.sn ;
        
        ''')
        items=[row for row in db]

    with dblock() as db2:
        db2.execute(f'''
        SELECT f.cou_sn as sn
        FROM  course_freq as f
        WHERE f.tea_sn = {user} ;
        ''')
        tea_cou = [row for row in db2]

    drop_items=[]
    for i in tea_cou:
        for j in items:
            if i.sn == j.cou_sn:
                drop_items.append(j)


    with dblock() as db3:
        db3.execute(f'''
        SELECT t.name as tn
        FROM  teacher as t
        WHERE t.sn = {user} ;
        ''')

        user = [row for row in db3]

    return jinjapage('tlist.html',
                     items=drop_items,
                     user=user)


'''修改成绩'''   
async def edit_grade(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")
    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    params = await request.post()
    grade = params.get("grade")

    try:
        stu_sn = int(stu_sn)
        cou_sn = int(cou_sn)
        grade = float(grade)
    except ValueError:
        return web.HTTPBadRequest(text="invalid value")

    with dblock() as db:
        db.execute("""
        UPDATE course_grade SET grade=%(grade)s
        WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn, grade=grade))

    return web.HTTPFound(location="/t") 

'''修改成绩页面'''
async def editor(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")
    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    with dblock() as db:
        db.execute("""
        SELECT grade FROM course_grade
            WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s;
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn))

        record = db.fetchone()

    if record is None:
        return web.HTTPNotFound(text=f"no such grade: stu_sn={stu_sn}, cou_sn={cou_sn}")

    return jinjapage('editgrade.html',
                        stu_sn=stu_sn,
                        cou_sn=cou_sn,
                        grade=record.grade)



'''录入成绩'''
async def entering_grade(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")
    if stu_sn is None or cou_sn is None:
        return web.HTTPBadRequest(text="stu_sn, cou_sn, must be required")

    params = await request.post()
    grade = params.get("grade")

    try:
        stu_sn = int(stu_sn)
        cou_sn = int(cou_sn)
        grade = float(grade)
    except ValueError:
        return web.HTTPBadRequest(text="invalid value")

    with dblock() as db:
        db.execute("""
        UPDATE course_grade SET grade=%(grade)s
        WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn, grade=grade))

    return web.HTTPFound(location=f"/t/classgover/inputresult/{cou_sn}") 


'''删除未录入成绩的学生'''
def delete_student(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")



    with psycopg.connect("dbname=examdb user=examdb") as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM course_grade
                WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
                """, dict(stu_sn=stu_sn, cou_sn=cou_sn))       
        conn.commit()

    return web.HTTPFound(location=f"/t/classgover/inputresult/{cou_sn}")



'''取消学生成绩'''
def cancel_grade(request):
    stu_sn = request.match_info.get("stu_sn")
    cou_sn = request.match_info.get("cou_sn")

    with dblock() as db:
        db.execute("""
        UPDATE course_grade SET grade=null
        WHERE stu_sn = %(stu_sn)s AND cou_sn = %(cou_sn)s
        """, dict(stu_sn=stu_sn, cou_sn=cou_sn))


    return web.HTTPFound(location="/t")


'''班级管理页面'''
async def classgover(request):
    user = get_current_user(request)
    if not user:
        raise web.HTTPFound('/t')
    with dblock() as db:
        db.execute(f"""
         SELECT c.name as course_name ,c.sn as course_sn ,c.term as course_term
         FROM  course_freq
         INNER JOIN teacher as t ON course_freq.tea_sn = t.sn
         INNER JOIN course as c  ON course_freq.cou_sn = c.sn  
         WHERE t.sn = {user} ;
         """)
        
        items=[row for row in db]    

    return jinjapage('classgover.html',
                        items=items)

'''录入成绩页面'''
async def inputresult(request):
    course_sn = request.match_info.get("course_sn")
    

    with dblock() as db:
        db.execute(f"""
         SELECT s.name as student_name ,s.no as student_no ,s.sn as stu_sn ,c.sn as cou_sn ,s.class as student_class ,c.name as course_name ,g.grade
         FROM course_grade as g
         INNER JOIN student as s ON g.stu_sn = s.sn
         INNER JOIN course as c  ON g.cou_sn = c.sn  
         WHERE c.sn = {course_sn}
         """)
        items=[row for row in db]   
    
    return jinjapage('inputresult.html',
                        items=items)










app = web.Application()
app.add_routes([
    web.get('/', list_grade),
    web.get('/choosecourse',list_course),

    web.get('/login', login_form_page),
    web.post('/login', handle_login),
    web.post('/logout', handle_logout),

    web.post('/action/choosecourse/addmycourse/{course_no}',addmycourse),
    web.get('/mycourse',mycourse),

    web.post('/mycourse/delete/{stu_sn}/{cou_sn}', delete_chosen_course),


#学生界面↑---------------------------------------------------------------------------------------------------教师界面↓#
    web.get('/t', tlist_grade),

    web.get('/tlogin', tlogin_form_page),
    web.post('/tlogin', handle_tlogin),
    web.post('/tlogout', handle_tlogout),
    
    web.get('/t/edit/{stu_sn}/{cou_sn}', editor),
    web.post('/t/action/edit/{stu_sn}/{cou_sn}', edit_grade),
    
    web.post('/t/action/entering/{stu_sn}/{cou_sn}', entering_grade),
    web.post('/t/action/deletestu/{stu_sn}/{cou_sn}',delete_student),

    web.post('/t/action/cancelgrade/{stu_sn}/{cou_sn}',cancel_grade),

    web.get('/t/classgover', classgover),
    web.get('/t/classgover/inputresult/{course_sn}', inputresult),
    web.static("/", Path.cwd() / "static"),

])


if __name__ == "__main__":
    web.run_app(app, port=8080)


