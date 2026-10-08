from flask import Blueprint, render_template, request, session, redirect, jsonify, flash
from models import Student, SemesterMarks, ParentMeeting, db, Subject, Mentor
import random
import string
from datetime import date

mentor = Blueprint("mentor", __name__)

# ---------- Mentor Login ----------
@mentor.route("/login", methods=["GET", "POST"])
def mentor_login():
    if request.method == "POST":
        uname = request.form["username"]
        password = request.form["password"]
        login_type = request.form.get("login_type", "mentor")  # Default mentor

        mentor_user = Mentor.query.filter_by(uname=uname).first()

        # ✅ FIX: use mentor_user everywhere (not mentor)
        if mentor_user and mentor_user.password == password:

            # ---------- Admin Login ----------
            if login_type == "admin":
                if mentor_user.dept == "Admin":
                    session["mentor_id"] = mentor_user.id
                    session["is_admin"] = True
                    return redirect("/mentor/admin/dashboard")
                else:
                    flash("Access Denied: You are not authorized as an Admin.")
                    return redirect("/mentor/login")

            # ---------- Normal Mentor Login ----------
            session["mentor_id"] = mentor_user.id

            from models import MentorsPcode
            pcodes_records = MentorsPcode.query.filter_by(uname=mentor_user.uname).all()

            session["mentor_pcodes"] = [int(p.pcode) for p in pcodes_records] if pcodes_records else []
            session["is_admin"] = False

            return redirect("/mentor/dashboard")

        elif login_type == "student":
            student_user = Student.query.filter_by(rollno=uname).first()
            if student_user and password == student_user.rollno:
                session["student_id"] = student_user.id
                session["student_rollno"] = student_user.rollno
                session["is_admin"] = False
                return redirect(f"/mentor/student/{student_user.rollno}")
            flash("Invalid student credentials")
            return redirect("/mentor/login")

        flash("Invalid mentor credentials")

    return render_template("login.html")


# ---------- Logout ----------
@mentor.route("/logout")
def mentor_logout():
    session.clear()
    return redirect("/mentor/login")
# ---------- Admin Dashboard & Search ----------
@mentor.route("/admin/dashboard")
def admin_dashboard():
    if "mentor_id" not in session or not session.get("is_admin"):
        flash("Please login as Admin to access this page.")
        return redirect("/mentor/login")
    
    from models import ProgramInfo
    programs = ProgramInfo.query.all()
    
    return render_template("admin_dashboard.html", programs=programs)

