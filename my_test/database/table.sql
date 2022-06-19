DROP TABLE IF EXISTS student;
CREATE TABLE IF NOT EXISTS student  (
    sn       INTEGER,     --序号
    no       VARCHAR(10), --学号
    name     TEXT,        --姓名
    gender   CHAR(1),     --性别(F/M/O)
    academy  TEXT,        --学院
    grade    INTEGER,      --学级
    class    TEXT,         --班级 
    PRIMARY KEY(sn)
);

-- 给sn创建一个自增序号
CREATE SEQUENCE seq_student_sn 
    START 10000 INCREMENT 1 OWNED BY student.sn;
ALTER TABLE student ALTER sn 
    SET DEFAULT nextval('seq_student_sn');
-- 学号唯一
CREATE UNIQUE INDEX idx_student_no ON student(no);



DROP TABLE IF EXISTS course;
CREATE TABLE IF NOT EXISTS course  (
    sn       INTEGER,     --序号
    no       VARCHAR(10), --课程号
    name     TEXT,        --课程名称
    term     TEXT,        --学期
    credit   INTEGER,      --学分
    period   INTEGER,      --学时
    PRIMARY KEY(sn)
);

-- 给sn创建一个自增序号
CREATE SEQUENCE seq_course_sn 
    START 10000 INCREMENT 1 OWNED BY course.sn;
ALTER TABLE course ALTER sn 
    SET DEFAULT nextval('seq_course_sn');
-- 课程号唯一
CREATE UNIQUE INDEX idx_course_no ON course(no);



DROP TABLE IF EXISTS teacher;
CREATE TABLE IF NOT EXISTS teacher  (
    sn       INTEGER,     --序号
    name     TEXT,        --教师名称
    PRIMARY KEY(sn)
);

-- 给sn创建一个自增序号
CREATE SEQUENCE seq_teacher_sn 
    START 10000 INCREMENT 1 OWNED BY teacher.sn;
ALTER TABLE teacher ALTER sn 
    SET DEFAULT nextval('seq_teacher_sn');
-- 教师号唯一
CREATE UNIQUE INDEX idx_teacher_no ON teacher(no);



DROP TABLE IF EXISTS course_grade;
CREATE TABLE IF NOT EXISTS course_grade  (
    stu_sn INTEGER,      -- 学生序号
    cou_sn INTEGER,      -- 课程序号
    grade  NUMERIC(5,2), -- 最终成绩
    PRIMARY KEY(stu_sn, cou_sn)
);

ALTER TABLE course_grade 
    ADD CONSTRAINT stu_sn_fk FOREIGN KEY (stu_sn) REFERENCES student(sn);
ALTER TABLE course_grade 
    ADD CONSTRAINT cou_sn_fk FOREIGN KEY (cou_sn) REFERENCES course(sn);



DROP TABLE IF EXISTS course_freq;
CREATE TABLE IF NOT EXISTS course_freq  (
    cou_sn INTEGER,     -- 课程序号
    tea_sn INTEGER,     -- 教师序号
    loc    TEXT,        -- 地点
    time   TEXT,        -- 时间
    PRIMARY KEY(cou_sn, tea_sn)
);

ALTER TABLE course_freq
    ADD CONSTRAINT cou_sn_fk FOREIGN KEY (cou_sn) REFERENCES course(sn);
ALTER TABLE course_freq
    ADD CONSTRAINT tea_sn_fk FOREIGN KEY (tea_sn) REFERENCES teacher(sn);