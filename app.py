# -*- coding = utf-8 -*-
import os
import random
import subprocess
import threading

from flask import Flask, render_template, request, redirect, session, url_for
from database import *
from flask_mysqldb import MySQL
import markdown
import psutil #windows
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '20021221wyc'
app.config['MYSQL_DB'] = 'luogudb'
mysql = MySQL(app)

hitokoto = [["千本桜 夜ニ紛レ 君ノ声モ届カナイヨ","——千本桜","https://music.163.com/song?id=26096272"],
            ["最黯淡的一个 梦最为炽热 万千孤单焰火 让这虚构灵魂鲜活","——光与影的对白","https://music.163.com/song?id=1963053471"],
            ["透通る波 映る僕らの影は蒼く遠く","——歌に形はないけれど","https://music.163.com/song?id=22677579"],
            ["在点线之外 是谁决弈黑白 似揺山撼海 峥嵘澎湃 须臾间卷起 万里尘埃","——弈","https://www.bilibili.com/festival/2022bnj?bvid=BV1q34y1271d"],
            ["鞘翅振涌 卷起击碎定论的漩涡 等待 数百天伏蛰 这一瞬冲破 最高亢的歌予我","——夏虫","https://music.163.com/song?id=1979007507"],
            ["お疲れでも元気でも乾杯！ バレない様に遊んじゃえ　合言葉はＹＹ","——YY","https://music.163.com/song?id=1475596604"]]
@app.route('/')
def index():
    show_koto = random.randint(0, len(hitokoto)-1)
    if 'id' in session:
        pro = select_profile(mysql, session['id'])
        if session['admin'] == '1':return render_template('index.html', userid = session['id'], username = session['username'],
                                                        admin = session['admin'], submit = pro[0], accept = pro[1],
                                                        koto=hitokoto[show_koto][0],stitle=hitokoto[show_koto][1],link=hitokoto[show_koto][2])
        else :return render_template('index.html', userid = session['id'], username = session['username'],
                                                submit = pro[0], accept = pro[1],
                                     koto=hitokoto[show_koto][0],stitle=hitokoto[show_koto][1],link=hitokoto[show_koto][2])
    else:
        return render_template('index.html',koto=hitokoto[show_koto][0],stitle=hitokoto[show_koto][1],link=hitokoto[show_koto][2])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'id' in session:
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_repeat = request.form['password_repeat']
        if password_repeat != password:
            return render_template('signup.html',hint = "两次输入的密码不相同！")
        if len(username) < 1:
            return render_template('signup.html', hint = "用户名长度至少为1位！")
        if len(password) < 6 or len(password) > 16:
            return render_template('signup.html', hint = "密码长度应为6~16位！")
        exist_user = select_usernames(mysql)
        for i in exist_user:
            if username == i[0]: return render_template('signup.html', hint = "该用户名已被注册！")

        insert_users(mysql,username,password)
        return redirect(url_for('login',hint = "注册成功！",good = True))
    else:
        return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    redirectTo = request.args.get('hint')
    if redirectTo is not None:
        return render_template('login.html', hint=redirectTo, good=request.args.get('good'))
    if 'id' in session:
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        result = check_password(mysql,username,password)
        if(result is not None):
            session['id'] = result[0]
            session['username'] = result[1]
            session['admin'] = result[2]
            return redirect('/')
        else:
            return render_template('login.html',hint = "无效的用户名或密码")
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    if request.referrer is None:
        return redirect(url_for('index'))
    else:
        return redirect(request.referrer)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'id' in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            password_new = request.form['password_new']
            password_repeat = request.form['password_repeat']
            if check_password(mysql, session['username'], password) is None: return render_template('profile.html', hint ="密码错误！", userid = session['id'], username = session['username'])
            if len(username) < 1: username = session['username']
            flag = False
            if username != session['username']:
                session['username'] = username
                update_pro_name(mysql,session['id'],username)
                flag = True
            if len(password_new) > 0:
                if password_new != password_repeat:  return render_template('profile.html', hint = "两次输入的新密码不一致！", userid = session['id'], username = session['username'])
                update_pro_password(mysql,session['id'],password_new)
                flag = True
            if flag: return render_template('profile.html', hint = "修改成功！", userid = session['id'], username = session['username'], good = True)
            else: return render_template('profile.html', hint = "未做修改！", userid = session['id'], username = session['username'])
        else: return render_template('profile.html', oldusername = session['username'], userid = session['id'], username = session['username'])
    else:
        return redirect(url_for('login', hint="请先登录！"))

@app.route('/delete')
def delete():
    if 'id' not in session: return redirect(url_for('login', hint="请先登录！"))
    if session['admin'] != '1': return
    delete_problem(mysql,request.args.get('problem_id'))

@app.route('/question')
def question():
    qid = request.args.get('id')
    if qid:
        result = select_description(mysql, qid)
        title = "Problem%s %s"%(qid,result[0])
        limit = "时空限制：%dms/%dMB 难度：%s"%(result[2],result[3],result[4])
        markdown_content = result[1]
        html_content = markdown.markdown(markdown_content)
        if 'id' in session: return render_template('description.html', userid=session['id'], username=session['username'],
                                                   title=title, limit=limit, content=html_content, problem_id=qid)
        else: return render_template('description.html', title=title, limit=limit, content=html_content)
    else:
        questions = select_questions(mysql)
        content = []
        for i in questions:
            item = ["/static/idle.png",i[0],i[1],i[2]]
            sub_acc = select_submission(mysql,i[0])
            item.append(sub_acc[0])
            item.append(sub_acc[1])
            content.append(item)
        if 'id' in session:
            for i in range(0,len(content)):
                accept = select_user_submission(mysql,session['id'],content[i][1])
                if len(accept) != 0: content[i][0]="/static/wrong.png"
                for j in accept:
                    if int(j[0]) == 100:
                        content[i][0]="/static/right.png"
                        break

            if session['admin'] == '1':return render_template('question.html', userid = session['id'], username = session['username'],
                                                                admin = session['admin'], question = content)
            else: return render_template('question.html', userid = session['id'], username = session['username'], question = content)
        else:
            return render_template('question.html', question = content)