@mentor.route("/admin/program/<int:pcode>")
def admin_program_dashboard(pcode):
    if "mentor_id" not in session or not session.get("is_admin"):
        flash("Please login as Admin to access this page.")
        return redirect("/mentor/login")

    from models import ProgramInfo, SemesterMarks, Subject, Student, db

    program_info = ProgramInfo.query.filter_by(pcode=pcode).first()
    if not program_info:
        flash("Program not found.")
        return redirect("/mentor/admin/dashboard")

    # Get all semester marks records for this pcode
    all_marks_raw = db.session.query(SemesterMarks, Subject.stitle).outerjoin(
        Subject, SemesterMarks.scode == Subject.scode
    ).filter(
        SemesterMarks.pcode == pcode
    ).order_by(SemesterMarks.attempt.desc()).all()

    student_stats = {}
    
    for mark, stitle in all_marks_raw:
        rno = mark.rollno
        scode = mark.scode
        if rno not in student_stats:
            student_stats[rno] = {}
            
        if scode not in student_stats[rno]:
            # Ordered by attempt desc, logic same as mentor dashboard
            student_stats[rno][scode] = {
                'is_pass': False, 
                'has_f': False,
                'sem': mark.sem,
                'stitle': stitle or 'Unknown Subject'
            }
            
        istotpf = mark.istotpf.strip().upper() if mark.istotpf else ''
        if istotpf == 'P':
            student_stats[rno][scode]['is_pass'] = True
        elif istotpf == 'F':
            student_stats[rno][scode]['has_f'] = True

    students_data = Student.query.filter_by(pcode=pcode).all()
    student_names = {s.rollno: s.sname for s in students_data}
    inactive_students = {s.rollno for s in students_data if str(s.status) == '1'}
    
    inactive_students_count = len([s for s in students_data if str(s.status) == '1'])
    
    total_students = 0
    backlog_counts = {1: [], 2: [], 3: [], 4: [], 5: [], '>5': []}
    
    passed_students_list = []
    backlog_students_list = []
    
    students_with_backlogs = 0

    for rno, subjects in student_stats.items():
        if rno in inactive_students:
            continue
            
        total_students += 1
        has_backlog = False
        student_backlog_count = 0
        
        for scode, status in subjects.items():
            if status['has_f'] and not status['is_pass']:
                has_backlog = True
                student_backlog_count += 1
                
        sname = student_names.get(rno, "Unknown")
        if has_backlog:
            students_with_backlogs += 1
            backlog_students_list.append({'rollno': rno, 'sname': sname, 'backlog_count': student_backlog_count})
            
            if student_backlog_count == 1:
                backlog_counts[1].append({'rollno': rno, 'sname': sname, 'backlog_count': 1})
            elif student_backlog_count == 2:
                backlog_counts[2].append({'rollno': rno, 'sname': sname, 'backlog_count': 2})
            elif student_backlog_count == 3:
                backlog_counts[3].append({'rollno': rno, 'sname': sname, 'backlog_count': 3})
            elif student_backlog_count == 4:
                backlog_counts[4].append({'rollno': rno, 'sname': sname, 'backlog_count': 4})
            elif student_backlog_count == 5:
                backlog_counts[5].append({'rollno': rno, 'sname': sname, 'backlog_count': 5})
            elif student_backlog_count > 5:
                backlog_counts['>5'].append({'rollno': rno, 'sname': sname, 'backlog_count': student_backlog_count})
        else:
            passed_students_list.append({'rollno': rno, 'sname': sname, 'backlog_count': 0})
            
    students_passed = total_students - students_with_backlogs
    
    stats = {
        'total_students': total_students,
        'students_passed': students_passed,
        'students_with_backlogs': students_with_backlogs,
        'passed_students_list': passed_students_list,
        'backlog_students_list': backlog_students_list,
        'backlog_counts': backlog_counts,
        'inactive_students_count': inactive_students_count
    }

    return render_template("admin_program_dashboard.html", program_info=program_info, stats=stats)

@mentor.route("/admin/overall")
def admin_overall_dashboard():
    if "mentor_id" not in session or not session.get("is_admin"):
        flash("Please login as Admin to access this page.")
        return redirect("/mentor/login")

    from models import SemesterMarks, Subject, Student, db

    class DummyProgramInfo:
        pshort = "Overall"
        
    program_info = DummyProgramInfo()

    # Get all semester marks records for all pcodes
    all_marks_raw = db.session.query(SemesterMarks, Subject.stitle).outerjoin(
        Subject, SemesterMarks.scode == Subject.scode
    ).order_by(SemesterMarks.attempt.desc()).all()

    student_stats = {}
    
    for mark, stitle in all_marks_raw:
        rno = mark.rollno
        scode = mark.scode
        if rno not in student_stats:
            student_stats[rno] = {}
            
        if scode not in student_stats[rno]:
            # Ordered by attempt desc, logic same as mentor dashboard
            student_stats[rno][scode] = {
                'is_pass': False, 
                'has_f': False,
                'sem': mark.sem,
                'stitle': stitle or 'Unknown Subject'
            }
            
        istotpf = mark.istotpf.strip().upper() if mark.istotpf else ''
        if istotpf == 'P':
            student_stats[rno][scode]['is_pass'] = True
        elif istotpf == 'F':
            student_stats[rno][scode]['has_f'] = True

    students_data = Student.query.all()
    student_names = {s.rollno: s.sname for s in students_data}
    inactive_students = {s.rollno for s in students_data if str(s.status) == '1'}
    
    inactive_students_count = len([s for s in students_data if str(s.status) == '1'])
    
    total_students = 0
    backlog_counts = {1: [], 2: [], 3: [], 4: [], 5: [], '>5': []}
    
    passed_students_list = []
    backlog_students_list = []
    
    students_with_backlogs = 0

    for rno, subjects in student_stats.items():
        if rno in inactive_students:
            continue
            
        total_students += 1
        has_backlog = False
        student_backlog_count = 0
        
        for scode, status in subjects.items():
            if status['has_f'] and not status['is_pass']:
                has_backlog = True
                student_backlog_count += 1
                
        sname = student_names.get(rno, "Unknown")
        if has_backlog:
            students_with_backlogs += 1
            backlog_students_list.append({'rollno': rno, 'sname': sname, 'backlog_count': student_backlog_count})
            
            if student_backlog_count == 1:
                backlog_counts[1].append({'rollno': rno, 'sname': sname, 'backlog_count': 1})
            elif student_backlog_count == 2:
                backlog_counts[2].append({'rollno': rno, 'sname': sname, 'backlog_count': 2})
            elif student_backlog_count == 3:
                backlog_counts[3].append({'rollno': rno, 'sname': sname, 'backlog_count': 3})
            elif student_backlog_count == 4:
                backlog_counts[4].append({'rollno': rno, 'sname': sname, 'backlog_count': 4})
            elif student_backlog_count == 5:
                backlog_counts[5].append({'rollno': rno, 'sname': sname, 'backlog_count': 5})
            elif student_backlog_count > 5:
                backlog_counts['>5'].append({'rollno': rno, 'sname': sname, 'backlog_count': student_backlog_count})
        else:
            passed_students_list.append({'rollno': rno, 'sname': sname, 'backlog_count': 0})
            
    students_passed = total_students - students_with_backlogs
    
    stats = {
        'total_students': total_students,
        'students_passed': students_passed,
        'students_with_backlogs': students_with_backlogs,
        'passed_students_list': passed_students_list,
        'backlog_students_list': backlog_students_list,
        'backlog_counts': backlog_counts,
        'inactive_students_count': inactive_students_count
    }

    return render_template("admin_program_dashboard.html", program_info=program_info, stats=stats)
