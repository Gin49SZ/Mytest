from aiohttp import web
from .config import web_routes
from .jinjapage import jinjapage,get_location
from .dblock import dblock

from aiohttp import web
from pathlib import Path
from cryptography.fernet import InvalidToken
from cryptography.fernet import Fernet
import psycopg
from .cookie import *

'''主界面'''
@web_routes.get("/t")
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

    return jinjapage('templates/tlist.html',
                     items=drop_items,
                     user=user)


'''修改成绩'''   
@web_routes.post("/t/action/edit/{stu_sn}/{cou_sn}")
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
@web_routes.get("/t/edit/{stu_sn}/{cou_sn}")
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

    return jinjapage('templates/editgrade.html',
                        stu_sn=stu_sn,
                        cou_sn=cou_sn,
                        grade=record.grade)



'''录入成绩'''
@web_routes.post("/t/action/entering/{stu_sn}/{cou_sn}")
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
@web_routes.post("/t/action/deletestu/{stu_sn}/{cou_sn}")
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
@web_routes.post("/t/action/cancelgrade/{stu_sn}/{cou_sn}")
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
@web_routes.get("/t/classgover")
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

    return jinjapage('templates/classgover.html',
                        items=items)

'''录入成绩页面'''
@web_routes.get("/t/classgover/inputresult/{course_sn}")
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
    
    return jinjapage('templates/inputresult.html',
                        items=items)



'''课程查询'''
@web_routes.get("/t/courselect")
async def course_select_view(request):
    user = get_current_user(request)
    if not user:
        raise web.HTTPFound('/t')
    return jinjapage('templates/courselect.html')



@web_routes.post("/t/action/courselect")
@web_routes.get("/t/courselect/result")
async def course_select(request):
    parmas = await request.post()  # 获取POST请求的表单字段数据
    term = str(parmas.get("term"))
    course = str(parmas.get("course"))
    print(term,course)
    with dblock() as db:
        db.execute("""
        SELECT c.sn as course_sn
        FROM course  as c
        WHERE c.term = %(term)s AND c.name = %(course)s
        """, dict(term=term, course=course))
        items=[row for row in db]
    sn = items[0].course_sn
    if sn == None:
        raise web.HTTPFound('/t/courselect')
    with dblock() as db2:
        db2.execute(f"""
        SELECT s.name as stu_name ,s.no as stu_no ,g.grade
        FROM course_grade as g
        INNER JOIN student as s ON g.stu_sn = s.sn
        INNER JOIN course as c  ON g.cou_sn = c.sn  
        WHERE c.sn = {sn}
        """)
        results=[row for row in db2]
    print(results)
    return jinjapage('templates/courselectResult.html',items=results)
