from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ---------- Mentor ----------
class Mentor(db.Model):
    __tablename__ = "mentors"

    id = db.Column(db.Integer, primary_key=True)

    uname = db.Column(db.String(20), unique=True, nullable=False)  # login id
    fname = db.Column(db.String(100))                              # full name

    ugpg = db.Column(db.String(10))
    gender = db.Column(db.String(10))

    mobile = db.Column(db.String(50))
    email = db.Column(db.String(100))

    desig = db.Column(db.String(100))      # designation
    dname = db.Column(db.String(100))      # department full name
    dept = db.Column(db.String(20))        # short code like ENG

    password = db.Column(db.String(50))

class MentorsPcode(db.Model):
    __tablename__ = "mentorspcode"

    id = db.Column(db.BigInteger, primary_key=True)
    uname = db.Column(db.String(20))
    pcode = db.Column(db.Float)

class ProgramInfo(db.Model):
    __tablename__ = "program_info_all"

    pcode = db.Column(db.BigInteger, primary_key=True)
    pshort = db.Column(db.String(50))
    pname = db.Column(db.String(100))
    ptitle = db.Column(db.String(100))
    year = db.Column(db.String(4))

# ---------- Student ----------
class Student(db.Model):
    __tablename__ = "students_all"

    id = db.Column(db.Integer, primary_key=True)

    
    rollno = db.Column(db.String(20), unique=True, nullable=False)

    sname = db.Column(db.String(100))
    fname = db.Column(db.String(100))
    mname = db.Column(db.String(100))

    jyear = db.Column(db.Integer)
    caste = db.Column(db.String(20))

    pcode = db.Column(db.Integer)
    pshort = db.Column(db.String(100))
    aadharno = db.Column(db.String(20))

    profile_image = db.Column(db.Text)

    dob = db.Column(db.Date)
    gender = db.Column(db.String(10))

    currsem = db.Column(db.Integer)
    secl = db.Column(db.String(10))

    mobileno = db.Column(db.String(15))
    status = db.Column(db.String(20))
    year = db.Column(db.String(4))

# ---------- Semester Marks ----------
class SemesterMarks(db.Model):
    __tablename__ = "exam_registration_all"
    __table_args__ = {"extend_existing": True}   # ✅ THIS FIX

    id = db.Column(db.Integer, primary_key=True)

    
    rollno = db.Column(db.String(20), nullable=False)
    pcode = db.Column(db.Integer)

    scode = db.Column(db.String(20))
    secl = db.Column(db.String(10))
    tp = db.Column(db.String(10))
    part = db.Column(db.String(10))

    sem = db.Column(db.Integer)

    credits = db.Column(db.Integer)
    fcredits = db.Column(db.Integer)

    cia = db.Column(db.Integer)
    cia_abs = db.Column(db.Integer)

    see = db.Column(db.Integer)
    see2 = db.Column(db.Integer)

    istot = db.Column(db.Integer)

    semcode = db.Column(db.String(50))
    barcode = db.Column(db.String(50))

    ciapf = db.Column(db.String(1))
    seepf = db.Column(db.String(1))
    istotpf = db.Column(db.String(1))

    gp = db.Column(db.Numeric(4, 2))
    grade = db.Column(db.String(5))

    ord = db.Column(db.Integer)
    my = db.Column(db.Integer)
 
    attempt = db.Column(db.Integer)

    regsup = db.Column(db.String(10))
    smc = db.Column(db.String(10))
    reval = db.Column(db.String(10))

    pentry = db.Column(db.String(10))
    examid = db.Column(db.Integer)
    facid = db.Column(db.Integer)
    year = db.Column(db.String(4))


# ---------- Parent Meeting ----------
class ParentMeeting(db.Model):
    __tablename__ = "parent_meetings"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students_all.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    remarks = db.Column(db.Text)


class Subject(db.Model):
    __tablename__ = "subjects_all"

    sid = db.Column(db.Integer)
    sinc = db.Column(db.Integer)
    dept = db.Column(db.String(20))

    scode = db.Column(db.String(20), primary_key=True)
    stitle = db.Column(db.Text)

    pcode = db.Column(db.Integer)
    sem = db.Column(db.Integer)
    ord = db.Column(db.Integer)

    tp = db.Column(db.String(5))
    part = db.Column(db.Integer)

    sbatch = db.Column(db.Integer)
    credits = db.Column(db.Integer)

    my = db.Column(db.Integer)
    totmax = db.Column(db.Integer)
    ciamax = db.Column(db.Integer)
    seemax = db.Column(db.Integer)

    tstatus = db.Column(db.Integer)
    valcode = db.Column(db.Integer)
    facid = db.Column(db.Integer)
    omr = db.Column(db.Integer)
    year = db.Column(db.String(4))