@mentor.route("/admin/search", methods=["POST"])
def admin_search():
    if "mentor_id" not in session or not session.get("is_admin"):
         return redirect("/mentor/login")
         
    rollno = request.form.get("rollno")
    if rollno:
        from models import Student, ProgramInfo, db, SemesterMarks
        # join student with program_info on pcode
        result = db.session.query(Student, ProgramInfo.pshort)\
            .outerjoin(ProgramInfo, Student.pcode == ProgramInfo.pcode)\
            .filter(Student.rollno == rollno)\
            .first()
        
        student_data = None
        backlogs_by_sem = {}
        total_backlogs = 0

        if result:
            student, pshort = result
            student_data = {
                "rollno": student.rollno,
                "sname": student.sname,
                "profile_image": student.profile_image,
                "pshort": pshort,
                "fname": student.fname,
                "mname": student.mname,
                "mobileno": student.mobileno
            }

            from models import Subject
            all_records = db.session.query(SemesterMarks, Subject.stitle).outerjoin(
                Subject, SemesterMarks.scode == Subject.scode
            ).filter(
                SemesterMarks.rollno == rollno
            ).order_by(SemesterMarks.attempt.desc()).all()

            subject_status = {}
            for record, stitle in all_records:
                scode = record.scode
                sem = record.sem
                istotpf = record.istotpf.strip().upper() if record.istotpf else ''
                istot = record.istot
                
                if scode not in subject_status:
                    subject_status[scode] = {
                        'sem': sem, 'is_pass': False, 'has_f': False, 'stitle': stitle or '—', 'istot': istot,
                        'ciapf': record.ciapf, 'seepf': record.seepf, 'istotpf': record.istotpf
                    }
                
                if istotpf == 'P':
                    subject_status[scode]['is_pass'] = True
                elif istotpf == 'F':
                    subject_status[scode]['has_f'] = True
                    # If this is an F attempt and not passed yet, we can keep the istot of this F attempt
                    # Because we process in descending order of attempt, the first F we encounter for this subject is the latest one.
                    # Or we just keep the latest istot if it's not a pass.
                    if not subject_status[scode]['is_pass']:
                         subject_status[scode]['istot'] = istot
                         subject_status[scode]['ciapf'] = record.ciapf
                         subject_status[scode]['seepf'] = record.seepf
                         subject_status[scode]['istotpf'] = record.istotpf

            for scode, status in subject_status.items():
                if status['has_f'] and not status['is_pass']:
                    sem = status['sem']
                    if sem not in backlogs_by_sem:
                        backlogs_by_sem[sem] = []
                    backlogs_by_sem[sem].append({
                        'scode': scode,
                        'stitle': status['stitle'],
                        'istot': status['istot'],
                        'ciapf': status['ciapf'],
                        'seepf': status['seepf'],
                        'istotpf': status['istotpf']
                    })
                    total_backlogs += 1
            
            backlogs_by_sem = dict(sorted(backlogs_by_sem.items()))
        else:
            flash(f"Student with Roll Number {rollno} not found.")
            
        return render_template("admin_dashboard.html", student_data=student_data, rollno=rollno, backlogs_by_sem=backlogs_by_sem, total_backlogs=total_backlogs)
    else:
        flash("Please enter a valid Roll Number")
        return redirect("/mentor/admin/dashboard")

