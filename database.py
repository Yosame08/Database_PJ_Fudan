from flask_mysqldb import MySQL
import hashlib
import time
def insert_users(mysql:MySQL,username,password):
    signtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    salt = signtime
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    iuser = mysql.connection.cursor()
    iuser.execute("SELECT COUNT(*) FROM users")
    newid = iuser.fetchone()[0] + 1
    iuser.execute("INSERT INTO users VALUES (%s,%s,%s,%s,%s)",(newid,username,hashed_password,signtime,0,))
    mysql.connection.commit()
    iuser.close()

def select_usernames(mysql:MySQL):
    quname = mysql.connection.cursor()
    quname.execute("SELECT username FROM users")
    result = quname.fetchall()
    quname.close()
    return result

def check_password(mysql:MySQL,username,password):
    iuser = mysql.connection.cursor()
    iuser.execute("SELECT userid,password,signdate,administrator FROM users WHERE username = %s", (username,))
    result = iuser.fetchone()
    iuser.close()
    if result is None: return None
    salt = result[2]
    if hashlib.sha256((password + salt).encode()).hexdigest() == result[1]: return result[0], username, result[3];
    else: return None

def select_profile(mysql:MySQL,id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM submission WHERE userid = %s", (id,))
    submit = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT idproblem) FROM submission WHERE userid = %s AND score = 100", (id,))
    accept = cur.fetchone()[0]
    cur.close()
    return submit, accept

def select_user_submission(mysql:MySQL,id,probid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT score,state FROM submission WHERE idproblem = %s AND userid = %s", (probid,id,))
    result = cur.fetchall()
    cur.close()
    return result

def select_submission(mysql:MySQL,probid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM submission WHERE idproblem = %s", (probid,))
    submit = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM submission WHERE idproblem = %s AND score = 100", (probid,))
    accept = cur.fetchone()[0]
    cur.close()
    return submit, accept

def select_questions(mysql:MySQL):
    cur = mysql.connection.cursor()
    cur.execute("SELECT idproblem,name,difficulty FROM problem")
    result = cur.fetchall()
    cur.close()
    return result

def select_description(mysql:MySQL, qid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT name,description,time,mem,difficulty FROM problem WHERE idproblem = %s",(qid,))
    result = cur.fetchone()
    cur.close()
    return result

def update_pro_name(mysql:MySQL, id, username):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET username = %s WHERE userid = %s", (username, id,))
    mysql.connection.commit()
    cur.close()
    return

def update_pro_password(mysql:MySQL, id, password):
    oldcheck = mysql.connection.cursor()
    oldcheck.execute("SELECT (signdate) FROM users WHERE userid = %s", (id,))
    salt = oldcheck.fetchone()[0]
    oldcheck.close()

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET password = %s WHERE userid = %s", (hashlib.sha256((password + salt).encode()).hexdigest(),id,))
    mysql.connection.commit()
    cur.close()
    return

def query_accept(mysql:MySQL, id, probid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT score FROM submission WHERE userid = %d AND idproblem = %d",(id,probid,))
    result = cur.fetchall()
    cur.close()
    for i in result:
        if i[0] == 100:return True
    return False

def handle_submission(mysql:MySQL, idproblem, userid, time, runtime, mem, length, score, state):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM submission")
    cnt = cur.fetchone()[0] + 1
    cur.execute("INSERT INTO submission VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (cnt+1,idproblem,userid,time,
                                                                               runtime,mem,length,score,state))
    mysql.connection.commit()
    cur.close()
    return

def insert_question(mysql:MySQL,name,description,time,mem,difficulty,input,output):
    cur = mysql.connection.cursor()
    cur.execute("SELECT idproblem FROM problem")
    pbs = cur.fetchall()
    newid = 0
    flag = False
    last = 0
    for i in pbs:
        now = int(i[0])
        if now != last + 1:
            flag = True
            newid = last + 1
            break
        else: last = now
    if not flag: newid = len(pbs) + 1
    testcase = len(output)
    cur.execute("INSERT INTO problem VALUES (%s,%s,%s,%s,%s,%s)",(newid,name,description,time,mem,difficulty,))
    for i in range(0,testcase):
        cur.execute("INSERT INTO data VALUES (%s,%s,%s,%s)",(newid, i, input[i], output[i],))
    mysql.connection.commit()
    cur.close()

def select_testcase(mysql:MySQL,probid,caseid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT input,output FROM data WHERE idproblem = %s AND testcase = %s",(probid,caseid,))
    result = cur.fetchone()
    cur.close()
    return result

def select_requirement(mysql:MySQL,probid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT time,mem FROM problem WHERE idproblem = %s",(probid,))
    result = cur.fetchone()
    cur.close()
    return result

def select_testcase_cnt(mysql:MySQL,probid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM data WHERE idproblem = %s",(probid,))
    result = cur.fetchone()[0]
    cur.close()
    return result

def insert_submission(mysql:MySQL,idproblem,userid,runtime,mem,length,score,state):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM submission")
    sid = cur.fetchone()[0] + 1
    subtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    cur.execute("INSERT INTO submission VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(sid,idproblem,userid,subtime,runtime,mem,length,score,state,))
    mysql.connection.commit()
    cur.close()

def select_all_submissions(mysql:MySQL):
    cur = mysql.connection.cursor()
    cur.execute("SELECT users.username,problem.idproblem,problem.name,submission.state,submission.score,"
                "submission.runtime,submission.mem,submission.length,submission.time "
                "FROM submission,users,problem WHERE submission.userid=users.userid AND "
                "submission.idproblem=problem.idproblem "
                "ORDER BY submission.time")
    result = cur.fetchall()
    cur.close()
    return result

def delete_problem(mysql:MySQL,pid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM submission WHERE idproblem = %s", (pid,))
    cur.execute("DELETE FROM data WHERE idproblem = %s", (pid,))
    cur.execute("DELETE FROM problem WHERE idproblem = %s",(pid,))
    mysql.connection.commit()
    cur.close()