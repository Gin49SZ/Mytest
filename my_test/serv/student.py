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
@web_routes.get("/")
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
        

    return jinjapage('templates/list.html',
                     user=user,
                     items=items)


'''选课界面'''
@web_routes.get("/choosecourse")
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

    return jinjapage('templates/choosecourse.html',
                     items=items)

'''添加此课程到自己的已选课程'''
@web_routes.post("/action/choosecourse/addmycourse/{course_no}")
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
@web_routes.get("/mycourse")
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

    return jinjapage('templates/mycourse.html',
                     items=items)




'''删除已选择的课'''
@web_routes.post("/mycourse/delete/{stu_sn}/{cou_sn}")
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