# ---------- Forgot Password / OTP APIs ----------

@mentor.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    contact = data.get("contact")
    
    if not contact:
        return jsonify({"success": False, "message": "Please enter email or mobile"})

    # Check if mentor exists with this email OR mobile
    # We use 'or_' for OR condition in SQLAlchemy or check manually
    from sqlalchemy import or_

    mentor_obj = Mentor.query.filter(
        or_(Mentor.email == contact, Mentor.mobile == contact)
    ).first()

    if not mentor_obj:
        return jsonify({"success": False, "message": "No account found with this email/mobile."})

    # Generate 6 digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    
    # Store in session
    session["reset_otp"] = otp
    session["reset_contact"] = contact # Store contact to verify later
    
    # --- SEND EMAIL (SMTP) ---
    if "@" in contact:
        try:
            import smtplib
            from email.message import EmailMessage
            from config import Config

            if "YOUR_EMAIL" in Config.MAIL_USERNAME:
                 # If config not set, fallback to simulation
                 print(f"⚠️ SMTP NOT CONFIGURED. SIMULATING OTP: {otp}")
                 return jsonify({"success": True, "message": "OTP sent (Simulated - Check Server Console)"})

            msg = EmailMessage()
            msg.set_content(f"Your OTP for Mentor Book Password Reset is: {otp}")
            msg["Subject"] = "Mentor Book - Password Reset OTP"
            msg["From"] = Config.MAIL_USERNAME
            msg["To"] = contact

            server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
            server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            return jsonify({"success": True, "message": f"OTP sent to {contact}"})

        except Exception as e:
            print("❌ EMAIL SENDING FAILED:", str(e))
            return jsonify({"success": False, "message": "Failed to send OTP. Check server logs."})

    # --- MOBILE (FUTURE) ---
    else:
        return jsonify({"success": False, "message": "Mobile OTP not implemented yet. Please use Email."})


@mentor.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    user_otp = data.get("otp")
    
    saved_otp = session.get("reset_otp")
    
    if saved_otp and user_otp == saved_otp:
        return jsonify({"success": True, "message": "OTP Verified"})
    else:
        return jsonify({"success": False, "message": "Invalid OTP"})


@mentor.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    new_password = data.get("password")
    
    # Security check: ensure OTP was verified recently (conceptually) 
    # and we have the contact in session
    contact = session.get("reset_contact")
    
    if not contact:
        return jsonify({"success": False, "message": "Session expired. Try again."})

    from sqlalchemy import or_
    mentor_obj = Mentor.query.filter(
        or_(Mentor.email == contact, Mentor.mobile == contact)
    ).first()

    if mentor_obj:
        mentor_obj.password = new_password
        db.session.commit()
        
        # Clear session OTP data
        session.pop("reset_otp", None)
        session.pop("reset_contact", None)
        
        return jsonify({"success": True, "message": "Password changed successfully!"})
    
    return jsonify({"success": False, "message": "User not found."})


# ---------- Dashboard ----------
from models import Mentor, MentorsPcode, SemesterMarks, ProgramInfo