@app.route('/status')
def status():
    acceptsres = select_all_submissions(mysql)
    if 'id' in session:
        return render_template('status.html', userid=session['id'], username=session['username'], result=acceptsres[::-1])
    else:
        return render_template('status.html', result=acceptsres[::-1])

@app.route('/administrator', methods=['GET', 'POST'])
def administrator():
    if 'id' in session and session['admin'] == '1':
        if request.method == 'POST':
            name = request.form['name']
            desc = request.form['inputField']
            tm = request.form['time']
            mem = request.form['space']
            difficulty = request.form['difficulty']
            input_data = request.form.getlist('input')
            output_data = request.form.getlist('output')
            insert_question(mysql,name,desc,tm,mem,difficulty,input_data,output_data)
            return render_template('addquestion.html',userid=session['id'], username=session['username'], hint="添加成功！")
        else:
            return render_template('addquestion.html',userid=session['id'], username=session['username'])
    else: return redirect(url_for('index'))

@app.route('/compile', methods=['POST'])
def compile():
    if 'id' not in session: return redirect(url_for('login', hint="请先登录！"))
    # Get the code and problem ID from the form
    code = request.form['code']
    problem_id = request.args.get('problem_id')

    # Save the code to a file
    with open('code.cpp', 'w') as f:
        f.write(code)

    # Render the compiling template
    return render_template('compiling.html', userid=session['id'], username=session['username'], problem_id=problem_id)

@app.route('/compile_code')
def compile_code():
    problem_id = request.args.get('problem_id')
    result = subprocess.run(['g++', '-C', 'code.cpp', '-o', 'code'], capture_output=True)
    if result.returncode == 0:
        return {'success': True}
    else:
        insert_submission(mysql,problem_id,session['id'],0,0,os.path.getsize("code.cpp"),0,"Compile Error")
        error_message = result.stderr.decode('utf-8')
        return {'success': False, 'error_message': error_message}

@app.route('/run')
def run():
    if 'id' not in session: redirect(url_for('login', hint="请先登录！"))
    problem_id = request.args.get('problem_id')
    casecnt = select_testcase_cnt(mysql,problem_id)
    return render_template('run.html',userid=session['id'], username=session['username'], problem_id=problem_id, casecnt=casecnt)

def monitor_memory(process, memory_limit, memory_usage, memory_exceed):
    while process.poll() is None:
        process_memory_info = psutil.Process(process.pid).memory_info()
        current_memory_usage = process_memory_info.peak_wset
        if current_memory_usage > memory_usage[0]:
            memory_usage[0] = current_memory_usage
        if current_memory_usage > memory_limit:
            memory_exceed[0] = True
            process.terminate()
            break
        time.sleep(0.01)


@app.route('/run_test_case')
def run_test_case():
    problem_id = request.args.get('problem_id')
    test_case = request.args.get('test_case')
    testfile = select_testcase(mysql, problem_id, test_case)
    requirement = select_requirement(mysql, problem_id)
    input_data = testfile[0]
    expected_outputs = testfile[1]
    time_limit = requirement[0]
    memory_limit = requirement[1] * 1024 * 1024

    flagTLE = False
    # Run compiled program with given input and measure execution time
    start_time = time.time()
    my_env = os.environ.copy()
    process = subprocess.Popen(['./code'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)

    # Start monitoring memory usage
    memory_usage = [0]
    memory_exceed = [False]
    monitor_thread = threading.Thread(target=monitor_memory, args=(process, memory_limit, memory_usage, memory_exceed))
    monitor_thread.start()

    try:
        stdout, stderr = process.communicate(input=input_data.encode('utf-8'), timeout=time_limit/1000)
    except subprocess.TimeoutExpired:
        process.terminate()
        stdout, stderr = process.communicate()
        flagTLE = True

    end_time = time.time()
    execution_time = end_time - start_time
    execution_time *= 1000
    if execution_time > time_limit:
        execution_time = time_limit
        flagTLE = True

    # Wait for monitor thread to finish
    monitor_thread.join()

    # Check if a runtime error occurred
    runtime_error = (process.returncode != 0)

    final_mem = round(memory_usage[0] / 1024 / 1024, 2)
    if memory_exceed[0]:
        return {'code': 'MLE', 'time': execution_time, 'memory': final_mem}
    if runtime_error:
        return {'code': 'RE', 'time': execution_time, 'memory': final_mem}
    if flagTLE:
        return {'code': 'TLE', 'time': execution_time, 'memory': final_mem}
    output = stdout.decode('utf-8').strip()
    if output == expected_outputs:
        return {'code': 'AC', 'time': execution_time, 'memory': final_mem}
    else:
        return {'code': 'WA', 'time': execution_time, 'memory': final_mem}


@app.route('/submit')
def submit():
    insert_submission(mysql, request.args.get('problem_id'), session['id'], request.args.get('time'),
                      request.args.get('mem'),os.path.getsize("code.cpp"),request.args.get('score'),request.args.get('state'))
    return {}
if __name__ == '__main__':
    app.run()