@mentor.route("/dashboard")
def dashboard():
    if "mentor_id" not in session:
        return redirect("/mentor/login")

    mentor_obj = Mentor.query.get(session["mentor_id"])

    # Extract all Pcodes for the logged-in mentor
    pcodes_records = MentorsPcode.query.filter_by(uname=mentor_obj.uname).all()
    dept_codes = [int(p.pcode) for p in pcodes_records] if pcodes_records else []

    # Get program info for these pcodes to use as titles
    programs = ProgramInfo.query.filter(ProgramInfo.pcode.in_(dept_codes)).all()
    program_dict = {p.pcode: p.pshort for p in programs}

    # Get all semester marks records for the mentor's students
    # Ordered by attempt desc so the first record processed per subject is the latest one
    from models import Subject
    all_marks_raw = db.session.query(SemesterMarks, Subject.stitle).outerjoin(
        Subject, SemesterMarks.scode == Subject.scode
    ).filter(
        SemesterMarks.pcode.in_(dept_codes)
    ).order_by(SemesterMarks.attempt.desc()).all()

    pcode_stats = {}
    for pcode in dept_codes:
        pcode_stats[pcode] = {
            'pshort': program_dict.get(pcode, f"Course {pcode}"),
            'student_stats': {},
            'total_students': 0,
            'students_passed': 0,
            'students_with_backlogs': 0
        }

    for mark, stitle in all_marks_raw:
        pcode = int(mark.pcode)
        if pcode not in pcode_stats:
            continue
            
        rno = mark.rollno
        scode = mark.scode
        if rno not in pcode_stats[pcode]['student_stats']:
            pcode_stats[pcode]['student_stats'][rno] = {}
            
        if scode not in pcode_stats[pcode]['student_stats'][rno]:
            # Ordered by attempt desc, so the first time we see an scode it's the latest attempt
            pcode_stats[pcode]['student_stats'][rno][scode] = {
                'is_pass': False, 
                'has_f': False,
                'sem': mark.sem,
                'stitle': stitle or 'Unknown Subject'
            }
            
        istotpf = mark.istotpf.strip().upper() if mark.istotpf else ''
        if istotpf == 'P':
            pcode_stats[pcode]['student_stats'][rno][scode]['is_pass'] = True
        elif istotpf == 'F':
            pcode_stats[pcode]['student_stats'][rno][scode]['has_f'] = True

    from models import Student
    students_data = Student.query.filter(Student.pcode.in_(dept_codes)).all()
    student_names = {s.rollno: s.sname for s in students_data}
    inactive_students = {s.rollno for s in students_data if str(s.status) == '1'}

    for pcode, stats in pcode_stats.items():
        inactive_students_count = len([s for s in students_data if str(s.status) == '1' and int(s.pcode) == pcode])
        stats['inactive_students_count'] = inactive_students_count
        
        total_students = 0
        backlogs = 0
        subject_backlogs = {} # sem -> {stitle: {'count': count, 'students': []}}
        
        passed_students_list = []
        backlog_students_list = []

        for rno, subjects in stats['student_stats'].items():
            if rno in inactive_students:
                continue
                
            total_students += 1
            has_backlog = False
            student_backlog_count = 0
            
            for scode, status in subjects.items():
                if status['has_f'] and not status['is_pass']:
                    has_backlog = True
                    student_backlog_count += 1
                    sem = status['sem']
                    stitle = status['stitle']
                    
                    if sem not in subject_backlogs:
                        subject_backlogs[sem] = {}
                    if stitle not in subject_backlogs[sem]:
                        subject_backlogs[sem][stitle] = {'count': 0, 'students': []}
                    
                    subject_backlogs[sem][stitle]['count'] += 1
                    sname = student_names.get(rno, "Unknown")
                    subject_backlogs[sem][stitle]['students'].append({'rollno': rno, 'sname': sname})
                    
            sname = student_names.get(rno, "Unknown")
            if has_backlog:
                backlogs += 1
                backlog_students_list.append({'rollno': rno, 'sname': sname, 'backlog_count': student_backlog_count})
            else:
                passed_students_list.append({'rollno': rno, 'sname': sname, 'backlog_count': 0})
                
        stats['total_students'] = total_students
                
        stats['students_with_backlogs'] = backlogs
        stats['students_passed'] = stats['total_students'] - backlogs
        stats['backlog_students_list'] = backlog_students_list
        stats['passed_students_list'] = passed_students_list
        
        chart_data = {}
        for sem in sorted(subject_backlogs.keys()):
            labels = []
            data = []
            students_info = []
            for stitle, info in sorted(subject_backlogs[sem].items(), key=lambda x: x[1]['count'], reverse=True):
                labels.append(stitle)
                data.append(info['count'])
                students_info.append(info['students'])
            chart_data[sem] = {'labels': labels, 'data': data, 'students_info': students_info}
            
        stats['sem_chart_data'] = chart_data

    return render_template(
        "dashboard.html",
        mentor=mentor_obj,
        pcode_stats=pcode_stats
    )


# ---------- Students ----------
@mentor.route("/students")
def students():
    
    if "mentor_id" not in session:
        return redirect("/auth/login")

    mentor = Mentor.query.get(session["mentor_id"])
    from models import MentorsPcode
    pcodes_records = MentorsPcode.query.filter_by(uname=mentor.uname).all()
    dept_codes = [int(p.pcode) for p in pcodes_records] if pcodes_records else []

    # ✅ FIX 2: keep only ONE query, matching ANY of the pcodes
    query = Student.query.filter(Student.pcode.in_(dept_codes))
    
    from models import ProgramInfo
    # 🔍 SEARCH FILTER
    search_query = request.args.get("search")
    
    # Use join to get pshort
    query = db.session.query(Student, ProgramInfo.pshort).outerjoin(
        ProgramInfo, Student.pcode == ProgramInfo.pcode
    ).filter(Student.pcode.in_(dept_codes))
    
    if search_query:
        search_term = f"%{search_query}%"
        from sqlalchemy import or_
        query = query.filter(or_(
            Student.rollno.ilike(search_term),
            Student.sname.ilike(search_term)
        ))

    results = query.order_by(Student.rollno).all()

    today = date.today()
    year_now = today.year
    month_now = today.month

    academic_year_start = year_now if month_now >= 7 else year_now - 1

    student_data = []

    for s, pshort in results:
        try:
            joining_year = 2000 + int(s.rollno[:2])
            calculated_year = (academic_year_start - joining_year) + 1
            calculated_year = min(max(calculated_year, 1), 3)
        except Exception:
            calculated_year = None

        student_data.append({
            "roll_no": s.rollno,
            "name": s.sname,
            "course": pshort or "Unknown",
            "pcode": s.pcode,
            "current_year": calculated_year,
            "currsem": s.currsem,
            "section": s.secl
        })

    return render_template("students.html", students=student_data)


# ---------- Parent Meetings ----------
@mentor.route("/student/<roll_no>/meetings", methods=["GET", "POST"])
def parent_meetings(roll_no):
    if "mentor_id" not in session:
        if "student_id" in session:
            flash("Students are not allowed to access the parent meetings page.")
            return redirect(f"/mentor/student/{session['student_rollno']}")
        return redirect("/mentor/login")

    # 🔒 SECURITY: Block Admin from Parent Meetings
    if session.get("is_admin"):
        flash("Admin is not allowed to access Parent Meetings.")
        return redirect(f"/mentor/student/{roll_no}/academics")

    # ✅ FIXED: roll_no → rollno (MODEL COLUMN)
    student = Student.query.filter_by(rollno=roll_no).first_or_404()

    # ---------- ADD MEETING ----------
    if request.method == "POST":
        meeting = ParentMeeting(
            student_id=student.id,
            semester=int(request.form["semester"]),
            meeting_date=request.form["meeting_date"],
            purpose=request.form["purpose"],
            remarks=request.form["remarks"]
        )
        db.session.add(meeting)
        db.session.commit()

        # ✅ SMALL FIX: prevent duplicate form submission
        return redirect(f"/mentor/student/{roll_no}/meetings")

    # ---------- VIEW MEETINGS ----------
    meetings = ParentMeeting.query.filter_by(
        student_id=student.id
    ).order_by(
        ParentMeeting.semester,
        ParentMeeting.meeting_date
    ).all()

    return render_template(
        "parent_meetings.html",
        student=student,
        meetings=meetings
    )


# ---------- View Students (Course + Year) ----------
@mentor.route("/mentor/students/<course>/<int:year>")
def view_students(course, year):
    # session check
    if "mentor_id" not in session:
        return redirect("/auth/login")

    mentor = Mentor.query.get(session["mentor_id"])
    from models import MentorsPcode
    pcodes_records = MentorsPcode.query.filter_by(uname=mentor.uname).all()
    dept_codes = [int(p.pcode) for p in pcodes_records] if pcodes_records else []

    # IMPORTANT:
    # Your current students table does NOT have `course`,
    # so we FILTER ONLY by pcode + year
    # `course` stays only for URL/UI compatibility

    students = Student.query.filter(
        Student.pcode.in_(dept_codes),
        Student.year == year
    ).order_by(Student.rollno).all()

    return render_template(
        "student_list_manage.html",
        students=students,
        course=course,
        year=year
    )

@mentor.route("/student/<rollno>", methods=["GET", "POST"])
def mentor_book(rollno):
    if "mentor_id" not in session and "student_id" not in session:
        return redirect("/mentor/login")

    if "student_id" in session and session.get("student_rollno") != rollno:
        flash("You can only view your own details.")
        return redirect(f"/mentor/student/{session['student_rollno']}")

    # 🔹 Fetch student using NEW column name
    student = Student.query.filter_by(rollno=rollno).first_or_404()
    
    from models import ProgramInfo
    program_info = ProgramInfo.query.filter_by(pcode=student.pcode).first()
    student.course = program_info.pshort if program_info else "Unknown"

    # ---------- Handle UPDATE ----------
    if request.method == "POST":
        # 🔒 SECURITY: Prevent Admin from updating
        if session.get("is_admin"):
            flash("Admin is not allowed to update student details.")
            return redirect(f"/mentor/student/{rollno}")

        # ✅ Only fields that EXIST in new table
        student.sname = request.form.get("sname")
        student.fname = request.form.get("fname")
        student.mname = request.form.get("mname")
        student.dob = request.form.get("dob")
        student.gender = request.form.get("gender")
        student.caste = request.form.get("caste")
        student.aadharno = request.form.get("aadharno")
        student.mobileno = request.form.get("mobileno")
        student.currsem = request.form.get("currsem")
        student.secl = request.form.get("secl")
        student.status = request.form.get("status")
        db.session.commit()
        return redirect(f"/mentor/student/{rollno}")

    # ---------- Calculate current year (USING jyear, not rollno guess) ----------
    from datetime import date
    today = date.today()
    academic_year_start = today.year if today.month >= 7 else today.year - 1

    if student.jyear:
        current_year = (academic_year_start - student.jyear) + 1
        current_year = min(max(current_year, 1), 3)
    else:
        current_year = None

    # ---------- Semester mapping ----------
    semester_map = {
        1: [1, 2],
        2: [3, 4],
        3: [5, 6]
    }
    semesters = semester_map.get(current_year, [])

    return render_template(
        "mentor_book.html",
        student=student,
        current_year=current_year,
        semesters=semesters
    )



@mentor.route("/student/<roll_no>/academics")
def academic_record(roll_no):
    if "mentor_id" not in session and "student_id" not in session:
        return redirect("/mentor/login")

    if "student_id" in session and session.get("student_rollno") != roll_no:
        flash("You can only view your own academic records.")
        return redirect(f"/mentor/student/{session['student_rollno']}/academics")

    # ---------------- Fetch student ----------------
    student = Student.query.filter_by(rollno=roll_no).first_or_404()

    from models import ProgramInfo
    program_info = ProgramInfo.query.filter_by(pcode=student.pcode).first()
    
    # Inject derived fields
    student.course = program_info.pshort if program_info else "Unknown"
    student.department = program_info.ptitle if program_info else "Unknown"

    # ---------------- FETCH MARKS + SUBJECT NAME ----------------
    results = (
        db.session.query(
            SemesterMarks,
            Subject.stitle
        )
        .outerjoin(Subject, SemesterMarks.scode == Subject.scode)
        .filter(SemesterMarks.rollno == roll_no)
        .order_by(SemesterMarks.sem, SemesterMarks.ord)
        .all()
    )

    # ---------------- Organize semester-wise ----------------
    from collections import defaultdict
    grouped_scores = defaultdict(list)
    for m, stitle in results:
        grouped_scores[m.scode].append((m, stitle))

    semesters = {i: [] for i in range(1, 9)}
    
    def get_attempt_val(r):
        try:
            return float(r[0].attempt)
        except (TypeError, ValueError):
            return 0
            
    for scode, records in grouped_scores.items():
        passed_records = [r for r in records if r[0].istotpf and r[0].istotpf.strip().upper() == 'P']
        
        if passed_records:
            best_record = sorted(passed_records, key=get_attempt_val, reverse=True)[0]
        else:
            best_record = sorted(records, key=get_attempt_val, reverse=True)[0]
            
        m, stitle = best_record
        m.subject_name = stitle or "—"
        
        m.is_backlog = False
        if not passed_records and m.istotpf and m.istotpf.strip().upper() == 'F':
            m.is_backlog = True
            
        if m.sem not in semesters:
            semesters[m.sem] = []
        semesters[m.sem].append(m)

    # Re-sort to maintain subject order within semester
    for sem in semesters:
        semesters[sem].sort(key=lambda m: m.ord if m.ord is not None else 999)

    # ---------------- Parent meetings ----------------
    meetings = ParentMeeting.query.filter_by(
        student_id=student.id
    ).order_by(
        ParentMeeting.semester,
        ParentMeeting.meeting_date
    ).all()

    return render_template(
        "academic_record.html",
        student=student,
        semesters=semesters,
        meetings=meetings
    )


